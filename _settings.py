import sys
import threading
from copy import deepcopy
import pickle
import random
from keyboard import KeyboardEvent
import keyboard
from configparser import ConfigParser
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
import _autoclicker
import _record
from collections import namedtuple

from PySide2.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QTreeWidgetItem
from PySide2.QtCore import QSignalBlocker, QRegularExpression
from PySide2.QtGui import QStandardItemModel, QStandardItem, QKeySequence
from ui_GUI import Ui_MainWindow
from recording_GUI import Ui_Dialog


class SettingsMethods:

    def saveAllSettings(self, destination='settings.dat', forced=False):
        print('Autosave:', self.ui.settingsAutosave.isChecked(), '- forced:', forced )
        print( 'destination:', destination )
        if forced or self.ui.settingsAutosave.isChecked():
            config = ConfigParser()
            config['autoclicker'] = {
                'hours': self.ui.AC_Hours.value(),
                'minutes': self.ui.AC_Minutes.value(),
                'seconds': self.ui.AC_Seconds.value(),
                'miliseconds': self.ui.AC_Miliseconds.value(),
                'whichButton': self.ui.AC_WhichButton.currentIndex(),
                'hotkey': self.ui.AC_Hotkey.keySequence().toString(),
                'clickUntilStopped' : self.ui.AC_ClickUntilStopped.isChecked(),
                'clickNTimes': self.ui.AC_ClickNTimes.isChecked(),
                'clickNTimesN': self.ui.AC_ClickNTimesN.value()
            }
            config['general'] = {
                'abortHotkey': self.ui.abortHotkey.keySequence().toString()
            }
            config['recording'] = {
                'recordingHotkey': self.recordDialog.recordingHotkey.keySequence().toString(),
                'previewHotkey': self.recordDialog.previewHotkey.keySequence().toString()
            }
            with open(destination, 'w') as f:
                config.write(f)
            print( 'saveAllSettings' )

    def autosave(self): # PyQt5 najwyraźniej przekazuje argumenty wywoływanym funkcjom, więc to najprostszy sposób zabezpieczenia przed nadpisaniem domyślnych wartości funkcji saveAllSettings
        self.saveAllSettings()

    def loadAllSettings(self, destination='settings.dat'):
        print( destination )
        parser = ConfigParser()

        if parser.read(destination):
            # autoclicker
            self.ui.AC_Hours.setValue(parser.getint('autoclicker', 'hours'))
            self.ui.AC_Minutes.setValue(parser.getint('autoclicker', 'minutes'))
            self.ui.AC_Seconds.setValue(parser.getint('autoclicker', 'seconds'))
            self.ui.AC_Miliseconds.setValue(parser.getint('autoclicker', 'miliseconds'))
            self.ui.AC_WhichButton.setCurrentIndex(parser.getint('autoclicker', 'whichButton'))
            self.ui.AC_Hotkey.setKeySequence(parser.get('autoclicker', 'hotkey'))
            self.ui.AC_ClickUntilStopped.setChecked(parser.getboolean('autoclicker', 'clickUntilStopped'))
            self.ui.AC_ClickNTimes.setChecked(parser.getboolean('autoclicker', 'clickNTimes'))
            self.ui.AC_ClickNTimesN.setValue(parser.getint('autoclicker', 'clickNTimesN'))

            # general
            self.ui.abortHotkey.setKeySequence( QKeySequence().fromString( parser.get( 'general', 'abortHotkey' )))
            self.updateAbortionHotkey()
            print( 'loadAllSettings' )

            # Recording
            self.recordDialog.recordingHotkey.setKeySequence( QKeySequence().fromString( parser.get( 'recording', 'recordingHotkey' )))
            self.recordDialog.previewHotkey.setKeySequence( QKeySequence().fromString( parser.get( 'recording', 'previewHotkey' )))

        elif parser.read( 'defaultSettings.dat' ):
            print( 'settings.dat not found' )
            self.ui.AC_Hours.setValue(parser.getint('autoclicker', 'hours'))
            self.ui.AC_Minutes.setValue(parser.getint('autoclicker', 'minutes'))
            self.ui.AC_Seconds.setValue(parser.getint('autoclicker', 'seconds'))
            self.ui.AC_Miliseconds.setValue(parser.getint('autoclicker', 'miliseconds'))
            self.ui.AC_WhichButton.setCurrentIndex(parser.getint('autoclicker', 'whichButton'))
            self.ui.AC_Hotkey.setKeySequence(parser.get('autoclicker', 'hotkey'))
            self.ui.AC_ClickUntilStopped.setChecked(parser.getboolean('autoclicker', 'clickUntilStopped'))
            self.ui.AC_ClickNTimes.setChecked(parser.getboolean('autoclicker', 'clickNTimes'))
            self.ui.AC_ClickNTimesN.setValue(parser.getint('autoclicker', 'clickNTimesN'))

            # general
            self.ui.abortHotkey.setKeySequence(QKeySequence().fromString(parser.get('general', 'abortHotkey')))
            self.updateAbortionHotkey()

            # Recording
            self.recordDialog.recordingHotkey.setKeySequence( QKeySequence().fromString(parser.get('recording', 'recordingHotkey')))
            self.recordDialog.previewHotkey.setKeySequence( QKeySequence().fromString(parser.get('recording', 'previewHotkey')))
            print( 'loadAllSettings' )

            with open( 'settings.dat', 'w' ) as f:
                parser.write(f)
            print('settings.dat created based on defaultSettings.dat')

        else:
            print( 'settings.dat and defaultSettings.dat not found' )
            # create defaultSettings.dat
            config = ConfigParser()
            config['autoclicker'] = {
                'hours': 0,
                'minutes': 0,
                'seconds': 0,
                'miliseconds': 100,
                'whichButton': 0,
                'hotkey': 'Ctrl+Q',
                'clickUntilStopped': True,
                'clickNTimes': False,
                'clickNTimesN': 1
            }
            config['general'] = {
                'abortHotkey': 'Ctrl+Alt+B'
            }
            config['recording'] = {
                'recordingHotkey': 'Ctrl+Alt+R',
                'previewHotkey': 'Ctrl+Alt+P'
            }

            with open('defaultSettings.dat', 'w') as f:
                config.write(f)
            print('defaultSettings.dat created.')

            self.loadAllSettings()

    def settingsDefaultConfirmation(self):
        print( 'settingsDefaultConfirmation' )
        msg = QMessageBox()
        msg.setWindowTitle("Resetowanie ustawień")
        msg.setText("Czy na pewno chcesz zresetować obecne ustawienia?")
        msg.setInformativeText("Jeśli autosave jest włączony, to stracisz wszystkie ustawienia!")
        msg.setIcon( QMessageBox.Warning )
        msg.setStandardButtons( QMessageBox.Ok | QMessageBox.Cancel )
        msg.setDefaultButton( QMessageBox.Cancel )
        msg.buttonClicked.connect( self.settingsDefaultConfirmed )
        x = msg.exec_()

    def settingsDefaultConfirmed(self, i):
        if i.text() == 'OK':
            self.loadAllSettings(destination='defaultSettings.dat')

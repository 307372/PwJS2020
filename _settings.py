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
            config['autoclicker_M'] = {
                'hours': self.ui.AC_Hours.value(),
                'minutes': self.ui.AC_Minutes.value(),
                'seconds': self.ui.AC_Seconds.value(),
                'miliseconds': self.ui.AC_Miliseconds.value(),
                'whichButton': self.ui.AC_WhichButton.currentIndex(),
                'hotkey': self.ui.AC_Hotkey.keySequence().toString(),
                'clickUntilStopped': self.ui.AC_ClickUntilStopped.isChecked(),
                'clickNTimes': self.ui.AC_ClickNTimes.isChecked(),
                'clickNTimesN': self.ui.AC_ClickNTimesN.value()
            }
            config['autoclicker_K'] = {
                'hours': self.ui.AC_KeyboardHours.value(),
                'minutes': self.ui.AC_KeyboardMinutes.value(),
                'seconds': self.ui.AC_KeyboardSeconds.value(),
                'miliseconds': self.ui.AC_KeyboardMiliseconds.value(),
                'keySequence': self.ui.AC_KeyboardKeySequence.keySequence().toString(),
                'hotkey': self.ui.AC_KeyboardHotkey.keySequence().toString(),
                'clickUntilStopped': self.ui.AC_KeyboardClickUntilStopped.isChecked(),
                'clickNTimes': self.ui.AC_KeyboardClickNTimes.isChecked(),
                'hold': self.ui.AC_KeyboardHold.isChecked(),
                'clickNTimesN': self.ui.AC_KeyboardClickNTimesN.value()
            }

            config['general'] = {
                'abortHotkey': self.ui.abortHotkey.keySequence().toString(),
                'execution_time': self.ui.execution_time.value()
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
            # autoclicker mouse
            self.ui.AC_Hours.setValue(parser.getint('autoclicker_M', 'hours'))
            self.ui.AC_Minutes.setValue(parser.getint('autoclicker_M', 'minutes'))
            self.ui.AC_Seconds.setValue(parser.getint('autoclicker_M', 'seconds'))
            self.ui.AC_Miliseconds.setValue(parser.getint('autoclicker_M', 'miliseconds'))
            self.ui.AC_WhichButton.setCurrentIndex(parser.getint('autoclicker_M', 'whichButton'))
            self.ui.AC_Hotkey.setKeySequence(parser.get('autoclicker_M', 'hotkey'))
            self.ui.AC_ClickUntilStopped.setChecked(parser.getboolean('autoclicker_M', 'clickUntilStopped'))
            self.ui.AC_ClickNTimes.setChecked(parser.getboolean('autoclicker_M', 'clickNTimes'))
            self.ui.AC_ClickNTimesN.setValue(parser.getint('autoclicker_M', 'clickNTimesN'))

            # autoclicker keyboard
            self.ui.AC_KeyboardHours.setValue(parser.getint('autoclicker_K', 'hours'))
            self.ui.AC_KeyboardMinutes.setValue(parser.getint('autoclicker_K', 'minutes'))
            self.ui.AC_KeyboardSeconds.setValue(parser.getint('autoclicker_K', 'seconds'))
            self.ui.AC_KeyboardMiliseconds.setValue(parser.getint('autoclicker_K', 'miliseconds'))
            self.ui.AC_KeyboardKeySequence.setKeySequence(QKeySequence().fromString(parser.get('autoclicker_K', 'keySequence')))
            self.ui.AC_KeyboardHotkey.setKeySequence(QKeySequence().fromString(parser.get('autoclicker_K', 'hotkey')))
            self.AC_KeyboardHotkeyChange()
            self.ui.AC_KeyboardClickUntilStopped.setChecked(parser.getboolean('autoclicker_K', 'clickUntilStopped'))
            self.ui.AC_KeyboardClickNTimes.setChecked(parser.getboolean('autoclicker_K', 'clickNTimes'))
            self.ui.AC_KeyboardHold.setChecked(parser.getboolean('autoclicker_K', 'hold'))
            self.ui.AC_KeyboardClickNTimesN.setValue(parser.getint('autoclicker_K', 'clickNTimesN'))

            # general
            self.ui.abortHotkey.setKeySequence( QKeySequence().fromString( parser.get('general', 'abortHotkey')))
            self.updateAbortionHotkey()
            self.ui.execution_time.setValue(parser.getfloat( 'general', 'execution_time' ))
            print( 'loadAllSettings' )

            # Recording
            self.recordDialog.recordingHotkey.setKeySequence( QKeySequence().fromString( parser.get( 'recording', 'recordingHotkey' )))
            self.recordDialog.previewHotkey.setKeySequence( QKeySequence().fromString( parser.get( 'recording', 'previewHotkey' )))

        elif parser.read( 'defaultSettings.dat' ):
            print( 'settings.dat not found' )
            self.ui.AC_Hours.setValue(parser.getint('autoclicker_M', 'hours'))
            self.ui.AC_Minutes.setValue(parser.getint('autoclicker_M', 'minutes'))
            self.ui.AC_Seconds.setValue(parser.getint('autoclicker_M', 'seconds'))
            self.ui.AC_Miliseconds.setValue(parser.getint('autoclicker_M', 'miliseconds'))
            self.ui.AC_WhichButton.setCurrentIndex(parser.getint('autoclicker_M', 'whichButton'))
            self.ui.AC_Hotkey.setKeySequence(parser.get('autoclicker_M', 'hotkey'))
            self.ui.AC_ClickUntilStopped.setChecked(parser.getboolean('autoclicker_M', 'clickUntilStopped'))
            self.ui.AC_ClickNTimes.setChecked(parser.getboolean('autoclicker_M', 'clickNTimes'))
            self.ui.AC_ClickNTimesN.setValue(parser.getint('autoclicker_M', 'clickNTimesN'))

            # autoclicker keyboard
            self.ui.AC_KeyboardHours.setValue(parser.getint('autoclicker_K', 'hours'))
            self.ui.AC_KeyboardMinutes.setValue(parser.getint('autoclicker_K', 'minutes'))
            self.ui.AC_KeyboardSeconds.setValue(parser.getint('autoclicker_K', 'seconds'))
            self.ui.AC_KeyboardMiliseconds.setValue(parser.getint('autoclicker_K', 'miliseconds'))
            self.ui.AC_KeyboardKeySequence.setKeySequence(QKeySequence().fromString(parser.get('autoclicker_K', 'keySequence')))
            self.ui.AC_KeyboardHotkey.setKeySequence(QKeySequence().fromString(parser.get('autoclicker_K', 'hotkey')))
            self.AC_KeyboardHotkeyChange()
            self.ui.AC_KeyboardClickUntilStopped.setChecked(parser.getboolean('autoclicker_K', 'clickUntilStopped'))
            self.ui.AC_KeyboardClickNTimes.setChecked(parser.getboolean('autoclicker_K', 'clickNTimes'))
            self.ui.AC_KeyboardHold.setChecked(parser.getboolean('autoclicker_K', 'hold'))
            self.ui.AC_KeyboardClickNTimesN.setValue(parser.getint('autoclicker_K', 'clickNTimesN'))

            # general
            self.ui.abortHotkey.setKeySequence(QKeySequence().fromString(parser.get('general', 'abortHotkey')))
            self.updateAbortionHotkey()
            self.ui.execution_time.setValue(parser.getfloat('general', 'execution_time'))

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
            config['autoclicker_M'] = {
                'hours': 0,
                'minutes': 0,
                'seconds': 0,
                'miliseconds': 10,
                'whichButton': 0,
                'hotkey': 'Ctrl+Q',
                'clickUntilStopped': True,
                'clickNTimes': False,
                'clickNTimesN': 1
            }

            config['autoclicker_K'] = {
                'hours': 0,
                'minutes': 0,
                'seconds': 0,
                'miliseconds': 10,
                'keySequence': 'W',
                'hotkey': 'Ctrl+K',
                'clickNTimes': False,
                'clickUntilStopped': True,
                'hold': False,
                'clickNTimesN': 1
            }

            config['general'] = {
                'abortHotkey': 'Ctrl+Alt+B',
                'execution_time': 5
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

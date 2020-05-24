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
from PySide2.QtGui import QStandardItemModel, QStandardItem
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
            config['test'] = {
                'abc': 'efg'
            }
            with open(destination, 'w') as f:
                config.write(f)
            print( 'saveAllSettings' )

    def autosave(self): # PyQt5 najwyraźniej przekazuje argumenty wywoływanym funkcjom, więc to najprostszy sposób zabezpieczenia przed nadpisaniem domyślnych wartości funkcji saveAllSettings
        self.saveAllSettings()

    def loadAllSettings(self, destination='settings.dat'):
        print( destination )
        parser = ConfigParser()
        parser.read( destination )

        self.ui.AC_Hours.setValue(parser.getint('autoclicker', 'hours'))
        self.ui.AC_Minutes.setValue(parser.getint('autoclicker', 'minutes'))
        self.ui.AC_Seconds.setValue(parser.getint('autoclicker', 'seconds'))
        self.ui.AC_Miliseconds.setValue(parser.getint('autoclicker', 'miliseconds'))
        self.ui.AC_WhichButton.setCurrentIndex(parser.getint('autoclicker', 'whichButton'))
        self.ui.AC_Hotkey.setKeySequence(parser.get('autoclicker', 'hotkey'))
        self.ui.AC_ClickUntilStopped.setChecked(parser.getboolean('autoclicker', 'clickUntilStopped'))
        self.ui.AC_ClickNTimes.setChecked(parser.getboolean('autoclicker', 'clickNTimes'))
        self.ui.AC_ClickNTimesN.setValue(parser.getint('autoclicker', 'clickNTimesN'))
        print( 'loadAllSettings' )

    def settingsDefaultConfirmation(self):
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

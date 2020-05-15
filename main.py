import sys
import threading
from copy import deepcopy
import pickle
from keyboard import KeyboardEvent
import keyboard
from configparser import ConfigParser
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
from PySide2.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QTreeWidgetItem
from PySide2.QtCore import QSignalBlocker, QRegularExpression
from PySide2.QtGui import QStandardItemModel, QStandardItem
from ui_GUI import Ui_MainWindow
from recording_GUI import Ui_Dialog


class Recording:
    def __init__(self, name='', events=[], speed_factor=1.0, cut_left=0, cut_right=0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        self.name = name
        self.events = events
        self.speed_factor = speed_factor
        self.cutLeft = cut_left
        self.cutRight = cut_right
        self.include_clicks = include_clicks
        self.include_moves = include_moves
        self.include_wheel = include_wheel
        self.include_keyboard = include_keyboard

    def setT0to0(self):  # sets time of first event to 0 and keeps relative time difference between the rest
        if self.events != []:
            if self.events[0].time != 0:
                edited_events = []
                t0 = float( self.events[0].time )
                for i in range( len( self.events ) ):
                    if type( self.events[i] ) == ButtonEvent:
                        edited_events.append( ButtonEvent( self.events[i].event_type, self.events[i].button, self.events[i].time - t0 ) )
                    elif type( self.events[i] ) == WheelEvent:
                        edited_events.append( WheelEvent( self.events[i].delta, self.events[i].time - t0 ) )
                    elif type( self.events[i] ) == MoveEvent:
                        edited_events.append( MoveEvent( self.events[i].x, self.events[i].y, self.events[i].time - t0 ) )
                    elif type( self.events[i] ) == KeyboardEvent:
                        edited_events.append( deepcopy(self.events[i]) )
                        edited_events[i].time = float( edited_events[i].time - t0 )
                    else:
                        print("Nieznany typ eventu")
                self.events = edited_events


class MacroEditorItem(QStandardItem):
    def __init__(self, action, text='' ):
        super().__init__(text=text)

        self.action = action
        self.setText(text)


class PlaceholderEvent:
    def __init__(self):
        self.event_type = 'PlaceholderEvent'


class ForEvent:
    def __init__(self, event_list=[PlaceholderEvent()], times=1):
        self.event_type = 'ForEvent'
        self.event_list = event_list
        self.times = times
        self.ensurePlaceholder()

    def ensurePlaceholder(self):
        if not isinstance( self.event_list[0], PlaceholderEvent ):
            self.event_list.insert(0, PlaceholderEvent())


class WaitEvent:
    def __init__(self, event_type, trigger ):
        self.event_type = event_type
        self.trigger = trigger


class MainWindow(QMainWindow):
    def __init__( self ):
        super( MainWindow, self ).__init__()  # Calling parent constructor
        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )

        # AC = autoclicker
        self.ui.AC_Start.clicked.connect(self.AC_StartPrep)
        self.ui.AC_Stop.clicked.connect(self.AC_Stop)
        self.isACRunning = False
        self.ui.AC_Hotkey.editingFinished.connect(self.AC_HotkeyChange)
        self.AC_Hotkey = self.ui.AC_Hotkey.keySequence().toString()
        keyboard.add_hotkey(self.ui.AC_Hotkey.keySequence().toString(), self.AC_Toggle)
        self.AC_Thread = threading.Event()
        self.AC_MouseButton = ''
        self.AC_MouseButtonUpdate()
        self.ui.AC_WhichButton.currentTextChanged.connect(self.AC_MouseButtonUpdate)

        self.ui.AC_Hours.valueChanged.connect(self.autosave)
        self.ui.AC_Minutes.valueChanged.connect(self.autosave)
        self.ui.AC_Seconds.valueChanged.connect(self.autosave)
        self.ui.AC_Miliseconds.valueChanged.connect(self.autosave)
        self.ui.AC_WhichButton.currentIndexChanged.connect(self.autosave)
        self.ui.AC_Hotkey.editingFinished.connect(self.autosave)
        self.ui.AC_ClickUntilStopped.clicked.connect(self.autosave)
        self.ui.AC_ClickNTimes.clicked.connect(self.autosave)
        self.ui.AC_ClickNTimesN.editingFinished.connect(self.autosave)

        # creator
        self.dialog = QDialog()
        self.recordDialog = Ui_Dialog()
        self.recordDialog.setupUi(self.dialog)
        # validator = QRegularExpression("[_]*")        # Ma nieprzyjmować podkreślników!
        # self.recordDialog.name.setValidator()
        self.recorded = []
        self.recordedCut = []
        self.recordedFinal = []
        self.recordsDict = {}

        self.macroElementNametags = {
            'MoveEvent': 'Przemieść kursor',
            'WheelEvent': 'Ruch kółka myszy',
            'ButtonEventup': 'Puść przycisk myszy',
            'ButtonEventdown': 'Przytrzymaj przycisk myszy',
            'ButtonEventclick': 'Kliknięcie',  # PAMIĘTAJ TO WSZYSTKO DODAć PRZY TWORZENIU AKCJI!!!!!
            'ButtonEventdouble': 'Podwójne kliknięcie',
            'KeyboardEventhotkey': 'Użyj skrótu klawiszowego',
            'KeyboardEventsend': 'Kliknij klawisz',
            'KeyboardEventdown': 'Przytrzymaj klawisz',
            'KeyboardEventup': 'Puść klawisz',
            'KeyboardEventwrite': 'Wypisz tekst',
            'KeyboardEventreleaseall': "Puść wszystkie klawisze",
            'WaitEventmouse': "Czekaj na akcję myszy",
            'WaitEventkeyboard': "Czekaj na akcje klawiatury",
            'WaitEventnseconds': "Czekaj N sekund",
            'ForEvent': "Wykonaj N razy",
            'PlaceholderEvent': "Początek pętli"
        }

        self.macroElementNameInterpreter = {
            'Przemieść kursor': MoveEvent(0, 0, 0),
            'Ruch kółka myszy': WheelEvent(1, 0),
            'Puść przycisk myszy': ButtonEvent(mouse.UP, mouse.LEFT, 0),
            'Przytrzymaj przycisk myszy': ButtonEvent(mouse.DOWN, mouse.LEFT, 0),
            'Kliknięcie': ButtonEvent('click', mouse.LEFT, 0),
            'Podwójne kliknięcie': ButtonEvent(mouse.DOUBLE, mouse.LEFT, 0),
            'Użyj skrótu klawiszowego': KeyboardEvent('hotkey', 0, time=0),
            'Kliknij klawisz': KeyboardEvent('write', 0, time=0),
            'Przytrzymaj klawisz': KeyboardEvent(keyboard.KEY_DOWN, 0, time=0),
            'Puść klawisz': KeyboardEvent(keyboard.KEY_UP, 0, time=0),
            'Wypisz tekst': KeyboardEvent('write', 0, time=0),
            "Puść wszystkie klawisze": KeyboardEvent('releaseall', 0, time=0),
            "Czekaj na akcję myszy": WaitEvent('mouse', 0),
            "Czekaj na akcję klawiatury": WaitEvent('keyboard', 0),
            "Czekaj N sekund": WaitEvent('nseconds', 0),
            "Wykonaj N razy": ForEvent(),
            "Początek pętli": PlaceholderEvent()
        }

        self.macroElements = []
        self.treeModel = QStandardItemModel()
        self.rootNode = self.treeModel.invisibleRootItem()
        self.treeModel.setColumnCount(2)
        self.ui.creatorEditorTreeView.setModel(self.treeModel)
        self.ui.creatorEditorTreeView.setColumnWidth(0, 300)

        self.isRecordingRunning = False
        self.isMacroRunning = False
        self.macroThread = threading.Event()
        self.recordedLength = 0

        self.creatorRecordHotkey = self.recordDialog.recordingHotkey.keySequence().toString()
        keyboard.add_hotkey( self.creatorRecordHotkey, self.creatorRecordToggle )

        self.creatorPreviewHotkey = self.recordDialog.previewHotkey.keySequence().toString()
        keyboard.add_hotkey( self.creatorPreviewHotkey, self.creatorRecordPreviewToggle )

        self.ui.creatorEditorNewRecording.clicked.connect( self.creatorRecordDisplay )

        self.recordDialog.replaySpeed.valueChanged.connect( self.creatorRecordTimeFinalUpdate )
        self.recordDialog.cutSliderLeft.valueChanged.connect( self.creatorRecordLeftSliderSpinBoxSync )
        self.recordDialog.cutTimeLeft.valueChanged.connect( self.creatorRecordLeftSpinBoxSliderSync )
        self.recordDialog.cutSliderRight.valueChanged.connect( self.creatorRecordRightSliderSpinBoxSync )
        self.recordDialog.cutTimeRight.valueChanged.connect( self.creatorRecordRightSpinBoxSliderSync )

        self.recordDialog.recordingHotkey.editingFinished.connect( self.creatorRecordHotkeyChange )
        self.recordDialog.previewHotkey.editingFinished.connect( self.creatorPreviewHotkeyChange )
        self.recordDialog.start.clicked.connect(self.creatorRecordToggle)
        self.recordDialog.preview.clicked.connect( self.creatorRecordPreviewToggle )
        self.recordDialog.addToActions.clicked.connect( self.creatorRecordAddToActions )

        self.ui.testSaveButton.clicked.connect( self.pickleRecordings )
        self.ui.testLoadButton.clicked.connect( self.unpickleRecordings )
        self.ui.testButton.clicked.connect( self.creatorEditorTreeViewUpdate )
        self.ui.testButton_2.clicked.connect( self.creatorEditorTreeViewClear )
        self.ui.WhatIsThisButton.clicked.connect( self.inspectThis )

        self.ui.creatorEditorDeleteFromActions.clicked.connect( self.creatorEditorDelete )
        self.ui.creatorEditorEdit.clicked.connect( self.creatorRecordOpenInEditor )
        self.ui.creatorEditorAddToMacro.clicked.connect( self.creatorAddActionToMacro )

        # settings
        self.ui.settingsDefault.clicked.connect( self.settingsDefaultConfirmation )
        self.ui.forceSave.clicked.connect( lambda: self.saveAllSettings(destination='settings.dat', forced=True) )
        self.ui.forceLoad.clicked.connect( lambda: self.loadAllSettings(destination='settings.dat') )

        self.unpickleRecordings()

    def testowa(self):
        x = self.ui.AC_Hotkey.keySequence().toString()
        print(x)

    def AC_StartPrep(self):
        print( "autoclickerStartPrep" )
        if not self.isACRunning:
            self.isACRunning = True
            thread = threading.Thread(target=self.AC_Start)
            thread.start()

    def AC_Start(self):
        print( "autoclickerStart" )
        time_delay = self.ui.AC_Miliseconds.value() + self.ui.AC_Seconds.value() * 1000 + self.ui.AC_Minutes.value() * 60 * 1000 + self.ui.AC_Hours.value() * 60 * 60 * 1000
        self.AC_Thread = threading.Event()
        if self.ui.AC_ClickUntilStopped.isChecked():
            while True:
                mouse.click(self.AC_MouseButton)
                if self.AC_Thread.wait(timeout=time_delay / 1000):
                    break
        else:
            i = 0
            while i < self.ui.AC_ClickNTimesN.value():
                i += 1
                mouse.click(self.AC_MouseButton)
                print( i )
                if self.AC_Thread.wait(timeout=time_delay / 1000):
                    break
        self.isACRunning = False

    def AC_Stop(self):
        print("autoclickerStop")
        self.AC_Thread.set()
        self.isACRunning = False

    def AC_Toggle(self):
        print( "autoclickerToggle" )
        if self.isACRunning:
            self.AC_Stop()
        else:
            self.AC_StartPrep()

    def AC_HotkeyChange(self):
        hotkey = self.ui.AC_Hotkey.keySequence().toString()
        if hotkey != '':
            print( "autoclickerHotkeyChange", hotkey )
            if self.AC_Hotkey != '':
                keyboard.remove_hotkey(self.AC_Hotkey)
            keyboard.add_hotkey(hotkey, self.AC_Toggle)
            self.AC_Hotkey = hotkey
        else:
            print("autoclickerHotkeyChange ''")
            keyboard.remove_hotkey(self.AC_Hotkey)
            self.AC_Hotkey = hotkey

    def AC_MouseButtonUpdate(self):  # biblioteka mouse wymaga poniższych nazw
        print( "autoclickerMouseButtonUpdate", end=' ' )
        buttonIndex = self.ui.AC_WhichButton.currentIndex()
        if buttonIndex == 0:    # lewy
            self.AC_MouseButton = 'left'
        elif buttonIndex == 1:  # srodkowy
            self.AC_MouseButton = 'middle'
        elif buttonIndex == 2:
            self.AC_MouseButton = 'right'
        print(self.AC_MouseButton)

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

    def pickleRecordings(self):
        # print( [self.recordDialog.name.text().replace(' ', '_')] )
        with open("recordedActions.pickle", "wb") as pickle_out:  # wb - write bytes
            pickle.dump(self.recordsDict, pickle_out)

    def unpickleRecordings(self):
        with open( "recordedActions.pickle", "rb") as pickle_in:  # rb - read bytes
            self.recordsDict = pickle.load( pickle_in )
            for key in self.recordsDict:
                QTreeWidgetItem(self.ui.creatorEditorActions.topLevelItem(3), [key])

    def creatorRecordDisplay(self):
        self.dialog.show()
        self.dialog.exec_()

    def creatorRecordStart(self):
        if not self.isRecordingRunning:
            self.isRecordingRunning = True
            self.recordDialog.start.setText("Stop")
            self.recorded = []
            keyboard.hook(self.recorded.append)
            mouse.hook(self.recorded.append)

    def creatorRecordStop(self):
        if self.isRecordingRunning:
            self.isRecordingRunning = False
            self.recordDialog.start.setText("Nagraj")
            mouse.unhook( self.recorded.append )
            keyboard.unhook( self.recorded.append )
            self.creatorRecordUpdateTimeAndCuts()

    def creatorRecordToggle(self):
        if not self.isRecordingRunning and not self.isMacroRunning:
            self.creatorRecordStart()
        else:
            self.creatorRecordStop()

    def creatorRecordUpdateTimeAndCuts(self):
        self.recordDialog.timeBase.setText(str("%.2f" % (self.recorded[-1].time - self.recorded[0].time)))
        self.recordDialog.cutTimeLeft.setMaximum((self.recorded[-1].time - self.recorded[0].time) / 2)
        self.recordDialog.cutTimeRight.setMaximum((self.recorded[-1].time - self.recorded[0].time) / 2)
        self.creatorRecordCut()
        self.creatorRecordTimeFinalUpdate()

    def creatorRecordHotkeyChange(self):
        hotkey = self.recordDialog.recordingHotkey.keySequence().toString()
        if hotkey != '':
            print( "creatorRecordHotkeyChange", hotkey )
            if self.creatorRecordHotkey != '':
                keyboard.remove_hotkey( self.creatorRecordHotkey )
            keyboard.add_hotkey(hotkey, self.creatorRecordToggle)
            self.creatorRecordHotkey = hotkey
        else:
            print("cretorRecordHotkeyChange ''")
            keyboard.remove_hotkey( self.creatorRecordHotkey )
            self.creatorRecordHotkey = hotkey

    def creatorPreviewHotkeyChange(self):
        hotkey = self.recordDialog.previewHotkey.keySequence().toString()
        if hotkey != '':
            print("creatorPreviewHotkeyChange", hotkey)
            if self.creatorRecordHotkey != '':
                keyboard.remove_hotkey(self.creatorPreviewHotkey)
            keyboard.add_hotkey(hotkey, self.creatorRecordPreviewToggle)
            self.creatorPreviewHotkey = hotkey
        else:
            print("cretorRecordHotkeyChange ''")
            keyboard.remove_hotkey(self.creatorRecordHotkey)
            self.creatorRecordHotkey = hotkey
######################################################################################

    def creatorRecordPreviewStart( self, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        timedelta = time.time()
        self.macroThread = threading.Event()
        state = keyboard.stash_state()
        t0 = time.time()
        last_time = 0

        for event in self.recordedFinal:
            if speed_factor > 0:
                target_time = t0 + (event.time - last_time) / speed_factor
                real_wait_time = target_time - time.time()
                if real_wait_time > 0:
                    if self.macroThread.wait(timeout=real_wait_time):
                        break
                t0 = target_time
                last_time = event.time
            if isinstance(event, MoveEvent) and include_moves:
                mouse.move(event.x, event.y)
            elif isinstance(event, ButtonEvent) and include_clicks:
                if event.event_type == mouse.UP:
                    mouse.release(event.button)
                else:
                    mouse.press(event.button)
            elif isinstance(event, KeyboardEvent) and include_keyboard:
                key = event.scan_code or event.name
                keyboard.press(key) if event.event_type == keyboard.KEY_DOWN else keyboard.release(key)
            elif isinstance(event, WheelEvent) and include_wheel:
                mouse.wheel(event.delta)
        self.isMacroRunning = False
        keyboard.restore_modifiers(state)
        keyboard.release( self.recordDialog.recordingHotkey.keySequence().toString() )
        keyboard.release( self.recordDialog.previewHotkey.keySequence().toString() )
        print( time.time() - timedelta )
        print("creatorRecordPreview")

    def creatorRecordPreviewPrep(self):
        print('creatorRecordPreviewPrep')
        if self.recorded != []:
            self.isMacroRunning = True
            self.creatorRecordCut()
            self.creatorRecordFinalEdit()
            thread = threading.Thread(target=lambda: self.creatorRecordPreviewStart(speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked() ))
            thread.start()

    def creatorRecordPreviewStop(self):
        print('creatorRecordPreviewStop')
        self.macroThread.set()
        self.isMacroRunning = False

    def creatorRecordPreviewToggle(self):
        print('creatorRecordPreviewToggle')
        if not self.isMacroRunning and not self.isRecordingRunning:
            self.creatorRecordPreviewPrep()
        else:
            self.creatorRecordPreviewStop()

######################################################################################################

    def creatorRecordOverwriteConfirmation(self):
        msg = QMessageBox()
        msg.setWindowTitle("Nagranie o tej nazwie już istnieje!")
        msg.setText("Czy na pewno chcesz zapisać to nagranie pod tą nazwą?")
        msg.setInformativeText("Spowoduje to nadpisanie istniejącego nagrania!")
        msg.setIcon( QMessageBox.Warning )
        msg.setStandardButtons( QMessageBox.Ok | QMessageBox.Cancel )
        msg.setDefaultButton( QMessageBox.Cancel )
        msg.buttonClicked.connect( self.creatorRecordOverwriteConfirmed )
        x = msg.exec_()

    def creatorRecordOverwriteConfirmed(self, i):
        if i.text() == 'OK':
            self.recordsDict[self.recordDialog.name.text()] = Recording( name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recorded, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked() )
            print("Overwritten")

    def creatorRecordAddToActions(self):
        print( 'creatorRecordAddToActions' )
        if self.recordDialog.name.text() != '':
            if self.recordDialog.name.text() in self.recordsDict:
                self.creatorRecordOverwriteConfirmation()
            else:
                QTreeWidgetItem( self.ui.creatorEditorActions.topLevelItem(3), [self.recordDialog.name.text()] )
                self.recordsDict[self.recordDialog.name.text()] = Recording( name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recorded, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked() )

    def creatorRecordOpenInEditor(self):
        print( self.ui.creatorEditorActions.selectedItems()[0].text(0) )
        selected = self.recordsDict[self.ui.creatorEditorActions.selectedItems()[0].text(0)]
        self.recordDialog.name.setText( selected.name )
        self.recorded = selected.events
        self.recordDialog.replaySpeed.setValue( selected.speed_factor )
        self.recordDialog.cutTimeLeft.setValue( selected.cutLeft )
        self.recordDialog.cutTimeRight.setValue( selected.cutRight )
        self.recordDialog.includeMoves.setChecked( selected.include_moves )
        self.recordDialog.includeClicks.setChecked( selected.include_clicks )
        self.recordDialog.includeWheel.setChecked( selected.include_wheel )
        self.recordDialog.includeKeyboard.setChecked( selected.include_keyboard )

        self.creatorRecordUpdateTimeAndCuts()

    def creatorEditorDelete(self):
        print( 'creatorEditorDelete' )
        # print( self.ui.creatorEditorActions.indexFromItem(self.ui.creatorEditorActions.selectedItems()[0], 0 ).parent().row() )
        if self.ui.creatorEditorActions.indexFromItem(self.ui.creatorEditorActions.selectedItems()[0], 0 ).parent().row() == 3:  # Upewniamy się, że kasujemy z zakładki "nagrane"
            self.recordsDict.pop( self.ui.creatorEditorActions.selectedItems()[0].text(0), None )
            self.ui.creatorEditorActions.topLevelItem(3).removeChild(self.ui.creatorEditorActions.selectedItems()[0])

    def creatorRecordCut(self):
        if self.recordDialog.cutTimeLeft.value() > 0:
            print( 'creatorRecordCutLeft' )
            for i in range( len(self.recorded) ):
                if self.recorded[i].time > self.recorded[0].time + self.recordDialog.cutTimeLeft.value():
                    self.recordedCut = self.recorded[i:]
                    break
        else:
            self.recordedCut = self.recorded
        if self.recordDialog.cutTimeRight.value() > 0:
            print('creatorRecordCutRight')
            for i in reversed(range(len(self.recordedCut))):
                if i == 0:
                    self.recordedCut = []
                elif self.recordedCut[i].time < self.recordedCut[-1].time - self.recordDialog.cutTimeRight.value():
                    self.recordedCut = self.recordedCut[:i]
                    break

    def creatorRecordRightSliderSpinBoxSync(self):  # Slider changes value => SpinBox value is changed
        if self.recordDialog.timeBase.text() != '':
            value = self.recordDialog.cutSliderRight.value() / 1000 * float( self.recordDialog.timeBase.text() )
            blocker = QSignalBlocker( self.recordDialog.cutTimeRight )
            self.recordDialog.cutTimeRight.setValue( value )
            blocker.unblock()
            self.creatorRecordCut()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordRightSpinBoxSliderSync(self):  # SpinBox changes value => Slider value is changed
        if self.recordDialog.timeBase.text() != '':
            value = round( self.recordDialog.cutTimeRight.value() / float( self.recordDialog.timeBase.text() ) * 1000 )
            blocker = QSignalBlocker( self.recordDialog.cutSliderRight )
            self.recordDialog.cutSliderRight.setValue( value )
            blocker.unblock()
            self.creatorRecordCut()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordLeftSliderSpinBoxSync(self):  # Slider changes value => SpinBox value is changed
        if self.recordDialog.timeBase.text() != '':
            value = self.recordDialog.cutSliderLeft.value() / 1000 * float( self.recordDialog.timeBase.text() )
            blocker = QSignalBlocker(self.recordDialog.cutTimeLeft)
            self.recordDialog.cutTimeLeft.setValue( value )
            blocker.unblock()
            self.creatorRecordCut()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordLeftSpinBoxSliderSync(self):  # SpinBox changes value => Slider value is changed
        if self.recordDialog.timeBase.text() != '':
            value = round( self.recordDialog.cutTimeLeft.value() / float( self.recordDialog.timeBase.text() ) * 1000 )
            blocker = QSignalBlocker( self.recordDialog.cutSliderLeft )
            self.recordDialog.cutSliderLeft.setValue( value )
            blocker.unblock()
            self.creatorRecordCut()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordTimeFinalUpdate(self):
        if self.recordedCut != []:
            self.recordDialog.timeFinal.setText( str( "%.2f" % ( self.recordedCut[-1].time - self.recordedCut[0].time )))   # ( ( self.recordedCut[-1].time - self.recordedCut[0].time ) * self.recordDialog.replaySpeed.value() )))
        else:
            self.recordDialog.timeFinal.setText('0,00')

    def creatorRecordFinalEdit(self):
        if self.recordedCut != []:
            self.recordedFinal = []
            t0 = float( self.recordedCut[0].time )
            for i in range( len( self.recordedCut ) ):
                if type( self.recordedCut[i] ) == ButtonEvent:
                    self.recordedFinal.append( ButtonEvent( self.recordedCut[i].event_type, self.recordedCut[i].button, self.recordedCut[i].time - t0 ) )
                elif type( self.recordedCut[i] ) == WheelEvent:
                    self.recordedFinal.append( WheelEvent( self.recordedCut[i].delta, self.recordedCut[i].time - t0 ) )
                elif type( self.recordedCut[i] ) == MoveEvent:
                    self.recordedFinal.append( MoveEvent( self.recordedCut[i].x, self.recordedCut[i].y, self.recordedCut[i].time - t0 ) )
                elif type( self.recordedCut[i] ) == KeyboardEvent:
                    self.recordedFinal.append( deepcopy(self.recordedCut[i]) )
                    self.recordedFinal[i].time = float( self.recordedFinal[i].time - t0 )
                else:
                    print("Nieznany typ eventu")

    def creatorEditorTreeViewUpdate(self):
        self.treeModel.clear()
        # self.ui.creatorEditorTreeView.setModel(self.treeModel)
        self.rootNode = self.treeModel.invisibleRootItem()
        self.treeModel.setColumnCount(2)
        self.ui.creatorEditorTreeView.setColumnWidth(0, 300)
        # item = MacroEditorItem(MoveEvent(100, 100, 0), 'Ruch')
        # self.rootNode.appendRow(item)
        for event in self.recordedFinal:  # self.macroElements
            if isinstance( event, ButtonEvent ):
                self.rootNode.appendRow(MacroEditorItem(event, self.macroElementNametags[type(event).__name__ + event.event_type]))
            elif isinstance( event, MoveEvent ):
                self.rootNode.appendRow(MacroEditorItem(event, self.macroElementNametags[type(event).__name__]))
            elif isinstance( event, WheelEvent ):
                self.rootNode.appendRow(MacroEditorItem(event, self.macroElementNametags[type(event).__name__]))
            elif isinstance( event, KeyboardEvent ):
                self.rootNode.appendRow(MacroEditorItem(event, self.macroElementNametags[type(event).__name__ + event.event_type]))

    def creatorAddActionToMacro(self):
        # print( self.ui.creatorEditorTreeView.selectedIndexes() )
        if not self.ui.creatorEditorActions.selectedItems() == []:  # if some action in the action list is selected
            item_name = self.ui.creatorEditorActions.selectedItems()[0].text(0)
            print( 'creatorAddActionToMacro -', item_name )
            if self.ui.creatorEditorTreeView.selectedIndexes() == []:   # if no action in the macro is selected
                item = MacroEditorItem( self.macroElementNameInterpreter[item_name], item_name )
                self.rootNode.appendRow(item)
                if item_name == "Wykonaj N razy":
                    item_name = "Początek pętli"
                    item.appendRow([MacroEditorItem(self.macroElementNameInterpreter[item_name], item_name), QStandardItem()])
                    self.ui.creatorEditorTreeView.setExpanded( item.index(), True )
            else:
                parent_index = self.ui.creatorEditorTreeView.selectedIndexes()[0].parent()
                if not parent_index.isValid():    # if item is from top level of the tree
                    item = MacroEditorItem( self.macroElementNameInterpreter[item_name], item_name )
                    self.rootNode.insertRow( self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1, item )
                    self.rootNode.setChild(self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1, item)
                    if item_name == "Wykonaj N razy":
                        item_name = "Początek pętli"
                        item.appendRow([MacroEditorItem(self.macroElementNameInterpreter[item_name], item_name), QStandardItem()])
                        self.ui.creatorEditorTreeView.setExpanded( item.index(), True )
                else:
                    item = MacroEditorItem(self.macroElementNameInterpreter[item_name], item_name)
                    self.treeModel.itemFromIndex(parent_index).insertRow( self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1, item )
                    self.treeModel.itemFromIndex(parent_index).setChild(self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1, item)
                    if item_name == "Wykonaj N razy":
                        item_name = "Początek pętli"
                        item.appendRow([MacroEditorItem(self.macroElementNameInterpreter[item_name], item_name), QStandardItem()])
                        self.ui.creatorEditorTreeView.setExpanded( item.index(), True )

                # self.treeModel.itemFromIndex(index).insertRow( 0, MacroEditorItem(self.macroElementNameInterpreter[item_name], item_name))

                # good for ForEvent!
                # item_name = self.ui.creatorEditorActions.selectedItems()[0].text(0)
                # index = self.ui.creatorEditorTreeView.selectedIndexes()[0]
                # self.treeModel.itemFromIndex(index).appendRow( MacroEditorItem( self.macroElementNameInterpreter[item_name], item_name ))

    def inspectThis(self):
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()
        print( 'indexes', indexes )
        print( 'data 0:', indexes[0].data() )
        print( self.treeModel.itemFromIndex( indexes[0] ).action )
        print( 'data 1:', indexes[1].data() )

    def creatorEditorTreeViewClear(self):
        self.treeModel.clear()

    def macroPlay( self, target, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        timedelta = time.time()
        self.macroThread = threading.Event()
        state = keyboard.stash_state()
        wait_events_duration = 0
        for_events_duration = 0
        t0 = time.time()
        last_time = 0

        for event in target:
            if speed_factor > 0:
                theoretical_wait_time = (event.time - last_time) / speed_factor
                target_time = t0 + wait_events_duration + for_events_duration + theoretical_wait_time
                real_wait_time = target_time - time.time()
                if real_wait_time > 0:
                    if self.macroThread.wait(timeout=real_wait_time):
                        break
                t0 += theoretical_wait_time
                last_time = event.time
            if isinstance(event, MoveEvent) and include_moves:
                mouse.move(event.x, event.y)
            elif isinstance(event, ButtonEvent) and include_clicks:
                if event.event_type == mouse.UP:
                    mouse.release(event.button)
                elif event.event_type == mouse.DOWN:
                    mouse.press(event.button)
                elif event.event_type == 'double':    # do testu
                    mouse.double_click(event.button)  #
                elif event.event_type == 'click':     # do testu
                    mouse.click(event.button)         #
                else:
                    print('Nieznany typ eventu myszy')
            elif isinstance(event, KeyboardEvent) and include_keyboard:
                key = event.scan_code or event.name
                if event.event_type == keyboard.KEY_DOWN:
                    keyboard.press(key)
                elif event.event_type == keyboard.KEY_UP:
                    keyboard.release(key)
                elif event.event_type == 'write':
                    keyboard.write(event.scan_code)  # do testu musi być nadpisany tekstem!
                elif event.event_type == 'hotkey':
                    keyboard.send(event.scan_code)   # do testu
                elif event.event_type == 'releaseall':
                    keyboard.stash_state()           # do testu
                else:
                    print('Nieznany typ eventu klawiatury')
            elif isinstance(event, WheelEvent) and include_wheel:
                mouse.wheel(event.delta)
            elif isinstance( event, WaitEvent ):
                if event.event_type == 'mouse':
                    before = time.time()
                    mouse.wait( event.trigger )
                    wait_events_duration += time.time() - before
                elif event.event_type == 'keyboard':
                    before = time.time()
                    keyboard.wait( event.trigger )
                    wait_events_duration += time.time() - before
                elif event.event_type == 'nseconds':
                    time.sleep( event.trigger )
                    wait_events_duration += event.trigger
                else:
                    print( 'Nieznany typ eventu oczekiwania' )
            elif isinstance(event, ForEvent):   # PSUJE CZASY? CHYBA NIE, DO TESTU
                before = time.time()
                for i in range(event.times):
                    self.macroPlay( event.event_list, speed_factor, include_clicks, include_moves, include_wheel, include_keyboard  )
                for_events_duration += time.time() - before
            elif isinstance( event, PlaceholderEvent ):
                pass
            else:
                print('Nieznany typ eventu', event)
        self.isMacroRunning = False
        keyboard.restore_modifiers(state)
        keyboard.release( self.recordDialog.recordingHotkey.keySequence().toString() )
        keyboard.release( self.recordDialog.previewHotkey.keySequence().toString() )
        print( time.time() - timedelta )
        print("creatorRecordPreview")

app = QApplication( sys.argv )

window = MainWindow()
window.show()

sys.exit(app.exec_())
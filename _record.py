import threading
from copy import deepcopy
import pickle
from keyboard import KeyboardEvent
import keyboard
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
from _classes import RecordingEvent

from PySide2.QtWidgets import QMessageBox, QTreeWidgetItem
from PySide2.QtCore import QSignalBlocker


class RecordMethods:
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

    def playRecording(self, recording, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        timedelta = time.time()
        state = keyboard.stash_state()
        t0 = time.time()
        last_time = 0

        for event in recording:
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
        keyboard.restore_modifiers(state)
        keyboard.release(self.recordDialog.recordingHotkey.keySequence().toString())
        keyboard.release(self.recordDialog.previewHotkey.keySequence().toString())
        print(time.time() - timedelta)
        print("playRecording")

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
            self.recordsDict[self.recordDialog.name.text()] = RecordingEvent(name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recorded, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked())
            print("Overwritten")

    def creatorRecordAddToActions(self):
        print( 'creatorRecordAddToActions' )
        if self.recordDialog.name.text() != '':
            if self.recordDialog.name.text() in self.recordsDict:
                self.creatorRecordOverwriteConfirmation()
            else:
                QTreeWidgetItem( self.ui.creatorEditorActions.topLevelItem(3), [self.recordDialog.name.text()] )
                self.recordsDict[self.recordDialog.name.text()] = RecordingEvent(name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recorded, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked())

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

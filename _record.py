import threading
from copy import deepcopy
import pickle
from keyboard import KeyboardEvent
import keyboard
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
from _classes import RecordingEvent, MoveEventV2, ButtonEventV2, WheelEventV2

from PySide2.QtWidgets import QMessageBox, QTreeWidgetItem
from PySide2.QtCore import QSignalBlocker


class RecordMethods:
    def pickleRecordings(self):
        print( 'pickleRecordings' )
        # print( [self.recordDialog.name.text().replace(' ', '_')] )
        with open("recordedActions.pickle", "wb") as pickle_out:  # wb - write bytes
            pickle.dump(self.recordsDict, pickle_out)

    def unpickleRecordings(self):
        print( 'unpickleRecordings' )
        try:
            with open( "recordedActions.pickle", "rb") as pickle_in:  # rb - read bytes
                self.recordsDict = pickle.load( pickle_in )
                for key in self.recordsDict:
                    QTreeWidgetItem(self.ui.creatorEditorActions.topLevelItem(3), [key])
        except:
            print( 'recordedActions.pickle not found!' )

    def creatorRecordDisplay(self):
        print( 'creatorRecordDisplay' )
        if not self.isDialogOpen:
            self.isDialogOpen = True
            self.dialog.move(self.x() + 793, self.y())
            self.dialog.show()
            self.dialog.exec_()

    def creatorRecordStart(self):
        print( 'creatorRecordStart' )
        if not self.isRecordingRunning:
            self.isRecordingRunning = True
            self.recordDialog.start.setText("Stop")
            self.recorded = []
            keyboard.hook(self.recorded.append)
            mouse.hook(self.recorded.append)

    def creatorRecordStop(self):
        print( 'creatorRecordStop' )
        if self.isRecordingRunning:
            self.isRecordingRunning = False
            self.recordDialog.start.setText("Nagraj")
            mouse.unhook( self.recorded.append )
            keyboard.unhook( self.recorded.append )
            self.recordedObject = RecordingEvent(name=self.recordDialog.name.text(),
                                                 cut_left=self.recordDialog.cutTimeLeft.value(),
                                                 cut_right=self.recordDialog.cutTimeRight.value(),
                                                 events=self.recorded,
                                                 speed_factor=self.recordDialog.replaySpeed.value(),
                                                 include_clicks=self.recordDialog.includeClicks.isChecked(),
                                                 include_moves=self.recordDialog.includeMoves.isChecked(),
                                                 include_wheel=self.recordDialog.includeWheel.isChecked(),
                                                 include_keyboard=self.recordDialog.includeKeyboard.isChecked() )
            self.creatorRecordUpdateTimeAndCuts()

    def creatorRecordToggle(self):
        print( 'creatorRecordToggle' )
        if not self.isRecordingRunning and not self.isMacroRunning:
            self.creatorRecordStart()
        else:
            self.creatorRecordStop()

    def creatorRecordUpdateTimeAndCuts(self):
        print( "creatorRecordUpdateTimeAndCuts" )
        self.recordedObject.prepareForPlaying()
        if self.recordedObject.events != []:
            self.recordDialog.timeBase.setText(str("%.2f" % (self.recordedObject.events[-1].time - self.recordedObject.events[0].time ) ) )
            self.recordDialog.cutTimeLeft.setMaximum((self.recordedObject.events[-1].time - self.recordedObject.events[0].time) / 2)
            self.recordDialog.cutTimeRight.setMaximum((self.recordedObject.events[-1].time - self.recordedObject.events[0].time) / 2)
        else:
            self.recordDialog.timeBase.setText( '0' )
            self.recordDialog.cutTimeLeft.setMaximum(0)
            self.recordDialog.cutTimeRight.setMaximum(0)
        self.creatorRecordTimeFinalUpdate()

    def creatorRecordHotkeyChange(self):
        hotkey = self.recordDialog.recordingHotkey.keySequence().toString()
        if hotkey != '':
            print( "creatorRecordHotkeyChange", hotkey )
            if self.creatorRecordHotkey != '':
                try:
                    keyboard.remove_hotkey( self.creatorRecordToggle )
                except KeyError:
                    pass
            keyboard.add_hotkey(hotkey, self.creatorRecordToggle )
            self.creatorRecordHotkey = hotkey
        else:
            print("cretorRecordHotkeyChange ''")
            if self.creatorRecordHotkey != '':
                try:
                    keyboard.remove_hotkey( self.creatorRecordToggle )
                except KeyError:
                    pass
            self.creatorRecordHotkey = hotkey

    def creatorPreviewHotkeyChange(self):
        hotkey = self.recordDialog.previewHotkey.keySequence().toString()
        if hotkey != '':
            print("creatorPreviewHotkeyChange", hotkey)
            if self.creatorPreviewHotkey != '':
                try:
                    keyboard.remove_hotkey( self.creatorRecordPreviewToggle )
                except KeyError:
                    pass
            keyboard.add_hotkey(hotkey, self.creatorRecordPreviewToggle )
            self.creatorPreviewHotkey = hotkey
        else:
            print("cretorRecordHotkeyChange ''")
            if self.creatorPreviewHotkey != '':
                try:
                    keyboard.remove_hotkey( self.creatorRecordPreviewToggle )
                except KeyError:
                    pass
            self.creatorPreviewHotkey = hotkey

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
                    if self.macroAbortEvent.wait(timeout=real_wait_time):
                        keyboard.stash_state()
                        return 'abort'

                t0 = target_time
                last_time = event.time
            if isinstance(event, MoveEventV2) and include_moves:
                mouse.move(event.x, event.y)
            elif isinstance(event, ButtonEventV2) and include_clicks:
                if event.event_type == mouse.UP:
                    mouse.release(event.button)
                else:
                    mouse.press(event.button)
            elif isinstance(event, KeyboardEvent) and include_keyboard:
                key = event.scan_code or event.name
                keyboard.press(key) if event.event_type == keyboard.KEY_DOWN else keyboard.release(key)
            elif isinstance(event, WheelEventV2) and include_wheel:
                mouse.wheel(event.delta)
        keyboard.stash_state()
        self.releaseAllMouseButtons()
        print(time.time() - timedelta)
        print("playRecording")

    def creatorRecordPreviewStart( self, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        print( 'creatorRecordPreviewStart' )
        timedelta = time.time()
        self.macroThread = threading.Event()
        state = keyboard.stash_state()
        t0 = time.time()
        last_time = 0

        self.recordedObject.prepareForPlaying()
        # for event in self.recordedObject.events_final:
        #     print( event.time, '    ', event )
        # print( self.recordedObject.events_final )
        for event in self.recordedObject.events_final:
            # print( 'time =', event.time )
            if speed_factor > 0:
                target_time = t0 + (event.time - last_time) / speed_factor
                real_wait_time = target_time - time.time()
                if real_wait_time > 0:
                    if self.macroThread.wait(timeout=real_wait_time):
                        break
                t0 = target_time
                last_time = event.time
            if isinstance(event, MoveEventV2) and include_moves:
                mouse.move(event.x, event.y)
            elif isinstance(event, ButtonEventV2) and include_clicks:
                if event.event_type == mouse.UP:
                    mouse.release(event.button)
                else:
                    mouse.press(event.button)
            elif isinstance(event, KeyboardEvent) and include_keyboard:
                key = event.scan_code or event.name
                keyboard.press(key) if event.event_type == keyboard.KEY_DOWN else keyboard.release(key)
            elif isinstance(event, WheelEventV2) and include_wheel:
                mouse.wheel(event.delta)
        self.isMacroRunning = False
        keyboard.restore_modifiers(state)
        if self.recordDialog.recordingHotkey.keySequence().toString() != '':
            keyboard.release( self.recordDialog.recordingHotkey.keySequence().toString() )
        if self.recordDialog.previewHotkey.keySequence().toString() != '':
            keyboard.release( self.recordDialog.previewHotkey.keySequence().toString() )
        print( time.time() - timedelta )

    def creatorRecordPreviewPrep(self):
        print('creatorRecordPreviewPrep')
        if self.recorded != []:
            print( 'self.recorded is not empty!' )
            self.recordedObject = RecordingEvent(name=self.recordDialog.name.text(),
                                                 cut_left=self.recordDialog.cutTimeLeft.value(),
                                                 cut_right=self.recordDialog.cutTimeRight.value(),
                                                 events=self.recorded,
                                                 speed_factor=self.recordDialog.replaySpeed.value(),
                                                 include_clicks=self.recordDialog.includeClicks.isChecked(),
                                                 include_moves=self.recordDialog.includeMoves.isChecked(),
                                                 include_wheel=self.recordDialog.includeWheel.isChecked(),
                                                 include_keyboard=self.recordDialog.includeKeyboard.isChecked())
            self.isMacroRunning = True
            # self.recordedObject.cutRecording()
            # self.creatorRecordFinalEdit()
            thread = threading.Thread(target=lambda: self.creatorRecordPreviewStart(speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked() ))
            thread.start()
            thread.join()
            self.creatorRecordPreviewStop()
        else:
            print( 'self.recorded is empty!' )
            print( self.recorded )

    def creatorRecordPreviewStop(self):
        print('creatorRecordPreviewStop')
        self.macroAbortEvent.set()
        self.isMacroRunning = False
        self.releaseAllMouseButtons()
        keyboard.stash_state()

    def creatorRecordPreviewToggle(self):
        print('creatorRecordPreviewToggle')
        if not self.isMacroRunning and not self.isRecordingRunning:
            self.creatorRecordPreviewPrep()
        else:
            self.creatorRecordPreviewStop()

    def creatorRecordOverwriteConfirmation(self):
        print( 'creatorRecordOverwriteConfirmation' )
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
        print( 'creatorRecordOverwriteConfirmed' )
        if i.text() == 'OK':
            self.recordsDict[self.recordDialog.name.text()] = RecordingEvent(name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recordedObject.events, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked())
            self.pickleRecordings()
            print("Overwritten")

    def creatorRecordAddToActions(self):
        print( 'creatorRecordAddToActions' )
        if self.recordDialog.name.text() != '':
            if not(self.recordDialog.name.text() in self.macroElementNametags.values()):
                if self.recordDialog.name.text() in self.recordsDict:
                    self.creatorRecordOverwriteConfirmation()
                else:
                    x = QTreeWidgetItem( self.ui.creatorEditorActions.topLevelItem(3), [self.recordDialog.name.text()] )
                    x.parent().setExpanded(True)
                    self.recordsDict[self.recordDialog.name.text()] = RecordingEvent(name=self.recordDialog.name.text(), cut_left=self.recordDialog.cutTimeLeft.value(), cut_right=self.recordDialog.cutTimeRight.value(), events=self.recordedObject.events, speed_factor=self.recordDialog.replaySpeed.value(), include_clicks=self.recordDialog.includeClicks.isChecked(), include_moves=self.recordDialog.includeMoves.isChecked(), include_wheel=self.recordDialog.includeWheel.isChecked(), include_keyboard=self.recordDialog.includeKeyboard.isChecked())
                    self.pickleRecordings()
            else:
                print( 'Nagranie nie moze sie nazywac jak funkcja wbudowana!' )

    def creatorRecordRightSliderSpinBoxSync(self):  # Slider changes value => SpinBox value is changed
        print( 'creatorRecordRightSliderSpinBoxSync' )
        if self.recordDialog.timeBase.text() != '':
            value = self.recordDialog.cutSliderRight.value() / 1000 * float( self.recordDialog.timeBase.text() )

            blocker = QSignalBlocker( self.recordDialog.cutTimeRight )
            self.recordDialog.cutTimeRight.setValue( value )
            blocker.unblock()

            self.recordedObject.cutRight = self.recordDialog.cutTimeRight.value()
            self.recordedObject.cutRecording()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordRightSpinBoxSliderSync(self):  # SpinBox changes value => Slider value is changed
        print( 'creatorRecordRightSpinBoxSliderSync' )
        if self.recordDialog.timeBase.text() != '':
            base_time = float( self.recordDialog.timeBase.text() )
            if base_time != 0:
                value = round( self.recordDialog.cutTimeRight.value() / base_time * 1000 )
            else:
                value = 0

            blocker = QSignalBlocker( self.recordDialog.cutSliderRight )
            self.recordDialog.cutSliderRight.setValue( value )
            blocker.unblock()

            self.recordedObject.cutRight = self.recordDialog.cutTimeRight.value()
            self.recordedObject.cutRecording()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordLeftSliderSpinBoxSync(self):  # Slider changes value => SpinBox value is changed
        print( 'creatorRecordLeftSliderSpinBoxSync' )
        if self.recordDialog.timeBase.text() != '':
            value = self.recordDialog.cutSliderLeft.value() / 1000 * float( self.recordDialog.timeBase.text() )

            blocker = QSignalBlocker(self.recordDialog.cutTimeLeft)
            self.recordDialog.cutTimeLeft.setValue( value )
            blocker.unblock()

            self.recordedObject.cutLeft = self.recordDialog.cutTimeLeft.value()
            self.recordedObject.cutRecording()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordLeftSpinBoxSliderSync(self):  # SpinBox changes value => Slider value is changed
        print('creatorRecordLeftSpinBoxSliderSync')
        if self.recordDialog.timeBase.text() != '':
            base_time = float( self.recordDialog.timeBase.text() )
            if base_time != 0:
                value = round( self.recordDialog.cutTimeLeft.value() / base_time * 1000 )
            else:
                value = 0

            blocker = QSignalBlocker( self.recordDialog.cutSliderLeft )
            self.recordDialog.cutSliderLeft.setValue( value )
            self.recordedObject.cutLeft = self.recordDialog.cutTimeLeft.value()
            blocker.unblock()

            self.recordedObject.cutRecording()
            self.creatorRecordTimeFinalUpdate()

    def creatorRecordTimeFinalUpdate(self):
        if self.recordedObject.events_final != []:
            print('creatorRecordTimeFinalUpdate')
            print( self.recordedObject.events_final )
            self.recordDialog.timeFinal.setText( str( "%.2f" % self.recordedObject.events_final[-1].time ))   # ( ( self.recordedCut[-1].time - self.recordedCut[0].time ) * self.recordDialog.replaySpeed.value() )))

        else:
            print('creatorRecordTimeFinalUpdate no events')
            self.recordDialog.timeFinal.setText('0.00')
        print('sukces')

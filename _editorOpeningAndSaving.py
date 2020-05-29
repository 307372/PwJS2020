import keyboard
from mouse import ButtonEvent, WheelEvent, MoveEvent
from _classes import RecordingEvent, MoveEventV2, WheelEventV2
from PySide2.QtGui import QKeySequence



class OpeningAndSaving:

    def creatorOpenSelectedInEditor(self):
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()
        if not indexes == []:
            self.currentlyEditedItem = self.treeModel.itemFromIndex(self.ui.creatorEditorTreeView.selectedIndexes()[0])
            event = self.treeModel.itemFromIndex(indexes[0]).action
            self.recordDialog.addToActions.setDisabled(True)
            event_type = type(event).__name__
            # print( event_type )
            # TUTAJ DAC RZECZY self.recordDialog.addToActions.
            if event_type in ['MoveEvent', 'MoveEventV2']:
                print(event_type, 'id=0')
                self.creatorSelectEditorPageByID(0)
                print('Edition implemented!')
                self.openInEditorMouseMovement()

            elif event_type in ['ButtonEvent', 'ButtonEventV2']:
                print(event_type, 'id=1')
                self.creatorSelectEditorPageByID(1)
                print('Edition implemented')
                self.openInEditorMouseButton()

            elif event_type in ['WheelEvent', 'WheelEventV2']:
                self.creatorSelectEditorPageByID(2)
                print(event_type, 'id=2')
                print('Edition implemented')
                self.openInEditorMouseWheel()

            elif event_type == 'KeyboardEvent':
                if event.event_type == 'releaseall':
                    print(event.event_type, 'id=None')

                elif event.event_type == 'up' or event.event_type == 'down' or event.event_type == 'click':
                    print(event.event_type, 'id=3')
                    self.creatorSelectEditorPageByID(3)
                    print('Edition implemented')
                    self.openInEditorKeyboardButton()

                elif event.event_type == 'hotkey':
                    print(event.event_type, 'id=4')
                    self.creatorSelectEditorPageByID(4)
                    print('Edition implemented')
                    self.openInEditorKeyboardHotkey()

                elif event.event_type == 'write':
                    print(event.event_type, 'id=5')
                    self.creatorSelectEditorPageByID(5)
                    print('Edition implemented')
                    self.openInEditorKeyboardWrite()

                else:
                    print('Nieznany typ KeyboardEventu!', event.event_type)

            elif event_type == 'WaitEvent':
                if event.event_type == 'mouse':
                    print(event.event_type, 'id=6')
                    self.creatorSelectEditorPageByID(6)
                    print('Edition implemented')
                    self.openInEditorWaitMouse()

                elif event.event_type == 'keyboard':
                    print(event.event_type, 'id=7')
                    self.creatorSelectEditorPageByID(7)
                    print('Edition implemented')
                    self.openInEditorWaitKeyboard()

                elif event.event_type == 'nseconds':
                    print(event.event_type, 'id=8')
                    self.creatorSelectEditorPageByID(8)
                    print('Edition implemented')
                    self.openInEditorWaitNSeconds()

                else:
                    print('Nieznany typ WaitEventu', event.event_type)

            elif event_type == 'ForEvent':
                print(event_type, 'id=9')
                self.creatorSelectEditorPageByID(9)
                print('Edition implemented')
                self.openInEditorForLoop()

            elif event_type == 'RecordingEvent':
                print(event_type, 'id=10')
                self.recordDialog.addToActions.setDisabled(False)
                self.creatorSelectEditorPageByID(10)
                print( 'Edition implemented' )
                self.openInEditorRecording()

            elif event_type == 'PlaceholderEvent':
                print(event_type, 'id=None')

            else:
                print('W ogóle nieznany typ eventu!', event_type)
            self.creatorRecordDisplay()

    def openInEditorMouseMovement(self):
        print( self.currentlyEditedItem )
        if isinstance( self.currentlyEditedItem, MoveEvent ):
            print( 'MoveEvent; Assuming absolute = true & exchanging for MoveEventV2' )
            self.treeModel.itemFromIndex(self.ui.creatorEditorTreeView.selectedIndexes()[0]).action = MoveEventV2( self.currentlyEditedItem.x, self.currentlyEditedItem.y, self.currentlyEditedItem.time, duration=True, absolute=True)
            # print(self.treeModel.itemFromIndex(self.ui.creatorEditorTreeView.selectedIndexes()[0]).action)
            # print( self.macroElements[0].action )
        self.recordDialog.movementAbsolute.setChecked( self.currentlyEditedItem.action.absolute )
        self.recordDialog.movementDuration.setValue( self.currentlyEditedItem.action.duration )
        self.recordDialog.movementX.setValue( self.currentlyEditedItem.action.x )
        self.recordDialog.movementY.setValue( self.currentlyEditedItem.action.y )
        # self.recordDialog.movementAbsolute.setChecked()

    def openInEditorMouseButton(self):
        print( self.currentlyEditedItem )

        action = self.currentlyEditedItem.action
        print( action )
        if action.event_type == 'click':
            self.recordDialog.typeButtonClick.setChecked(True)
        elif action.event_type == 'double':
            self.recordDialog.typeButtonDoubleClick.setChecked(True)
        elif action.event_type == 'down':
            self.recordDialog.typeButtonHold.setChecked(True)
        elif action.event_type == 'up':
            self.recordDialog.typeButtonRelease.setChecked(True)

        if action.button == 'left':
            self.recordDialog.mouseButtonSelection.setCurrentIndex(0)

        elif action.button == 'right':
            self.recordDialog.mouseButtonSelection.setCurrentIndex(1)

        elif action.button == 'middle':
            self.recordDialog.mouseButtonSelection.setCurrentIndex(2)

    def openInEditorMouseWheel(self):
        self.recordDialog.mouseWheelDelta.setValue( self.currentlyEditedItem.action.delta )

    def openInEditorKeyboardButton(self):
        action = self.currentlyEditedItem.action
        print( action )
        if action.event_type == 'click':
            self.recordDialog.typeKeyClick.setChecked(True)
        elif action.event_type == 'down':
            self.recordDialog.typeKeyHold.setChecked(True)
        elif action.event_type == 'up':
            self.recordDialog.typeKeyRelease.setChecked(True)
        else:
            print("Cos poszlo nie tak! Nieznany event type", action.event_type)
        self.recordDialog.keyboardButtonSelection.setText( self.currentlyEditedItem.action.name )

    def openInEditorKeyboardHotkey(self):
        if self.currentlyEditedItem.action.name is not None:
            self.recordDialog.keyboardHotkeySelection.setKeySequence( self.currentlyEditedItem.action.name )

    def openInEditorKeyboardWrite(self):
        self.recordDialog.keyboardWriteTextfield.setPlainText( self.currentlyEditedItem.action.name )

    def openInEditorWaitMouse(self):
        print( self.currentlyEditedItem.action )
        event = self.currentlyEditedItem.action.triggering_event
        event_index = None
        if event == 'down':
            event_index = 0
        elif event == 'up':
            event_index = 1
        elif event == 'double':
            event_index = 2
        else:
            print( 'Nieznany triggerujący event:', event )

        button = self.currentlyEditedItem.action.target_button
        button_index = None
        if button == 'left':
            button_index = 0
        elif button == 'right':
            button_index = 1
        elif button == 'middle':
            button_index = 2
        else:
            print( 'Nieznany przycisk:', button )

        self.recordDialog.typeOfMouseAction.setCurrentIndex( event_index )
        self.recordDialog.typeOfMouseButton.setCurrentIndex( button_index )

    def openInEditorWaitKeyboard(self):
        self.recordDialog.waitKeyboardHotkey.setKeySequence( QKeySequence.fromString( str(self.currentlyEditedItem.action.target_button) ) )
        self.recordDialog.waitKeyboardSuppressor.setChecked( self.currentlyEditedItem.action.suppress )

    def openInEditorWaitNSeconds(self):
        self.recordDialog.waitNSecondsTime.setValue( self.currentlyEditedItem.action.wait_time )

    def openInEditorForLoop(self):
        self.recordDialog.forLoopTimes.setValue( self.currentlyEditedItem.action.times )

    def openInEditorRecording(self):
        # print( self.ui.creatorEditorActions.selectedItems()[0].text(0) )

        recording_event = self.currentlyEditedItem.action
        self.recordDialog.name.setText( recording_event.name )
        self.recordedObject = recording_event
        self.recordDialog.replaySpeed.setValue( recording_event.speed_factor )
        self.recordDialog.cutTimeLeft.setValue( recording_event.cutLeft )
        self.recordDialog.cutTimeRight.setValue( recording_event.cutRight )
        self.recordDialog.includeMoves.setChecked( recording_event.include_moves )
        self.recordDialog.includeClicks.setChecked( recording_event.include_clicks )
        self.recordDialog.includeWheel.setChecked( recording_event.include_wheel )
        self.recordDialog.includeKeyboard.setChecked( recording_event.include_keyboard )

        self.creatorRecordUpdateTimeAndCuts()

    def saveEditedItem(self):

        if self.currentlyEditedItem is not None:
            page = self.recordDialog.pages.currentIndex()
            if page == 0:  # mouseMovement
                print(page, 'id=0')
                print('Saving implemented!')
                self.editorSaveMouseMovement()

            elif page == 1:  # mouseButton
                print(page, 'id=1')
                print('Saving implemented!')
                self.editorSaveMouseButton()

            elif page == 2:  # mouseWheel
                print(page, 'id=2')
                print('Saving implemented!')
                self.editorSaveMouseWheel()

            elif page == 3:  # keyboardButton
                print(page, 'id=3')
                print('Saving implemented')
                self.editorSaveKeyboardButton()

            elif page == 4:  # keyboardHotkey
                print(page, 'id=4')
                print('Saving implemented (?)')
                self.editorSaveKeyboardHotkey()

            elif page == 5:  # keyboardWrite
                print(page, 'id=5')
                print('Saving implemented (?)')
                self.editorSaveKeyboardWrite()

            elif page == 6:  # waitMouse
                print(page, 'id=6')
                print('Saving implemented')
                self.editorSaveWaitMouse()

            elif page == 7:  # waitKeyboard
                print(page, 'id=7')
                print('Saving implemented')
                self.editorSaveWaitKeyboard()

            elif page == 8:  # wait N seconds
                print(page, 'id=8')
                print('Saving implemented')
                self.editorSaveWaitNSeconds()

            elif page == 9:  # forLoop
                print(page, 'id=9')
                print('Saving implemented')
                self.editorSaveForLoop()

            elif page == 10:  # recording
                print(page, 'id=10')
                print('Saving not fully implemented')
                self.editorSaveRecording()
            else:
                print('Nieznana strona! id =', page)
            self.macroUpdateTime()

    def editorSaveMouseMovement(self):
        text = 'Przemieść kursor '
        self.currentlyEditedItem.action.absolute = self.recordDialog.movementAbsolute.isChecked()
        self.currentlyEditedItem.action.duration = self.recordDialog.movementDuration.value()
        self.currentlyEditedItem.action.x = self.recordDialog.movementX.value()
        self.currentlyEditedItem.action.y = self.recordDialog.movementY.value()
        print( 'saved', self.currentlyEditedItem, '!' )
        if self.currentlyEditedItem.action.absolute:
            text += 'do '
        else:
            text += 'o '
        text += 'x=' + str(self.currentlyEditedItem.action.x) + ', y=' + str(self.currentlyEditedItem.action.y)
        if self.recordDialog.movementDuration.value() > 0:
            text += ' w ' + str(self.recordDialog.movementDuration.value()) + 's'
        self.currentlyEditedItem.setText( text )

    def editorSaveMouseButton(self):
        print( self.currentlyEditedItem )

        button = self.recordDialog.mouseButtonSelection.currentText()
        text = ''

        if self.recordDialog.typeButtonClick.isChecked():
            self.currentlyEditedItem.action.event_type = 'click'
            text = 'Kliknij '
        elif self.recordDialog.typeButtonDoubleClick.isChecked():
            self.currentlyEditedItem.action.event_type = 'double'
            text = 'Kliknij podwójnie '
        elif self.recordDialog.typeButtonHold.isChecked():
            self.currentlyEditedItem.action.event_type = 'down'
            text = 'Przytrzymaj '
        elif self.recordDialog.typeButtonRelease.isChecked():
            self.currentlyEditedItem.action.event_type = 'up'
            text = 'Puść '

        else:
            print( 'Error: No radio selected?' )

        if button == 'Lewy':
            self.currentlyEditedItem.action.button = 'left'
            text += 'lewy przycisk myszy'

        elif button == 'Prawy':
            self.currentlyEditedItem.action.button = 'right'
            text += 'prawy przycisk myszy'

        elif button == 'Środkowy':
            self.currentlyEditedItem.action.button = 'middle'
            text += 'środkowy przycisk myszy'

        print( self.currentlyEditedItem )
        self.currentlyEditedItem.setText( text )
        print( self.macroElements[0] )

    def editorSaveMouseWheel(self):
        print( 'pre:', self.currentlyEditedItem )
        self.currentlyEditedItem.action = WheelEventV2( self.recordDialog.mouseWheelDelta.value(), 0 )
        text = 'Ruch kółka myszy o ' + str(self.recordDialog.mouseWheelDelta.value())
        self.currentlyEditedItem.setText( text )
        print( 'post:', self.currentlyEditedItem )

    def editorSaveKeyboardButton(self):
        text = ''
        if self.recordDialog.typeKeyClick.isChecked():
            self.currentlyEditedItem.action.event_type = 'click'
            text = 'Kliknij klawisz '

        elif self.recordDialog.typeKeyHold.isChecked():
            self.currentlyEditedItem.action.event_type = 'down'
            text = 'Przytrzymaj klawisz '

        elif self.recordDialog.typeKeyRelease.isChecked():
            self.currentlyEditedItem.action.event_type = 'up'
            text = 'Puść klawisz '

        if self.recordDialog.keyboardButtonSelection.text() != '':
            self.currentlyEditedItem.action.scan_code = None
            self.currentlyEditedItem.action.name = keyboard.normalize_name(self.recordDialog.keyboardButtonSelection.text())
            text += self.recordDialog.keyboardButtonSelection.text()
        self.currentlyEditedItem.setText( text )

    def editorSaveKeyboardHotkey(self):
        self.currentlyEditedItem.action.name = self.recordDialog.keyboardHotkeySelection.keySequence().toString()
        text = "Użyj skrótu klawiszowego " + self.recordDialog.keyboardHotkeySelection.keySequence().toString()
        self.currentlyEditedItem.setText( text )
        print(self.currentlyEditedItem.action.name)
        print(self.currentlyEditedItem.action)

    def editorSaveKeyboardWrite(self):
        self.currentlyEditedItem.action.scan_code = self.recordDialog.keyboardWriteTextfield.toPlainText()
        if self.currentlyEditedItem.action.name != '':
            self.currentlyEditedItem.setText( 'Wypisz tekst (wpisany)' )
        else:
            self.currentlyEditedItem.setText( 'Wypisz tekst' )

    def editorSaveWaitMouse(self):
        event_text = self.recordDialog.typeOfMouseAction.currentText()
        text = 'Czekaj na '
        if event_text == 'Wciśnięcie przycisku myszy':
            self.currentlyEditedItem.action.triggering_event = 'down'
            text += 'wciśnięcie '
        elif event_text == 'Puszczenie przycisku myszy':
            self.currentlyEditedItem.action.triggering_event = 'up'
            text += 'puszczenie '
        elif event_text == 'Podwójne kliknięcie przycisku myszy':
            self.currentlyEditedItem.action.triggering_event = 'double'
            text += 'podwójne kliknięcie '
        else:
            print( 'Nieznany tekst:', event_text )

        button_text = self.recordDialog.typeOfMouseButton.currentText()

        if button_text == 'Lewy':
            self.currentlyEditedItem.action.target_button = 'left'
            text += 'LPM'
        elif button_text == 'Prawy':
            self.currentlyEditedItem.action.target_button = 'right'
            text += 'PPM'
        elif button_text == 'Środkowy':
            self.currentlyEditedItem.action.target_button = 'middle'
            text += 'ŚPM'
        else:
            print( 'Nieznany tekst:', button_text )

        self.currentlyEditedItem.setText( text )

            # self.currentlyEditedItem.action

    def editorSaveWaitKeyboard(self):
        self.currentlyEditedItem.action.target_button = self.recordDialog.waitKeyboardHotkey.keySequence().toString()
        self.currentlyEditedItem.action.suppress = self.recordDialog.waitKeyboardSuppressor.isChecked()
        text = 'Czekaj na wciśnięcie ' + str( self.currentlyEditedItem.action.target_button )
        if self.currentlyEditedItem.action.suppress:
            text += ' (wyciszone)'
        self.currentlyEditedItem.setText( text )

    def editorSaveWaitNSeconds(self):
        self.currentlyEditedItem.action.wait_time = self.recordDialog.waitNSecondsTime.value()
        text = 'Czekaj ' + str( self.currentlyEditedItem.action.wait_time ) + ' sekund'
        self.currentlyEditedItem.setText( text )

    def editorSaveForLoop(self):
        self.currentlyEditedItem.action.times = self.recordDialog.forLoopTimes.value()
        text = 'Wykonaj ' + str( self.currentlyEditedItem.action.times ) + ' razy'
        self.currentlyEditedItem.setText( text )

    def editorSaveRecording(self):
        name = self.recordDialog.name.text()
        events = self.recordedObject.events
        speed_factor = self.recordDialog.replaySpeed.value()
        cutLeft = self.recordDialog.cutTimeLeft.value()
        cutRight = self.recordDialog.cutTimeRight.value()
        include_clicks = self.recordDialog.includeClicks.isChecked()
        include_moves = self.recordDialog.includeMoves.isChecked()
        include_wheel = self.recordDialog.includeWheel.isChecked()
        include_keyboard = self.recordDialog.includeKeyboard.isChecked()
        self.currentlyEditedItem.action = RecordingEvent( name=name, events=events, speed_factor=speed_factor,
                                                          cut_left=cutLeft, cut_right=cutRight,
                                                          include_clicks=include_clicks, include_moves=include_moves,
                                                          include_wheel=include_wheel, include_keyboard=include_keyboard)


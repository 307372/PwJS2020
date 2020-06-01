import threading
from copy import deepcopy
from keyboard import KeyboardEvent
import keyboard
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QKeySequence
from PySide2.QtWidgets import QKeySequenceEdit


class RecordingEvent:
    def __init__(self, name='', events=[], speed_factor=1.0, cut_left=0, cut_right=0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True, time=0):
        print( '__init__' )
        self.event_type = 'RecordingEvent'
        self.name = name
        self.events = events
        self.events_included = []
        self.events_cut = []
        self.events_final = []
        self.speed_factor = speed_factor
        self.cutLeft = cut_left
        self.cutRight = cut_right
        self.include_clicks = include_clicks
        self.include_moves = include_moves
        self.include_wheel = include_wheel
        self.include_keyboard = include_keyboard
        self.time = time

        self.prepareForPlaying()

    def __str__(self):
        return 'RE(event_type=' + str(self.event_type) + \
               '\nname=' + str(self.name) + \
               '\nlen(events)=' + str(len(self.events)) + \
               '\nlen(events_included)=' + str(len(self.events_included)) + \
               '\nlen(events_cut)=' + str(len(self.events_cut)) + \
               '\nlen(events_final)=' + str(len(self.events_final)) + \
               '\nspeed_factor=' + str(self.speed_factor) + \
               '\ncutLeft=' + str(self.cutLeft) + \
               '\ncutRight=' + str(self.cutRight) + ')'



    def prepareForPlaying(self):
        print('prepareForPlaying')
        self.cutRecording()

    def cutRecording(self):
        print( 'cutRecording' )
        self.events_cut = []
        if self.cutLeft > 0:
            print( 'RecordingEventCutLeft' )
            for i in range( len(self.events) ):
                if self.events[i].time > self.events[0].time + self.cutLeft:
                    self.events_cut = self.events[i:]
                    break
        else:
            self.events_cut = self.events

        if self.cutRight > 0:
            print('RecordingEventCutRight')
            for i in reversed(range(len(self.events_cut))):
                if i == 0:
                    self.events_cut = []
                elif self.events_cut[i].time < self.events_cut[-1].time - self.cutRight:
                    self.events_cut = self.events_cut[:i]
                    break
        self.excludeExcludedEvents()

    def excludeExcludedEvents(self):
        print('excludeExcludedEvents')
        if self.events_cut != []:
            if self.events_cut[0].time != 0:
                self.events_final = []
                t0 = 0
                for event in self.events_cut:

                    if isinstance( event, MoveEvent ):
                        if self.include_moves:
                            if t0 == 0:
                                t0 = float(event.time)
                            move = MoveEventV2( x=event.x, y=event.y, time=float(event.time - t0) )
                            self.events_final.append( move )

                    elif isinstance( event, MoveEventV2 ):
                        if self.include_moves:
                            if t0 == 0:
                                t0 = float(event.time)
                            copied_event = deepcopy( event )
                            copied_event.time -= t0
                            self.events_final.append( copied_event )

                    elif isinstance( event, ButtonEvent ):
                        if self.include_clicks:
                            if t0 == 0:
                                t0 = float(event.time)
                            button = ButtonEventV2( event_type=event.event_type, button=event.button, play_at=float(event.time - t0) )
                            self.events_final.append( button )

                    elif isinstance( event, ButtonEventV2 ):
                        if self.include_clicks:
                            if t0 == 0:
                                t0 = float(event.time)
                            copied_event = deepcopy( event )
                            copied_event.time -= t0
                            self.events_final.append( copied_event )

                    elif isinstance( event, WheelEvent ):
                        if self.include_wheel:
                            if t0 == 0:
                                t0 = float(event.time)
                            wheel = WheelEventV2( delta=event.delta, time=float(event.time - t0) )
                            self.events_final.append( wheel )

                    elif isinstance( event, WheelEventV2 ):
                        if self.include_wheel:
                            if t0 == 0:
                                t0 = float(event.time)
                            copied_event = deepcopy( event )
                            copied_event.time -= t0
                            self.events_final.append( copied_event )

                    elif isinstance( event, KeyboardEvent ):
                        if self.include_keyboard:
                            if t0 == 0:
                                t0 = float(event.time)
                            # event.time = float(event.time - t0)
                            self.events_final.append( deepcopy(event) )
                            self.events_final[-1].time -= t0
                    else:
                        print( 'Nieznany typ eventu!' )


class MoveEventV2:
    def __init__(self, x, y, time, duration=0, absolute=True ):
        self.event_type = 'MoveEvent'
        self.x = x
        self.y = y
        self.time = time
        self.duration = duration
        self.absolute = absolute

    def __str__(self):
        return 'MoveEventV2(x=' + str(self.x) + ', y=' + str(self.y) + ', time=' + str(self.time) + ', duration=' + str(self.duration) + ', absolute=' + str(self.absolute) + ')'


class ButtonEventV2:
    def __init__(self, event_type, button, play_at ):
        self.event_type = event_type
        self.button = button
        self.time = play_at

    def __str__(self):
        return 'ButtonEventV2(event_type=' + str(self.event_type) + ', button=' + str(self.button) + ', time=' + str(self.time) + ')'


class WheelEventV2:
    def __init__(self, delta, time):
        self.event_type = 'WheelEvent'
        self.delta = delta
        self.time = time

    def __str__(self):
        return 'WheelEvent(event_type=' + str(self.event_type) + ', delta=' + str(self.delta) + ', time=' + str(self.time) + ')'


class MacroEditorItem(QStandardItem):  # MEI
    def __init__(self, action, text='' ):
        super().__init__(text=text)
        self.action = action
        self.setText(text)
        self.setEditable(False)

    def __str__(self):
        return 'MEI(' + str(self.action) + ', ' + self.text() + ')'

    def __reduce__(self):
        return (self.__class__, ( self.action, self.text() ) )


class PlaceholderEvent:
    def __init__(self, time=0):
        self.event_type = 'PlaceholderEvent'
        self.time = time

    def __str__(self):
        return str(self.event_type)


class ForEvent:
    def __init__(self, event_list=None, times=1, time=0):
        if event_list is None:
            event_list = [MacroEditorItem(PlaceholderEvent(), 'Początek pętli')]
        self.event_type = 'ForEvent'
        self.event_list = event_list
        self.times = times  # How many times to play event_list
        self.time = time  # what time to start at

    def __str__(self):
        printed_string = 'ForEvent['
        for event in self.event_list:
            printed_string += str(event) + ', '
        return printed_string + ']'

    def ensurePlaceholder(self):
        if not isinstance( self.event_list[0].action[0], PlaceholderEvent ):
            self.event_list.insert(0, MacroEditorItem(PlaceholderEvent(), 'Początek pętli'))


class WaitEvent:
    def __init__(self, event_type, target_button='left', triggering_event='down', suppress=False, time=0, wait_time=0 ):
        self.event_type = event_type
        self.target_button = target_button
        self.triggering_event = triggering_event
        self.suppress = suppress
        self.time = time
        self.wait_time = wait_time

    def __str__(self):
        if self.event_type == 'mouse':
            return 'WaitEvent(event_type=' + str(self.event_type) + ', target_button=' + str(self.target_button) + ', triggering_event=' + str( self.triggering_event ) + ')'
        elif self.event_type == 'keyboard':
            return 'WaitEvent(event_type=' + str(self.event_type) + ', target_button=' + str(self.target_button) + ', suppress=' + str(self.suppress) + ')'
        else:
            return 'WaitEvent(event_type=' + str(self.event_type) + ', time=' + str(self.time) + ')'


class MacroTreeviewItem(QStandardItem):  # MTvI
    def __init__(self, macro_editor_items_list, name, item_duration, item_hotkey, item_speed, speed_factor=1.0, hotkey='' ):
        super().__init__(name)
        self.setCheckable( True )
        self.setCheckState( Qt.Checked )
        self.active = self.checkState()
        self.macro_editor_items_list = macro_editor_items_list
        self.itemDuration = item_duration
        self.itemHotkey = item_hotkey
        self.itemSpeed = item_speed
        self.widgetHotkey = None
        self.widgetSpeedFactor = None
        self.speed_factor = speed_factor
        self.hotkey = hotkey

        self.macroThread = None
        self.macroAbortEvent = threading.Event()
        self.isMacroRunning = False
        self.updateCheckState( self.active )

    def updateCheckState(self, checked):
        print( 'updateCheckState, state=', checked )
        if checked == Qt.Checked:
            self.active = Qt.Checked
            self.setCheckState( Qt.Checked )
        else:
            self.active = Qt.Unchecked
            self.setCheckState( Qt.Unchecked )

    def updateSpeedFactor(self, speed_factor ):
        print( self.text() + '.updateSpeedFactor', speed_factor )
        self.speed_factor = speed_factor

    def updateKeySequence(self, key_sequence, just_loaded=False ):
        if not just_loaded:
            if key_sequence != '':
                print( "MTI_KeySequence:", self.text(), key_sequence )
                if self.hotkey != '':
                    keyboard.remove_hotkey(self.macroPrep)
                keyboard.add_hotkey(key_sequence, self.macroPrep)
                self.hotkey = key_sequence
            else:
                print("MTI_HotkeyChange", self.text(), " ' ''", key_sequence)
                if self.hotkey != '':
                    keyboard.remove_hotkey(self.hotkey)
                self.hotkey = key_sequence
        else:
            if key_sequence != '':
                self.hotkey = key_sequence
                keyboard.add_hotkey( key_sequence, self.macroPrep )
            else:
                self.hotkey = key_sequence

    def macroPrep(self):
        if not self.isMacroRunning:
            self.isMacroRunning = True
            self.macroThread = threading.Thread(target=self.macroStart)
            self.macroThread.start()
        else:
            self.macroStop()

    def macroStart(self):
        begin = time.time()
        self.macroAbortEvent = threading.Event()
        x = self.macroPlay( self.macro_editor_items_list, self.speed_factor )
        if isinstance( x, str ):
            print( 'Macro aborted.' )
        self.isMacroRunning = False
        print( 'total duration:', time.time() - begin )

    def macroStop(self):
        print( 'macroStop' )
        self.isMacroRunning = False
        self.macroAbortEvent.set()

    def macroPlay( self, target, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        timedelta = time.time()
        state = keyboard.stash_state()
        # recording_events_time = 0
        wait_events_duration = 0
        for_events_duration = 0
        t0 = time.time()
        last_time = 0

        for item in target:
            event = item.action
            if speed_factor > 0:  # temporal stuff
                theoretical_wait_time = (event.time - last_time) / speed_factor
                target_time = t0 + wait_events_duration + for_events_duration + theoretical_wait_time
                real_wait_time = target_time - time.time()
                # print( 'theory:', theoretical_wait_time, ' reality:', real_wait_time, ' total:', event.time )
                if real_wait_time > 0:
                    if self.macroAbortEvent.wait(timeout=real_wait_time):
                        keyboard.stash_state()
                        return 'abort'
                # recording_events_time = 0
                t0 += theoretical_wait_time
                last_time = event.time

            if isinstance(event, (MoveEventV2, MoveEvent)) and include_moves:
                mouse.move(event.x, event.y, absolute=event.absolute, duration=event.duration)
            elif isinstance(event, (ButtonEventV2, ButtonEvent)) and include_clicks:
                if event.event_type == mouse.UP:
                    mouse.release(event.button)
                elif event.event_type == mouse.DOWN:
                    mouse.press(event.button)
                elif event.event_type == 'double':  # do testu
                    mouse.double_click(event.button)  #
                elif event.event_type == 'click':  # do testu
                    mouse.click(event.button)  #
                else:
                    print('Nieznany typ eventu myszy')
            elif isinstance(event, KeyboardEvent) and include_keyboard:
                key = event.name or event.scan_code
                if event.event_type == keyboard.KEY_DOWN:
                    keyboard.press(key)
                elif event.event_type == keyboard.KEY_UP:
                    keyboard.release(key)
                elif event.event_type == 'write':
                    writeGoodEnough(event.scan_code)  # do testu musi być nadpisany tekstem!
                elif event.event_type == 'click':
                    keyboard.press_and_release(key)
                elif event.event_type == 'hotkey':
                    keyboard.send(key)  # do testu
                elif event.event_type == 'releaseall':
                    keyboard.stash_state()  # do testu
                else:
                    print('Nieznany typ eventu klawiatury')
            elif isinstance(event, (WheelEvent, WheelEventV2)) and include_wheel:
                mouse.wheel(event.delta)
            elif isinstance(event, WaitEvent):
                if event.event_type == 'mouse':
                    before = time.time()
                    mouse.wait(event.target_button)
                    wait_events_duration += time.time() - before
                elif event.event_type == 'keyboard':
                    before = time.time()
                    keyboard.wait(event.target_button, suppress=event.suppress)
                    wait_events_duration += time.time() - before
                elif event.event_type == 'nseconds':
                    pass  # waiting for this event is handled in the beginning of the loop
                else:
                    print('Nieznany typ eventu oczekiwania')
            elif isinstance(event, RecordingEvent):
                x = self.playRecording(event.events_final, event.speed_factor * speed_factor, event.include_clicks, event.include_moves, event.include_wheel, event.include_keyboard)
                if isinstance( x, str ):
                    return 'abort'

            elif isinstance(event, ForEvent):  # PSUJE CZASY? CHYBA NIE, DO TESTU
                before = time.time()
                for i in range(event.times):
                    x = self.macroPlay(event.event_list, speed_factor, include_clicks, include_moves, include_wheel, include_keyboard)
                    if isinstance( x, str ):
                        return 'abort'
                    time.sleep(0.0025/speed_factor)           # PAMIĘTAJ O TYM, JEŚLI CZAS PRZESTANIE SIĘ ZGADZAC
                for_events_duration += time.time() - before
            elif isinstance(event, PlaceholderEvent):
                pass
            else:
                print('Nieznany typ eventu', event)
        keyboard.restore_modifiers(state)
        keyboard.release(self.hotkey)

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
        keyboard.restore_modifiers(state)
        keyboard.release(self.hotkey)
        # print(time.time() - timedelta)
        print("MTI_playRecording")
        return time.time() - timedelta

    def __str__(self):
        return "MTI(checkState=" + str(bool(self.checkState())) + \
               ', active=' + str(self.active) + \
               ', isCheckable=' + str(bool(self.isCheckable())) + \
               ', itemDuration=' + str(self.itemDuration) + \
               ', itemHotkey=' + str(self.itemHotkey) + \
               ', itemSpeed=' + str(self.itemSpeed) + \
               ', widgetHotkey=' + str(self.widgetHotkey) + \
               ', widgetSpeedFactor=' + str(self.widgetSpeedFactor) + \
               ', speed_factor=' + str(self.speed_factor) + \
               ', hotkey=' + str(self.hotkey) + ')\nMTI list' + str([ str(event) for event in self.macro_editor_items_list ])

    def __reduce__(self):
        return (self.__class__, ( self.macro_editor_items_list, self.text(), None, None, None, self.speed_factor, self.hotkey ) )


class SingleKeySequenceEdit(QKeySequenceEdit):
    def __init__(self, parent=None):
        super(SingleKeySequenceEdit, self).__init__(parent)

    def keyPressEvent(self, QKeyEvent):
        super(SingleKeySequenceEdit, self).keyPressEvent(QKeyEvent)
        value = self.keySequence()
        self.setKeySequence(QKeySequence(value))
        self.keySequenceChanged.emit(value)
        self.editingFinished.emit()


def writeGoodEnough(text, delay=0, restore_state_after=True):
    # Moja wersja keyboard.write. Autor znowu nie przetestował dobrze swojej biblioteki (kompatybilna prawdopodobnie tylko z windowsem)
    # Przy delay < 0.00125 program (u mnie) kończy wysyłać sygnały do buforu klawiatury szybciej,
    # niż są one wypisywane (przepełnienie buforu przy długim tekście, desynchronizacja czasu w makro)
    state = keyboard.stash_state()
    if delay < 0.00125:
        delay = 0.00125

    for letter in text:
        if letter in '\n\b':
            keyboard.send(letter)
            time.sleep(delay)
        else:
            keyboard._os_keyboard.type_unicode(letter)
            time.sleep(delay)

    if restore_state_after:
        keyboard.restore_modifiers(state)

from copy import deepcopy
from keyboard import KeyboardEvent
from mouse import ButtonEvent, WheelEvent, MoveEvent
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem


class RecordingEvent:
    def __init__(self, name='', events=[], speed_factor=1.0, cut_left=0, cut_right=0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True, events_final=[], time=0):
        self.event_type = 'RecordingEvent'
        self.name = name
        self.events = events
        self.events_final = events_final
        self.speed_factor = speed_factor
        self.cutLeft = cut_left
        self.cutRight = cut_right
        self.include_clicks = include_clicks
        self.include_moves = include_moves
        self.include_wheel = include_wheel
        self.include_keyboard = include_keyboard
        self.time = time

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
                self.events_final = edited_events


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
        return 'MEI(' + str(self.action) + ')'


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
    def __init__(self, macro_editor_items_list, name, item_duration, item_hotkey, item_speed, speed_factor=1.0 ):
        super().__init__(name)
        self.setCheckable( True )
        self.setCheckState( Qt.Checked )
        self.macro_editor_items_list = macro_editor_items_list
        self.itemDuration = item_duration
        self.itemHotkey = item_hotkey
        self.itemSpeed = item_speed
        self.speed_factor = speed_factor
        self.widgetHotkey = None
        self.widgetSpeedFactor = None
        self.hotkey = None

    def setConnections(self):
        print( 'Przed podlaczeniem' )
        self.widgetHotkey.keySequenceChanged.connect( self.hotkeyChanged )
        print( 'Po podlaczeniu' )
        # item.widgetHotkey.keySequenceChanged.connect( item.hotkeyChanged )
    def changes(self):
        print( 'Coś się zmieniło!')

    def hotkeyChanged(self):
        print( self.widgetHotkey.keySequence() )

    def speedFactorChanged(self, speed_factor):
        print( speed_factor )

    def updateSpeedFactor(self, speed_factor ):
        self.speed_factor = speed_factor

    def updateKeySequence(self, key_sequence ):  # Potrzebne do oszukania connect w Qt
        self.hotkey = key_sequence

    def __str__(self):
        return "MTI(hotkey=" + str(self.hotkey) + ', speed_factor=' + str(self.speed_factor) + ')'

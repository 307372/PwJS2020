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
import _settings
import _editorOpeningAndSaving
from _classes import RecordingEvent, MoveEventV2, ButtonEventV2, WheelEventV2, MacroEditorItem, PlaceholderEvent, ForEvent, WaitEvent
from collections import namedtuple

from PySide2.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QTreeWidgetItem
from PySide2.QtCore import QSignalBlocker, QRegularExpression
from PySide2.QtGui import QStandardItemModel, QStandardItem, QKeySequence
from ui_GUI import Ui_MainWindow
from recording_GUI import Ui_Dialog


class MainWindow(QMainWindow, _autoclicker.AutoclickerMethods, _record.RecordMethods, _settings.SettingsMethods, _editorOpeningAndSaving.OpeningAndSaving):
    def __init__( self ):
        super( MainWindow, self ).__init__()  # Calling parent constructor
        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )

        # AC = autoclicker
        if True:
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

        self.macroElements = []
        self.currentlyEditedItem = None
        self.treeModel = QStandardItemModel()
        self.rootNode = self.treeModel.invisibleRootItem()
        self.treeModel.setColumnCount(2)
        # self.ui.creatorEditorTreeView.select
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

        # Connects
        if True:
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
            self.recordDialog.save.clicked.connect( self.saveEditedItem )

            self.ui.creatorEditorDeleteFromActions.clicked.connect(self.creatorEditorDelete)
            # self.ui.creatorEditorEdit.clicked.connect(self.creatorRecordOpenInEditor)  # DO POłĄCZENIA Z self.creatorSelectEditorPageBySelectedAction !
            self.ui.creatorEditorAddToMacro.clicked.connect(self.creatorAddActionToMacro)
            self.ui.creatorEditorDeleteFromMacro.clicked.connect(self.creatorRemoveActionFromMacro)
            self.ui.creatorEditorEdit.clicked.connect( self.creatorOpenSelectedInEditor )
            self.ui.previewButton.clicked.connect( self.previewMacro )
            # self.ui.creatorEditorTreeView.setSelection()


            # Test functions
            self.ui.testSaveButton.clicked.connect( self.pickleRecordings )
            self.ui.testLoadButton.clicked.connect( self.unpickleRecordings )
            self.ui.testButton.clicked.connect( self.creatorEditorTreeViewUpdate )
            self.ui.testButton_2.clicked.connect( self.macroUpdateTime )
            self.ui.testButton_3.clicked.connect( self.testowa )

            self.ui.WhatIsThisButton.clicked.connect( self.inspectThis )



        # settings
        self.ui.settingsDefault.clicked.connect( self.settingsDefaultConfirmation )
        self.ui.forceSave.clicked.connect( lambda: self.saveAllSettings(destination='settings.dat', forced=True) )
        self.ui.forceLoad.clicked.connect( lambda: self.loadAllSettings(destination='settings.dat') )

        self.unpickleRecordings()

    def testowa(self):
        print( 'test' )


    def creatorEditorDelete(self):
        print( 'creatorEditorDelete' )
        # print( self.ui.creatorEditorActions.indexFromItem(self.ui.creatorEditorActions.selectedItems()[0], 0 ).parent().row() )
        if self.ui.creatorEditorActions.indexFromItem(self.ui.creatorEditorActions.selectedItems()[0], 0 ).parent().row() == 3:  # Upewniamy się, że kasujemy z zakładki "nagrane"
            self.recordsDict.pop( self.ui.creatorEditorActions.selectedItems()[0].text(0), None )
            self.ui.creatorEditorActions.topLevelItem(3).removeChild(self.ui.creatorEditorActions.selectedItems()[0])

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
        if not self.ui.creatorEditorActions.selectedItems() == []:  # if some action in the action list is selected
            item_name = self.ui.creatorEditorActions.selectedItems()[0].text(0)
            item = None
            is_name_known = True
            if 'Przemieść kursor' == item_name:
                item = MoveEventV2(0, 0, 0)
            elif 'Ruch kółka myszy' == item_name:
                item = WheelEventV2(1, 0)
            elif 'Puść przycisk myszy' == item_name:
                item = ButtonEventV2(mouse.UP, mouse.LEFT, 0)
            elif 'Przytrzymaj przycisk myszy' == item_name:
                item = ButtonEventV2(mouse.DOWN, mouse.LEFT, 0)
            elif 'Kliknięcie' == item_name:
                item = ButtonEventV2('click', mouse.LEFT, 0)
            elif 'Podwójne kliknięcie' == item_name:
                item = ButtonEventV2(mouse.DOUBLE, mouse.LEFT, 0)
            elif 'Użyj skrótu klawiszowego' == item_name:
                item = KeyboardEvent('hotkey', 0, time=0)
            elif 'Kliknij klawisz' == item_name:
                item = KeyboardEvent('click', 0, time=0)
            elif 'Przytrzymaj klawisz' == item_name:
                item = KeyboardEvent(keyboard.KEY_DOWN, 0, time=0)
            elif 'Puść klawisz' == item_name:
                item = KeyboardEvent(keyboard.KEY_UP, 0, time=0)
            elif 'Wypisz tekst' == item_name:
                item = KeyboardEvent('write', 0, time=0)
            elif "Puść wszystkie klawisze" == item_name:
                item = KeyboardEvent('releaseall', 0, time=0)
            elif "Czekaj na akcję myszy" == item_name:
                item = WaitEvent('mouse', 'left', 'down' )
            elif "Czekaj na akcję klawiatury" == item_name:
                item = WaitEvent('keyboard', 0, 0)
            elif "Czekaj N sekund" == item_name:
                item = WaitEvent('nseconds', '')
            elif "Wykonaj N razy" == item_name:
                item = ForEvent()  # lambda: random.randint(0, 2000000000)),
            elif "Początek pętli" == item_name:
                item = PlaceholderEvent()
            elif item_name in self.recordsDict.keys():
                print( item_name, self.recordsDict[item_name] )
                item = deepcopy( self.recordsDict[item_name] )
                item.setT0to0()
            else:
                is_name_known = False
                print( 'Nieznana nazwa' )
            item = MacroEditorItem(item, item_name)

            print( 'creatorAddActionToMacro -', item_name )
            if self.ui.creatorEditorTreeView.selectedIndexes() == [] and is_name_known:   # if no action in the macro is selected
                self.rootNode.appendRow( item )
                self.macroElements.append( item )  # Dodawanie elementu do listy poleceń makra
                if item_name == "Wykonaj N razy":
                    item_name = "Początek pętli"
                    item.appendRow([MacroEditorItem(PlaceholderEvent(), item_name), QStandardItem()])
                    self.ui.creatorEditorTreeView.setExpanded( item.index(), True )
            elif is_name_known:
                print( self.ui.creatorEditorTreeView.selectedIndexes()[0].parent() )
                parent_index = self.ui.creatorEditorTreeView.selectedIndexes()[0].parent()
                if not parent_index.isValid():    # if item is from top level of the tree
                    print( 'invalid', parent_index )
                    index = self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1
                    self.rootNode.insertRow( index, item )  # z jakiegoś powodu zamiast rzeczy w zmiennej item, wstawia QStandardItem()
                    self.rootNode.setChild( index, item )   # dlatego w tej linijce to nadpisujemy moim itemem i działa
                    self.macroElements.insert( index, item )  # Dodawanie elementu do listy poleceń makra
                    if item_name == "Wykonaj N razy":
                        item_name = "Początek pętli"
                        item.appendRow([MacroEditorItem(PlaceholderEvent(), item_name), QStandardItem()])
                        self.ui.creatorEditorTreeView.setExpanded( item.index(), True )
                else:  # if item in not from top level of the tree
                    print( 'parent_index', parent_index )
                    print(  'item from parent_index', self.treeModel.itemFromIndex(parent_index) )
                    print( 'valid', self.treeModel.itemFromIndex(parent_index).text() )
                    item_index = self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1
                    self.treeModel.itemFromIndex( parent_index ).insertRow( item_index, item )
                    self.treeModel.itemFromIndex( parent_index ).setChild( item_index, item )
                    self.treeModel.itemFromIndex( parent_index ).action.event_list.insert( item_index, item )  # Dodawanie elementu do listy poleceń makra
                    print('valid', self.treeModel.itemFromIndex( parent_index ).action.event_list )
                    # print( self.macroElements[0].action.event_list )
                    print( self.treeModel.itemFromIndex( parent_index ).action.event_list )
                    if item_name == "Wykonaj N razy":
                        item_name = "Początek pętli"
                        item.appendRow([MacroEditorItem(PlaceholderEvent(), item_name), QStandardItem()])
                        self.ui.creatorEditorTreeView.setExpanded( item.index(), True )

    def creatorRemoveActionFromMacro(self):
        if not self.ui.creatorEditorTreeView.selectedIndexes() == []:  # if some action in the macro is selected
            items = self.ui.creatorEditorTreeView.selectedIndexes()
            print( 'creatorRemoveActionFromMacro -', items )
            row = items[0].row()
            parent_index = items[0].parent()
            if not parent_index.isValid():  # if item is from top level of the tree
                print( 'index invalid!' )
                del self.macroElements[row]
                self.rootNode.removeRow( row )
            else:  # if item in not from top level of the tree
                print('row =', row)
                print( self.treeModel.itemFromIndex( parent_index ).action.event_list )
                print( self.treeModel.itemFromIndex( parent_index ).action.event_list[row] )
                del self.treeModel.itemFromIndex( parent_index ).action.event_list[row]
                self.treeModel.itemFromIndex( parent_index ).removeRow(row)

    def creatorSelectEditorPageByID(self, page_id):
        self.recordDialog.pages.setCurrentIndex( page_id )

    def inspectThis(self):
        # print( self.macroElements )
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()
        print( self.treeModel.itemFromIndex(indexes[0]) )
        self.showMacroStructure()
        # print( 'indexes', indexes )
        # print( 'data 0:', indexes[0].data() )
        # print( self.treeModel.itemFromIndex( indexes[0].parent() ).action.event_list )

        # list = self.treeModel.itemFromIndex( indexes[0].parent() ).action.event_list
        # print( '[ ', end='' )
        # for element in list:
        #     print( type(element.action).__name__, ', ', sep='', end='' )
        # print( ' ]' )
        # print( 'data 1:', indexes[1].data() )

    def showMacroStructure(self):
        string = '['
        for element in self.macroElements:
            string += str(element) + ', '
        print(string + ']')

    def creatorEditorTreeViewClear(self):
        self.treeModel.clear()

    def macroUpdateTime(self):
        self.updateTime( self.macroElements )

    def updateTime(self, events, indentation=''):
        for i in range( len(events) ):
            if i == 0:
                events[i].action.time = 0
            elif events[i].action.event_type in ['nseconds', 'keyboard', 'mouse']:
                events[i].action.time = events[i-1].action.time  # it's checked if i==0 first, so it's safe
            else:
                # print(events[i].action.event_type, 'not in ["wait", "keyboard", "mouse"]')
                events[i].action.time = events[i-1].action.time + 0.1  # 100ms
            print( indentation, events[i].action.time, events[i].action )

            if isinstance( events[i-1].action, MoveEventV2 ):
                events[i].action.time += events[i-1].action.duration
            elif events[i-1].action.event_type == 'nseconds':
                events[i].action.time += events[i-1].action.wait_time

            if isinstance( events[i].action, ForEvent ):
                self.updateTime( events[i].action.event_list, indentation + '   ' )




    def previewMacro(self):
        self.macroPlay( self.macroElements )

    def macroPlay( self, target, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
        timedelta = time.time()
        self.macroThread = threading.Event()
        state = keyboard.stash_state()
        wait_events_duration = 0
        for_events_duration = 0
        t0 = time.time()
        last_time = 0

        for item in target:
            event = item.action
            if speed_factor > 0:
                theoretical_wait_time = (event.time - last_time) / speed_factor
                target_time = t0 + wait_events_duration + for_events_duration + theoretical_wait_time
                real_wait_time = target_time - time.time()
                if real_wait_time > 0:
                    if self.macroThread.wait(timeout=real_wait_time):
                        break
                t0 += theoretical_wait_time
                last_time = event.time
            if isinstance(event, (MoveEventV2, MoveEvent)) and include_moves:
                mouse.move(event.x, event.y, absolute=event.absolute, duration=event.duration )
            elif isinstance(event, (ButtonEventV2, ButtonEvent)) and include_clicks:
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
                elif event.event_type == 'click':
                    keyboard.press_and_release(key)
                elif event.event_type == 'hotkey':
                    keyboard.send(key)   # do testu
                elif event.event_type == 'releaseall':
                    keyboard.stash_state()           # do testu
                else:
                    print('Nieznany typ eventu klawiatury')
            elif isinstance(event, (WheelEvent, WheelEventV2)) and include_wheel:
                mouse.wheel(event.delta)
            elif isinstance( event, WaitEvent ):
                if event.event_type == 'mouse':
                    before = time.time()
                    mouse.wait( event.target_button )
                    wait_events_duration += time.time() - before
                elif event.event_type == 'keyboard':
                    before = time.time()
                    keyboard.wait( event.target_button, suppress=event.suppress )
                    wait_events_duration += time.time() - before
                elif event.event_type == 'nseconds':
                    time.sleep( event.wait_time )
                else:
                    print( 'Nieznany typ eventu oczekiwania' )
            elif isinstance( event, RecordingEvent ):
                begin = time.time()
                print( event.speed_factor )
                print( event.events_final )
                self.playRecording( event.events_final, event.speed_factor, event.include_clicks, event.include_moves, event.include_wheel, event.include_keyboard )
                for_events_duration += time.time() - begin

            elif isinstance( event, ForEvent ):   # PSUJE CZASY? CHYBA NIE, DO TESTU
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
        print("macroPlay")


app = QApplication( sys.argv )

window = MainWindow()
window.show()

sys.exit(app.exec_())

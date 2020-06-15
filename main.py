import sys
import os
import threading
from copy import deepcopy
import pickle
import random
from math import floor
from keyboard import KeyboardEvent
import keyboard
# import psutil
from win32ui import FindWindow, error
from configparser import ConfigParser
import time
from mouse import ButtonEvent, WheelEvent, MoveEvent
import mouse
import _autoclicker
import _record
import _settings
import _editorOpeningAndSaving
from _classes import RecordingEvent, MoveEventV2, ButtonEventV2, WheelEventV2, MacroEditorItem, PlaceholderEvent, ForEvent, WaitEvent, MacroTreeviewItem, SingleKeySequenceEdit
from collections import namedtuple

from PySide2.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QTreeWidgetItem, QDoubleSpinBox, QPushButton, QKeySequenceEdit
from PySide2.QtCore import QSignalBlocker, QRegularExpression, Qt, QRect, QModelIndex, QItemSelectionRange, QItemSelection, QCoreApplication
from PySide2.QtGui import QStandardItemModel, QStandardItem, QKeySequence, QCloseEvent
from ui_GUI import Ui_MainWindow
from recording_GUI import Ui_Dialog

# 85 metod łącznie 30.05.2020


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


class MainWindow(QMainWindow, _autoclicker.AutoclickerMethods, _record.RecordMethods, _settings.SettingsMethods, _editorOpeningAndSaving.OpeningAndSaving):
    def __init__( self ):
        self.checkIfProgramIsAlreadyRunning()
        super( MainWindow, self ).__init__()  # Calling parent constructor

        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )

        # AC = autoclicker
        if True:
            # AC Mouse
            self.ui.AC_Hotkey = SingleKeySequenceEdit(parent=self.ui.groupBox)
            self.ui.AC_Hotkey.setObjectName(u"AC_Hotkey")
            self.ui.AC_Hotkey.setGeometry(QRect(20, 110, 113, 20))
            self.ui.verticalLayout.insertWidget( 5, self.ui.AC_Hotkey )
            self.ui.AC_Hotkey.keySequenceChanged.connect( self.AC_HotkeyChange )

            self.ui.AC_Hotkey.editingFinished.connect(self.AC_HotkeyChange)
            self.AC_Hotkey = self.ui.AC_Hotkey.keySequence().toString()
            # print(self.ui.AC_Hotkey.keySequence().toString())
            if self.ui.AC_Hotkey.keySequence().toString() != '':
                keyboard.add_hotkey(self.ui.AC_Hotkey.keySequence().toString(), self.AC_Toggle)

            self.ui.AC_Start.clicked.connect(self.AC_StartPrep)
            self.ui.AC_Stop.clicked.connect(self.AC_Stop)
            self.isACRunning = False
            self.AC_Thread = threading.Event()
            self.AC_MouseButton = ''
            self.AC_MouseButtonUpdate()
            self.ui.AC_WhichButton.currentTextChanged.connect(self.AC_MouseButtonUpdate)

            # AC Keyboard

            self.ui.AC_KeyboardKeySequence = SingleKeySequenceEdit(self.ui.AC_KeyboardOptions)
            self.ui.AC_KeyboardKeySequence.setObjectName(u"AC_KeyboardKeySequence")
            self.ui.verticalLayout_2.insertWidget( 2, self.ui.AC_KeyboardKeySequence)

            self.ui.AC_KeyboardHotkey = SingleKeySequenceEdit(self.ui.AC_KeyboardOptions)
            self.ui.AC_KeyboardHotkey.setObjectName(u"AC_KeyboardHotkey")
            self.ui.verticalLayout_2.insertWidget( 5, self.ui.AC_KeyboardHotkey)

            self.ui.AC_KeyboardStart.clicked.connect(self.AC_KeyboardStartPrep)
            self.ui.AC_KeyboardStop.clicked.connect(self.AC_KeyboardStop)
            self.isACKeyboardRunning = False
            self.AC_KeyboardThread = threading.Event()
            self.AC_KeyboardHotkey = ''
            self.ui.AC_KeyboardHotkey.editingFinished.connect(self.AC_KeyboardHotkeyChange)



        # creator
        self.dialog = QDialog()
        self.recordDialog = Ui_Dialog()
        self.recordDialog.setupUi(self.dialog)
        # dialog stuff
        if True:
            self.recordDialog.keyboardButtonSelection = SingleKeySequenceEdit( self.recordDialog.keyboardButtonGB )
            self.recordDialog.keyboardButtonSelection.setObjectName(u"keyboardButtonSelection")
            self.recordDialog.keyboardButtonSelection.setGeometry(QRect(30, 70, 113, 20))

            self.recordDialog.recordingHotkey = SingleKeySequenceEdit(self.recordDialog.hotkeys)
            self.recordDialog.recordingHotkey.setObjectName(u"recordingHotkey")
            self.recordDialog.verticalLayout_2.insertWidget( 1, self.recordDialog.recordingHotkey )

            self.recordDialog.previewHotkey = SingleKeySequenceEdit(self.recordDialog.hotkeys)
            self.recordDialog.previewHotkey.setObjectName(u"previewHotkey")
            self.recordDialog.verticalLayout_2.insertWidget( 3, self.recordDialog.previewHotkey )

            self.recordDialog.waitKeyboardHotkey = SingleKeySequenceEdit(self.recordDialog.waitKeyboardGB)
            self.recordDialog.waitKeyboardHotkey.setObjectName(u"waitKeyboardHotkey")
            self.recordDialog.waitKeyboardHotkey.setGeometry(QRect(110, 80, 113, 20))

        # validator = QRegularExpression("[_]*")        # Ma nieprzyjmować podkreślników!
        # self.recordDialog.name.setValidator()
        self.recordedInObject = None
        self.recordedObject = None
        self.recorded = []
        self.recordedCut = []
        self.recordedFinal = []
        self.recordsDict = {}
        self.isDialogOpen = False


        self.macroElementNametags = {
            'MoveEvent': 'Przemieść kursor',
            'WheelEvent': 'Ruch kółka myszy',
            'ButtonEventup': 'Puść przycisk myszy',
            'ButtonEventdown': 'Przytrzymaj przycisk myszy',
            'ButtonEventclick': 'Kliknięcie',
            'ButtonEventdouble': 'Podwójne kliknięcie',
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
        self.macroTotalTime = 0
        self.currentlyEditedItem = None
        self.treeModel = QStandardItemModel()
        self.rootNode = self.treeModel.invisibleRootItem()
        self.treeModel.setColumnCount(2)
        # self.ui.creatorEditorTreeView.select
        self.ui.creatorEditorTreeView.setModel(self.treeModel)
        self.ui.creatorEditorTreeView.setColumnWidth(0, 355)
        self.ui.creatorEditorTreeView.setColumnWidth(1, 100)
        self.treeModel.setHeaderData(0, Qt.Horizontal, 'Nazwa czynności')
        self.treeModel.setHeaderData(1, Qt.Horizontal, 'Czas po wykonaniu')
        self.editorSelectionModel = self.ui.creatorEditorTreeView.selectionModel()
        self.ui.creatorEditorDeleteFromActions.setDisabled(True)
        self.ui.creatorEditorAddToMacro.setDisabled(True)
        self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())

        # Macro manager
        self.macroTreeModel = QStandardItemModel()
        self.macroRootNode = self.macroTreeModel.invisibleRootItem()
        self.macroTreeModel.setColumnCount( 4 )  # Nazwa, Czas trwania, Skrót klawiszowy, Prędkość odtwarzania
        self.macroTreeModel.setHeaderData(0, Qt.Horizontal, 'Nazwa makra')
        self.macroTreeModel.setHeaderData(1, Qt.Horizontal, 'Czas trwania')
        self.macroTreeModel.setHeaderData(2, Qt.Horizontal, 'Skrót klawiszowy')
        self.macroTreeModel.setHeaderData(3, Qt.Horizontal, 'Prędkość')
        self.ui.macroTreeView.setModel( self.macroTreeModel )
        self.ui.macroTreeView.setColumnWidth( 0, 445 )
        self.macroTreeviewItems = []

        self.charactersProhibitedInWindows = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.' ]  # https://en.wikipedia.org/wiki/Filename#In_Windows

        # /\?%*:|"<>.

        self.isRecordingRunning = False
        self.isMacroRunning = False
        self.macroAbortEvent = threading.Event()
        self.macroThread = None
        self.recordedLength = 0

        # settings
        self.execution_time = 0.0001

        self.ui.settingsDefault.clicked.connect( self.settingsDefaultConfirmation )
        self.ui.forceSave.clicked.connect( lambda: self.saveAllSettings(destination='settings.dat', forced=True))
        self.ui.forceLoad.clicked.connect( lambda: self.loadAllSettings(destination='settings.dat'))

        self.ui.abortHotkey = SingleKeySequenceEdit(self.ui.settingsTab)
        self.ui.abortHotkey.setObjectName(u"abortHotkey")
        self.ui.abortHotkey.setGeometry(QRect(610, 30, 113, 20))

        self.abortionHotkey = ''
        self.ui.abortHotkey.editingFinished.connect( self.updateAbortionHotkey )

        self.dialog.closeEvent = self.dialogCloseEvent

        self.loadAllSettings(destination='settings.dat')
        self.unpickleRecordings()
        self.clearEditor()
        self.loadAllMacros()

        self.creatorRecordHotkey = self.recordDialog.recordingHotkey.keySequence().toString()
        if self.creatorRecordHotkey != '':
            keyboard.add_hotkey(self.creatorRecordHotkey, self.creatorRecordToggle)

        self.creatorPreviewHotkey = self.recordDialog.previewHotkey.keySequence().toString()
        if self.creatorPreviewHotkey != '':
            keyboard.add_hotkey(self.creatorPreviewHotkey, self.creatorRecordPreviewToggle)

        # Connects
        if True:
            self.recordDialog.replaySpeed.valueChanged.connect(self.creatorRecordTimeFinalUpdate)
            self.recordDialog.cutSliderLeft.valueChanged.connect(self.creatorRecordLeftSliderSpinBoxSync)
            self.recordDialog.cutTimeLeft.valueChanged.connect(self.creatorRecordLeftSpinBoxSliderSync)
            self.recordDialog.cutSliderRight.valueChanged.connect(self.creatorRecordRightSliderSpinBoxSync)
            self.recordDialog.cutTimeRight.valueChanged.connect(self.creatorRecordRightSpinBoxSliderSync)

            self.recordDialog.recordingHotkey.editingFinished.connect(self.creatorRecordHotkeyChange)
            self.recordDialog.previewHotkey.editingFinished.connect(self.creatorPreviewHotkeyChange)
            self.recordDialog.start.clicked.connect(self.creatorRecordToggle)
            self.recordDialog.preview.clicked.connect(self.creatorRecordPreviewToggle)
            self.recordDialog.addToActions.clicked.connect(self.creatorRecordAddToActions)
            self.recordDialog.save.clicked.connect(self.saveEditedItem)
            self.recordDialog.cancel.clicked.connect( self.closeEditorDialog )

            self.ui.creatorEditorNewRecording.clicked.connect(self.creatorRecordNewRecording)
            self.ui.creatorEditorSave.clicked.connect(self.saveMacroFromEditorToMacroTree)
            self.ui.macroDelete.clicked.connect(self.deleteSelectedMacro)
            self.ui.creatorEditorMoveUp.clicked.connect(self.creatorMoveSelectedActionUp)
            self.ui.creatorEditorMoveDown.clicked.connect(self.creatorMoveSelectedActionDown)
            self.ui.creatorEditorDeleteFromActions.clicked.connect(self.creatorEditorDelete)

            self.ui.creatorEditorAddToMacro.clicked.connect(self.creatorAddActionToMacro)
            self.ui.creatorEditorDeleteFromMacro.clicked.connect(self.creatorRemoveActionFromMacro)

            self.ui.previewButton.clicked.connect(self.previewMacro)

            self.ui.creatorEditorClear.clicked.connect(self.clearEditor)
            self.ui.macroNew.clicked.connect(self.openEmptyEditor)
            self.ui.macroEdit.clicked.connect(self.openSelectedMacroInEditor)
            self.ui.creatorEditorActions.itemSelectionChanged.connect( self.actionsWhatIsSelected )
            self.ui.creatorEditorName.textChanged.connect( lambda: self.ui.creatorEditorSave.setDisabled( self.checkIfSavingIsPossible() ) )

            # autosaves
            self.ui.abortHotkey.editingFinished.connect(self.autosave)
            self.recordDialog.previewHotkey.editingFinished.connect(self.autosave)
            self.recordDialog.recordingHotkey.editingFinished.connect(self.autosave)

            self.ui.AC_Hours.valueChanged.connect(self.autosave)
            self.ui.AC_Minutes.valueChanged.connect(self.autosave)
            self.ui.AC_Seconds.valueChanged.connect(self.autosave)
            self.ui.AC_Miliseconds.valueChanged.connect(self.autosave)
            self.ui.AC_WhichButton.currentIndexChanged.connect(self.autosave)
            self.ui.AC_Hotkey.editingFinished.connect(self.autosave)
            self.ui.AC_ClickUntilStopped.clicked.connect(self.autosave)
            self.ui.AC_ClickNTimes.clicked.connect(self.autosave)
            self.ui.AC_ClickNTimesN.editingFinished.connect(self.autosave)

            self.ui.AC_KeyboardHours.valueChanged.connect(self.autosave)
            self.ui.AC_KeyboardMinutes.valueChanged.connect(self.autosave)
            self.ui.AC_KeyboardSeconds.valueChanged.connect(self.autosave)
            self.ui.AC_KeyboardMiliseconds.valueChanged.connect(self.autosave)
            self.ui.AC_KeyboardKeySequence.editingFinished.connect(self.autosave)
            self.ui.AC_KeyboardHotkey.editingFinished.connect(self.autosave)
            self.ui.AC_KeyboardClickUntilStopped.clicked.connect(self.autosave)
            self.ui.AC_KeyboardClickNTimes.clicked.connect(self.autosave)
            self.ui.AC_KeyboardHold.clicked.connect(self.autosave)
            self.ui.AC_KeyboardClickNTimesN.editingFinished.connect(self.autosave)

    def checkIfProgramIsAlreadyRunning(self):
        # print( 'Name of the window:', self.windowTitle() )
        target_window_title = 'Automatyczne robienie rzeczy 0.8'
        try:
            FindWindow( None, target_window_title )  # win32ui.FindWindow
        except error:  # win32ui.error
            print( 'Nie znaleziono' )
        else:
            print( 'Znaleziono' )
            exit()

    def releaseAllMouseButtons(self):
        if mouse.is_pressed( 'left' ):
            mouse.release( 'left' )
        if mouse.is_pressed( 'right' ):
            mouse.release( 'right' )
        if mouse.is_pressed( 'middle' ):
            mouse.release( 'middle' )

    def checkIfSavingIsPossible(self):
        if self.macroElements != [] and self.ui.creatorEditorName.text() != '':
            name = self.ui.creatorEditorName.text()
            for char in name:
                if char in self.charactersProhibitedInWindows:
                    print('Nazwa zawiera niedozwolone znaki! Nie zapisano!')
                    return True  # Blokuj zapis
            return False  # Nie blokuj zapisu
        else:
            print( 'Nie można zapisywać, nazwa:', self.ui.creatorEditorName.text(), ', len(macroElements):', len(self.macroElements) )
            return True  # blokuj zapis (brak nazwy lub elementów)

    def actionsWhatIsSelected(self):
        items = self.ui.creatorEditorActions.selectedItems()
        if items != []:
            item = items[0]
            if not (item.parent() is None):
                if item.parent().text(0) == "Nagrane":
                    self.ui.creatorEditorDeleteFromActions.setDisabled( False )
                else:
                    self.ui.creatorEditorDeleteFromActions.setDisabled( True )
                self.ui.creatorEditorAddToMacro.setDisabled( False )
            else:
                self.ui.creatorEditorDeleteFromActions.setDisabled( True )
                self.ui.creatorEditorAddToMacro.setDisabled( True )

    def actionInEditorClicked(self, clicked_index):
        print( 'actionInEditorClicked' )
        print( 'clicked_index:', clicked_index )
        print( 'selected_index:', self.ui.creatorEditorTreeView.selectedIndexes() )
        if clicked_index in self.ui.creatorEditorTreeView.selectedIndexes():
            print( 'Kliknięto w zaznaczone' )
        else:
            print( 'Kliknięto w niezaznaczone' )

    def isPlaceholderSelected(self):
        items = self.ui.creatorEditorTreeView.selectedIndexes()
        if items != []:
            print('creatorRemoveActionFromMacro -', items)
            type_of_action = type(self.treeModel.itemFromIndex(items[0]).action).__name__
            if type_of_action == 'PlaceholderEvent':
                return True
        return False

    def editorSelectionChanged(self):
        selected = self.ui.creatorEditorTreeView.selectedIndexes()
        if selected != []:  # coś jest w makro
            self.ui.creatorEditorDeleteFromMacro.setDisabled( self.isPlaceholderSelected() )  # dostępne
        else:
            self.ui.creatorEditorDeleteFromMacro.setDisabled( True )  # Niedostępne
        blocker = QSignalBlocker(self.ui.creatorEditorTreeView)
        self.creatorOpenSelectedInEditor()  # To ma być zawsze na końcu
        blocker.unblock()

    def abortAllMacros(self):
        print( 'abortAllMacros' )
        self.AC_Stop()  # autoclicker
        self.creatorRecordPreviewStop()  # preview in creator
        for mti in self.macroTreeviewItems:
            mti.macroStop()

    def updateAbortionHotkey(self):
        print( 'updateAbortionHotkey' )
        hotkey = self.ui.abortHotkey.keySequence().toString()
        if hotkey != '':
            print("updateAbortionHotkey", hotkey)
            if self.abortionHotkey != '':
                try:
                    keyboard.remove_hotkey(self.abortAllMacros)
                except KeyError:
                    pass
            keyboard.add_hotkey( hotkey, self.abortAllMacros )
            self.abortionHotkey = hotkey
        else:
            print("updateAbortionHotkey ''")
            if self.abortionHotkey != '':
                try:
                    keyboard.remove_hotkey(self.abortAllMacros)
                except KeyError:
                    pass
            self.abortionHotkey = hotkey

    def creatorRecordNewRecording(self):
        print( 'creatorRecordNewRecording' )
        self.currentlyEditedItem = MacroEditorItem( RecordingEvent() )
        recording_event = self.currentlyEditedItem.action
        self.recordDialog.name.setText(recording_event.name)
        self.recordedObject = recording_event
        self.recordDialog.replaySpeed.setValue(recording_event.speed_factor)
        self.recordDialog.cutTimeLeft.setValue(recording_event.cutLeft)
        self.recordDialog.cutTimeRight.setValue(recording_event.cutRight)
        self.recordDialog.includeMoves.setChecked(recording_event.include_moves)
        self.recordDialog.includeClicks.setChecked(recording_event.include_clicks)
        self.recordDialog.includeWheel.setChecked(recording_event.include_wheel)
        self.recordDialog.includeKeyboard.setChecked(recording_event.include_keyboard)

        self.recordDialog.save.setDisabled(True)

        self.creatorRecordUpdateTimeAndCuts()
        self.creatorSelectEditorPageByID(9)
        self.creatorRecordDisplay()

    def closeEvent(self, event):
        print( 'MainWindowCloseEvent' )
        if self.isDialogOpen:
            self.dialog.close()

    def dialogCloseEvent(self, event):
        print( 'DialogCloseEvent' )
        self.isDialogOpen = False

    def closeEditorDialog(self):
        print( 'closeEditorDialog' )
        self.dialog.close()

    def clearEditor(self):
        print( 'clearEditor' )
        if self.macroElements == []:
            self.macroElements = []
            self.currentlyEditedItem = None
            self.treeModel = QStandardItemModel()
            self.rootNode = self.treeModel.invisibleRootItem()
            self.treeModel.setColumnCount(2)
            # self.ui.creatorEditorTreeView.select
            self.ui.creatorEditorTreeView.setModel(self.treeModel)
            self.ui.creatorEditorTreeView.setColumnWidth(0, 355)
            self.ui.creatorEditorTreeView.setColumnWidth(1, 100)
            self.treeModel.setHeaderData(0, Qt.Horizontal, 'Nazwa czynności')
            self.treeModel.setHeaderData(1, Qt.Horizontal, 'Czas po wykonaniu')

            self.ui.creatorEditorName.clear()
            self.editorSelectionModel = self.ui.creatorEditorTreeView.selectionModel()

            self.editorSelectionModel.selectionChanged.connect( self.editorSelectionChanged )
            self.ui.creatorEditorTreeView.doubleClicked.connect( self.editorSelectionChanged )
            self.creatorSelectEditorPageByID(10)
            self.ui.creatorEditorDeleteFromMacro.setDisabled(True)  # Niedostępne
            self.ui.creatorEditorSave.setDisabled( self.checkIfSavingIsPossible() )
        else:
            self.clearEditorConfirmation()

    def clearEditorConfirmation(self):
        print('clearEditorConfirmation')
        msg = QMessageBox()
        msg.setWindowTitle("Kreator zawiera rzeczy!")
        msg.setText("Czy na pewno chcesz go wyczyścić?")
        msg.setInformativeText("Rzeczy z listy komend tworzących makro zostaną usunięte!")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.buttonClicked.connect(self.clearEditorConfirmed)
        x = msg.exec_()

    def clearEditorConfirmed(self, i):
        print('clearEditorConfirmed')
        if i.text() == 'OK':
            self.macroElements = []
            self.currentlyEditedItem = None
            self.treeModel = QStandardItemModel()
            self.rootNode = self.treeModel.invisibleRootItem()
            self.treeModel.setColumnCount(2)
            # self.ui.creatorEditorTreeView.select
            self.ui.creatorEditorTreeView.setModel(self.treeModel)
            self.ui.creatorEditorTreeView.setColumnWidth(0, 355)
            self.ui.creatorEditorTreeView.setColumnWidth(1, 100)
            self.treeModel.setHeaderData(0, Qt.Horizontal, 'Nazwa czynności')
            self.treeModel.setHeaderData(1, Qt.Horizontal, 'Czas po wykonaniu')

            self.ui.creatorEditorName.clear()
            self.editorSelectionModel = self.ui.creatorEditorTreeView.selectionModel()

            self.editorSelectionModel.selectionChanged.connect(self.editorSelectionChanged)
            self.ui.creatorEditorTreeView.doubleClicked.connect(self.editorSelectionChanged)
            self.creatorSelectEditorPageByID(10)
            self.ui.creatorEditorDeleteFromMacro.setDisabled(True) # Niedostępne
            self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())
            print( 'Cleared' )
        else:
            print( 'Not cleared' )

    def testowa(self):
        print( 'test' )

    def saveMacroFromEditorToMacroTree(self):
        print( 'saveMacroFromEditorToMacroTree' )
        if self.macroElements != [] and self.ui.creatorEditorName.text() != '':
            name = self.ui.creatorEditorName.text()
            for char in name:
                if char in self.charactersProhibitedInWindows:
                    print( 'Nazwa zawiera niedozwolone znaki! Nie zapisano!' )
                    return

            item_duration = QStandardItem( str("%.2f" % self.updateTime( self.macroElements )) )
            item_duration.setEditable(False)
            item_speed = QStandardItem()

            # print(self.macroTreeModel.itemFromIndex(index_speed))

            item_hotkey = QStandardItem()
            item_hotkey.setData( QKeySequence(1), Qt.EditRole )

            item = MacroTreeviewItem( deepcopy(self.macroElements), name, item_duration=item_duration, item_hotkey=item_hotkey, item_speed=item_speed )

            is_found = False
            for i in range(len(self.macroTreeviewItems)):
                if self.macroTreeviewItems[i].text() == name:
                    is_found = True
                    exit_code = self.macroOverwriteConfirmation()
                    if exit_code == 1024:  # Nadpisywać
                        try:
                            keyboard.remove_hotkey( self.macroTreeviewItems[i].macroPrep )
                            print( "odbindowany" )
                        except KeyError:
                            print( 'Nie byl zbindowany i tak' )
                        row = self.macroTreeviewItems[i].row()
                        self.macroTreeModel.setItem(row, 0, item)
                        self.macroTreeModel.setItem(row, 1, item_duration)
                        self.macroTreeModel.setItem(row, 2, item_hotkey)
                        self.macroTreeModel.setItem(row, 3, item_speed)
                        self.macroTreeviewItems[i] = item
                        print( 'Nadpisano macro!' )
                    elif exit_code > 1024:  # Nie nadpisywać
                        return
                    else:
                        print( 'O.o co jest o.O' )
                    break

            if not is_found:
                print( 'Dodano nowe macro!' )
                self.macroRootNode.appendRow([item, item_duration, item_hotkey, item_speed])
                self.macroTreeviewItems.append(item)

            index_speed = item_speed.index()
            self.ui.macroTreeView.setIndexWidget(index_speed, QDoubleSpinBox())
            item.widgetSpeedFactor = self.ui.macroTreeView.indexWidget(index_speed)
            item.widgetSpeedFactor.setValue(1.0)
            item.widgetSpeedFactor.editingFinished.connect(lambda: item.updateSpeedFactor(item.widgetSpeedFactor.value()))
            item.widgetSpeedFactor.editingFinished.connect( lambda: self.saveSingleMacro( item ) )
            index_hotkey = item_hotkey.index()
            self.ui.macroTreeView.setIndexWidget(index_hotkey, SingleKeySequenceEdit())
            item.widgetHotkey = self.ui.macroTreeView.indexWidget(index_hotkey)
            item.widgetHotkey.keySequenceChanged.connect(
                lambda: item.updateKeySequence(item.widgetHotkey.keySequence().toString()))
            item.widgetHotkey.keySequenceChanged.connect( lambda: self.saveSingleMacro( item ) )

            print( 'Dodano item do listy makr' )
            self.saveSingleMacro( item )

    def macroOverwriteConfirmation(self):
        print('macroOverwriteConfirmation')
        msg = QMessageBox()
        msg.setWindowTitle("Makro o tej nazwie już istnieje!")
        msg.setText("Czy na pewno chcesz zapisać to makro pod tą nazwą?")
        msg.setInformativeText("Spowoduje to nadpisanie istniejącego makra!")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        x = msg.exec_()
        return x

    def macroOverwriteConfirmed(self, i):
        if i.text() == 'OK':
            return 'Confirmed'
        else:
            return 'Unconfirmed'

    def saveAllMacros(self):
        print( 'saveAllMacros' )
        try:
            for MTI in self.macroTreeviewItems:
                with open( 'macros/' + MTI.text() + '.pickle', 'wb' ) as f:
                    pickle.dump( MTI, f )
        except FileNotFoundError:
            print( 'Folder nie istnieje! Tworzę folder...' )
            os.mkdir( 'macros' )

    def saveSingleMacro(self, MTI):
        print( 'saveSingleMacro' )
        try:
            with open('macros/' + MTI.text() + '.pickle', 'wb') as f:
                pickle.dump(MTI, f)
        except FileNotFoundError:
            print( 'Folder nie istnieje! Tworzę folder...' )
            os.mkdir( 'macros' )

    def loadAllMacros(self):
        print( 'loadAllMacros' )
        self.clearMacroData()
        try:
            list_of_files = os.listdir('macros')
            macros_for_unpickling = [file for file in list_of_files if os.path.splitext(file)[1] == '.pickle']
            # print( macros_for_unpickling )
            for macro_name in macros_for_unpickling:
                with open('macros/' + macro_name, 'rb') as pickled_macro:
                    unpickled = pickle.load(pickled_macro)
                    if type(unpickled).__name__ == 'MacroTreeviewItem':
                        self.loadSingleMacro( unpickled )

                    else:
                        print( 'Uwaga! Nieodpowiedni typ pliku! Dla pewności nie zostanie wczytany jako makro.' )
                        print( unpickled )
        except FileNotFoundError:
            print( 'Folder nie istnieje! Tworzę folder...' )
            os.mkdir( 'macros' )

    def loadSingleMacro(self, item):
        # print('Typ odpowiedni. Rozpoczynam wczytywanie do drzewa...')
        # print(item)
        item_duration = QStandardItem(str("%.2f" % self.updateTime(item.macro_editor_items_list, update_text=False)))
        item_duration.setEditable( False )

        item.itemDuration = item_duration

        item_speed = QStandardItem()
        item.itemSpeed = item_speed

        item_hotkey = QStandardItem()
        item_hotkey.setData(QKeySequence(1), Qt.EditRole)
        item.itemHotkey = item_hotkey

        self.macroRootNode.appendRow([item, item.itemDuration, item.itemHotkey, item.itemSpeed])
        self.macroTreeviewItems.append(item)

        index_speed = item.itemSpeed.index()
        self.ui.macroTreeView.setIndexWidget(index_speed, QDoubleSpinBox())
        item.widgetSpeedFactor = self.ui.macroTreeView.indexWidget(index_speed)
        item.widgetSpeedFactor.setValue(item.speed_factor)
        item.widgetSpeedFactor.editingFinished.connect(
            lambda: item.updateSpeedFactor(item.widgetSpeedFactor.value()))
        item.widgetSpeedFactor.editingFinished.connect( lambda: self.saveSingleMacro( item ) )

        index_hotkey = item.itemHotkey.index()
        self.ui.macroTreeView.setIndexWidget(index_hotkey, SingleKeySequenceEdit(QKeySequence().fromString(item.hotkey)))
        item.widgetHotkey = self.ui.macroTreeView.indexWidget(index_hotkey)

        # item.widgetHotkey.keySequenceChanged.connect( lambda: print( 'keySequenceChanged!' ) )
        item.widgetHotkey.keySequenceChanged.connect(
            lambda: item.updateKeySequence(item.widgetHotkey.keySequence().toString()))
        item.widgetHotkey.keySequenceChanged.connect( lambda: self.saveSingleMacro( item ) )

        item.updateSpeedFactor(item.widgetSpeedFactor.value())
        item.updateKeySequence(item.widgetHotkey.keySequence().toString(), just_loaded=True)

    def clearMacroData(self):
        print( 'clearMacroData' )
        self.macroTreeModel = QStandardItemModel()
        self.macroRootNode = self.macroTreeModel.invisibleRootItem()
        self.macroTreeModel.setColumnCount(4)  # Nazwa, Czas trwania, Skrót klawiszowy, Prędkość odtwarzania
        self.macroTreeModel.setHeaderData(0, Qt.Horizontal, 'Nazwa makra')
        self.macroTreeModel.setHeaderData(1, Qt.Horizontal, 'Czas trwania')
        self.macroTreeModel.setHeaderData(2, Qt.Horizontal, 'Skrót klawiszowy')
        self.macroTreeModel.setHeaderData(3, Qt.Horizontal, 'Prędkość')
        self.ui.macroTreeView.setModel(self.macroTreeModel)
        self.ui.macroTreeView.setColumnWidth(0, 445)
        self.macroTreeviewItems = []
        self.macroTreeModel.itemChanged.connect(self.MTIchanged)
        # self.ui.creatorEditorTreeView.mousePressEvent.connect( self.testowa )  # DO DOKONCZENIA - ZAZNACZENIE AKTYWUJE SKRÓT DO MAKRO

    def MTIchanged(self, item ):
        # print( bool(item.checkState()) )
        print( type(item).__name__, item.text() )
        if type(item).__name__ == 'MacroTreeviewItem':
            if bool(item.checkState()):  # just got set to active
                if item.hotkey != '':
                    try:
                        keyboard.remove_hotkey( item.macroPrep )
                    except KeyError:
                        print( 'Hotkey was inactive anyway' )
                    keyboard.add_hotkey( item.hotkey, item.macroPrep )
                    print( 'Hotkey set to:', item.hotkey )
                else:
                    print( 'Hotkey set to nothing' )
            else:  # just set to inactive
                if item.hotkey != '':
                    try:
                        keyboard.remove_hotkey( item.macroPrep )
                        print('Hotkey now inactive')
                    except KeyError:
                        print('Hotkey was inactive anyway')
                else:
                    print( 'Hotkey was inactive anyway' )

            if item.last_known_name == item.text():
                print( 'te same nazwy', item.last_known_name, item.text() )
            else:
                counter = 0
                for MTI in self.macroTreeviewItems:
                    if MTI.text() == item.text():
                        counter += 1
                if counter == 0:
                    print( 'Cos tu nie gra!' )
                elif counter == 1:
                    print( 'Dokladnie jedno macro o tej nowej nazwie. Można zapisać.' )
                    os.remove('macros/' + item.last_known_name + '.pickle')
                    item.last_known_name = item.text()
                else:
                    print( 'Więcej niż jedno macro o tej nowej nazwie - cofam zmianę nazwy' )
                    item.setText( item.last_known_name )

            self.saveSingleMacro( item )

    def deleteSelectedMacro(self):
        indexes = self.ui.macroTreeView.selectedIndexes()
        if indexes != []:
            self.deleteSelectedMacroConfirmation()

    def deleteSelectedMacroConfirmation(self):
        print( 'deleteSelectedMacroConfirmation' )
        msg = QMessageBox()
        msg.setWindowTitle("Usuwanie makra")
        msg.setText("Czy na pewno chcesz usunąć zaznaczone makro?")
        msg.setInformativeText("Ta czynność jest nieodwracalna!")
        msg.setIcon( QMessageBox.Warning )
        msg.setStandardButtons( QMessageBox.Ok | QMessageBox.Cancel )
        msg.setDefaultButton( QMessageBox.Cancel )
        msg.buttonClicked.connect( self.deleteSelectedMacroConfirmed )
        x = msg.exec_()

    def deleteSelectedMacroConfirmed(self, i):
        print( 'deleteSelectedMacroConfirmed' )
        if i.text() == 'OK':
            print("Macro deleted")
            indexes = self.ui.macroTreeView.selectedIndexes()
            if indexes != []:
                print('deleteSelectedMacro')
                row_number = indexes[0].row()
                root_index = self.macroTreeModel.indexFromItem(self.macroRootNode)
                item = self.macroTreeviewItems[row_number]
                if item.hotkey != '':
                    try:
                        keyboard.remove_hotkey(item.macroPrep)
                    except KeyError:
                        pass
                os.remove('macros/' + item.text() + '.pickle')
                self.macroTreeModel.removeRow(row_number, root_index)
                self.macroTreeviewItems.pop(row_number)


    def inspectMacroItem(self):
        print( 'inspectMacroItem' )
        indexes = self.ui.macroTreeView.selectedIndexes()
        for index in indexes:
            print(self.macroTreeModel.itemFromIndex(index))
        # self.showMacroStructure()

    def inspectRecording(self):
        print( 'inspectRecording' )
        if not self.ui.creatorEditorTreeView.selectedIndexes() == []:
            item_index = self.ui.creatorEditorTreeView.selectedIndexes()[0]
            print( self.treeModel.itemFromIndex( item_index ) )

        # selection_model = self.ui.creatorEditorTreeView.selectionModel()
        # print( selection_model )
        # print( selection_model.currentIndex() )

    def creatorEditorDelete(self):
        print( 'creatorEditorDelete' )
        if self.ui.creatorEditorActions.indexFromItem(self.ui.creatorEditorActions.selectedItems()[0], 0 ).parent().row() == 3:  # Upewniamy się, że kasujemy z zakładki "nagrane"
            self.creatorEditorDeleteConfirmation()

    def creatorEditorDeleteConfirmation(self):
        print('creatorEditorDeleteConfirmation')
        msg = QMessageBox()
        msg.setWindowTitle("Usuwanie nagrania")
        msg.setText("Czy na pewno chcesz usunąć to nagranie?")
        msg.setInformativeText("Dane nagrania zostaną utracone!")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.buttonClicked.connect( self.creatorEditorDeleteConfirmed )
        x = msg.exec_()

    def creatorEditorDeleteConfirmed(self, i):
        print('creatorEditorDeleteConfirmed')
        if i.text() == 'OK':
            self.recordsDict.pop(self.ui.creatorEditorActions.selectedItems()[0].text(0), None)
            self.ui.creatorEditorActions.topLevelItem(3).removeChild(self.ui.creatorEditorActions.selectedItems()[0])
            self.pickleRecordings()
            print( "Deleted" )
        else:
            print( 'Deleting canceled' )

    def creatorAddActionToMacro(self):
        print( 'creatorAddActionToMacro' )
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
            else:
                is_name_known = False
                print( 'Nieznana nazwa' )
            item = MacroEditorItem(item, item_name)

            print( 'creatorAddActionToMacro -', item_name )
            if is_name_known:
                blocker = QSignalBlocker( self.editorSelectionModel )
                if self.ui.creatorEditorTreeView.selectedIndexes() == []:   # if no action in the macro is selected
                    self.rootNode.appendRow( [item, QStandardItem('1')] )
                    self.macroElements.append( item )  # Dodawanie elementu do listy poleceń makra

                    if item_name == "Wykonaj N razy":
                        item_name = "Początek pętli"
                        placeholder_item = MacroEditorItem(PlaceholderEvent(), item_name)
                        item.appendRow([ placeholder_item, QStandardItem()])
                        self.ui.creatorEditorTreeView.setExpanded( item.index(), True )

                        new_index = self.treeModel.indexFromItem(placeholder_item)
                        time_index = new_index.siblingAtColumn(1)

                        selection = QItemSelection(new_index, time_index)

                        self.editorSelectionModel.select(selection,  self.editorSelectionModel.ClearAndSelect)

                    else:
                        new_index = self.treeModel.indexFromItem(item)
                        time_index = new_index.siblingAtColumn(1)

                        selection = QItemSelection(new_index, time_index)

                        self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)
                else:
                    parent_index = self.ui.creatorEditorTreeView.selectedIndexes()[0].parent()
                    if not parent_index.isValid():    # if item is from top level of the tree
                        index = self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1
                        self.rootNode.insertRow( index, item )    # z jakiegoś powodu zamiast rzeczy w zmiennej item, wstawia QStandardItem()
                        self.rootNode.setChild( index, item )     # dlatego w tej linijce to nadpisujemy moim itemem i działa
                        self.macroElements.insert( index, item )  # Dodawanie elementu do listy poleceń makra

                        if item_name == "Wykonaj N razy":
                            item_name = "Początek pętli"
                            placeholder_item = MacroEditorItem(PlaceholderEvent(), item_name)
                            item.appendRow([placeholder_item, QStandardItem()])
                            self.ui.creatorEditorTreeView.setExpanded( item.index(), True )

                            new_index = self.treeModel.indexFromItem(placeholder_item)
                            time_index = new_index.siblingAtColumn(1)

                            selection = QItemSelection( new_index, time_index )

                            self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                        else:
                            new_index = self.treeModel.indexFromItem(item)
                            time_index = new_index.siblingAtColumn(1)

                            selection = QItemSelection(new_index, time_index)

                            self.editorSelectionModel.select( selection, self.editorSelectionModel.ClearAndSelect )

                    else:  # if item in not from top level of the tree

                        item_index = self.ui.creatorEditorTreeView.selectedIndexes()[0].row() + 1
                        self.treeModel.itemFromIndex( parent_index ).insertRow( item_index, [item, QStandardItem('123')] )
                        # self.treeModel.itemFromIndex( parent_index ).setChild( item_index, [item, QStandardItem()] )
                        self.treeModel.itemFromIndex( parent_index ).action.event_list.insert( item_index, item )  # Dodawanie elementu do listy poleceń makra

                        if item_name == "Wykonaj N razy":
                            item_name = "Początek pętli"
                            placeholder_item = MacroEditorItem(PlaceholderEvent(), item_name)
                            item.appendRow([placeholder_item, QStandardItem()])
                            self.ui.creatorEditorTreeView.setExpanded( item.index(), True )

                            new_index = self.treeModel.indexFromItem(placeholder_item)
                            time_index = new_index.siblingAtColumn(1)

                            selection = QItemSelection(new_index, time_index)

                            self.editorSelectionModel.select( selection, self.editorSelectionModel.ClearAndSelect )

                        else:
                            new_index = self.treeModel.indexFromItem(item)
                            time_index = new_index.siblingAtColumn(1)

                            selection = QItemSelection(new_index, time_index)

                            self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                self.macroUpdateTime()
                blocker.unblock()

                self.ui.creatorEditorDeleteFromMacro.setDisabled(self.isPlaceholderSelected())  # dostępne
                self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())
                self.creatorOpenSelectedInEditor()  # Musi być ostatnie!

    def creatorRemoveActionFromMacro(self):
        print( 'creatorRemoveActionFromMacro' )
        if not self.ui.creatorEditorTreeView.selectedIndexes() == []:  # if some action in the macro is selected
            items = self.ui.creatorEditorTreeView.selectedIndexes()
            print( 'creatorRemoveActionFromMacro -', items )
            type_of_action = type(self.treeModel.itemFromIndex( items[0] ).action).__name__
            if type_of_action == 'PlaceholderEvent':
                return
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

            if self.macroElements == []:
                self.creatorSelectEditorPageByID(10)
                self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())
            else:
                self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())
                self.macroUpdateTime()

    def creatorSelectEditorPageByID(self, page_id):
        self.recordDialog.pages.setCurrentIndex( page_id )

    def creatorMoveSelectedActionUp(self):
        print( 'creatorMoveSelectedActionUp' )
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()

        if indexes != []:
            qt_is_broken_and_for_some_reason_this_fixes_it = self.treeModel.itemFromIndex(self.macroElements[-1].index().siblingAtColumn(1))
            row_number = indexes[0].row()
            parent_index = indexes[0].parent()
            print( 'row:', row_number )
            print( 'parent:', parent_index )

            blocker = QSignalBlocker(self.editorSelectionModel)

            if row_number > 1 and parent_index.isValid():  # row 0 is reserved for placeholder item
                # row_of_items = self.treeModel.takeRow( row_number )
                parent_item = self.treeModel.itemFromIndex( parent_index )
                row_of_items = parent_item.takeRow( row_number )
                parent_item.insertRow( row_number - 1, row_of_items )

                parent_item.action.event_list.insert( row_number-1, parent_item.action.event_list.pop( row_number ) )

                new_index = self.treeModel.indexFromItem(row_of_items[0])
                time_index = self.treeModel.indexFromItem(row_of_items[1])

                selection = QItemSelection(new_index, time_index)

                self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                # self.editorSelectionModel.setCurrentIndex(new_index, self.editorSelectionModel.ClearAndSelect)
                # self.editorSelectionModel.setCurrentIndex(time_index, self.editorSelectionModel.Select)

                self.macroUpdateTime()

            elif row_number > 0 and not parent_index.isValid():
                print('row_number:', row_number )
                parent_item = self.rootNode
                row_of_items = parent_item.takeRow(row_number)

                print( 'row_of_items:', row_of_items )
                parent_item.insertRow(row_number - 1, row_of_items)

                self.macroElements.insert(row_number - 1, self.macroElements.pop(row_number))

                new_index = self.treeModel.indexFromItem(row_of_items[0])
                time_index = self.treeModel.indexFromItem(row_of_items[1])

                selection = QItemSelection(new_index, time_index)
                self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                # self.editorSelectionModel.setCurrentIndex(new_index, self.editorSelectionModel.ClearAndSelect)
                # self.editorSelectionModel.setCurrentIndex(time_index, self.editorSelectionModel.Select)

                self.macroUpdateTime()
            else:
                print( 'Nie mozna przesunac itemu w gorę!' )
            blocker.unblock()
            # self.creatorOpenSelectedInEditor() # niepotrzebne

    def creatorMoveSelectedActionDown(self):
        print( 'creatorMoveSelectedActionDown' )
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()
        if indexes != []:
            row_number = indexes[0].row()
            parent_index = indexes[0].parent()
            print( 'row:', row_number )
            print( 'parent:', parent_index )


            if parent_index.isValid():
                parent_item = self.treeModel.itemFromIndex( parent_index )
                row_limit = len( parent_item.action.event_list )
                if row_number + 1 < row_limit and row_number != 0:
                    row_of_items = parent_item.takeRow(row_number)
                    parent_item.insertRow(row_number + 1, row_of_items)

                    parent_item.action.event_list.insert(row_number + 1, parent_item.action.event_list.pop(row_number))

                    new_index = self.treeModel.indexFromItem(row_of_items[0])
                    time_index = self.treeModel.indexFromItem(row_of_items[1])

                    selection = QItemSelection(new_index, time_index)
                    self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                    # self.editorSelectionModel.setCurrentIndex(new_index, self.editorSelectionModel.ClearAndSelect)
                    # self.editorSelectionModel.setCurrentIndex(time_index, self.editorSelectionModel.Select)

                    self.macroUpdateTime()
                else:
                    print('Nizej sie nie da!')

            else:
                parent_item = self.rootNode
                row_limit = len( self.macroElements )
                if row_number + 1 < row_limit:
                    print( 'row_number:', row_number, 'row_limit:', row_limit )
                    row_of_items = parent_item.takeRow( row_number )
                    parent_item.insertRow(row_number + 1, row_of_items)

                    self.macroElements.insert(row_number + 1, self.macroElements.pop(row_number))

                    new_index = self.treeModel.indexFromItem(row_of_items[0])
                    time_index = self.treeModel.indexFromItem(row_of_items[1])

                    selection = QItemSelection(new_index, time_index)
                    self.editorSelectionModel.select(selection, self.editorSelectionModel.ClearAndSelect)

                    # self.editorSelectionModel.setCurrentIndex(new_index, self.editorSelectionModel.ClearAndSelect)
                    # self.editorSelectionModel.setCurrentIndex(time_index, self.editorSelectionModel.Select)

                    self.macroUpdateTime()
                else:
                    print( 'Nizej sie nie da!' )

    def inspectThis(self):
        print( 'inspectThis' )
        # print( self.macroElements )
        indexes = self.ui.creatorEditorTreeView.selectedIndexes()
        print( 'Row: [', end='')
        for index in indexes:
            print( self.treeModel.itemFromIndex(index), end=', ' )
        print(']')
        item = self.treeModel.itemFromIndex(indexes[0])
        sibling = self.treeModel.itemFromIndex(item.index().siblingAtColumn(1))
        print('item:', item, 'sibling:', sibling)
        # self.showMacroStructure()

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
        print( 'showMacroStructure' )
        string = '['
        for element in self.macroElements:
            string += str(element) + ', '
        print(string + ']')

    def openEmptyEditor(self):
        print( 'openEmptyEditor' )
        self.clearEditor()
        self.ui.tabs.setCurrentIndex(1)

    def openSelectedMacroInEditor(self):
        print( 'openSelectedMacroInEditor' )
        indexes = self.ui.macroTreeView.selectedIndexes()
        if indexes != []:
            macro_item = self.macroTreeModel.itemFromIndex( indexes[0] )
            items = macro_item.macro_editor_items_list
            self.clearEditor()

            self.macroElements = deepcopy( items )

            self.putStuffIntoEditor( self.macroElements, self.rootNode )
            self.macroUpdateTime()
            self.ui.creatorEditorTreeView.expandAll()
            self.ui.creatorEditorName.setText( macro_item.text() )
            self.ui.creatorEditorSave.setDisabled(self.checkIfSavingIsPossible())
            self.ui.tabs.setCurrentIndex( 1 )

    def putStuffIntoEditor(self, event_list, parent):

        for item in event_list:
            if item.action.event_type != 'ForEvent':
                parent.appendRow([item, QStandardItem()])
            else:
                parent.appendRow([item, QStandardItem()])
                self.putStuffIntoEditor( item.action.event_list, item )

    def macroUpdateTime(self):
        print( 'macroUpdateTime' )
        if len(self.macroElements) > 0:
            self.macroTotalTime = self.updateTime( self.macroElements )

            # time_string = str( floor( self.macroTotalTime*100)/100 )
            # self.treeModel.itemFromIndex(self.macroElements[-1].index().siblingAtColumn(1)).setText(time_string)

    def updateTime_backup(self, events, indentation='', update_text=True):
        # print( 'updateTime, len(self.macroElements)', len( events ) )
        recording_duration = 0
        for_event_duration = 0
        execution_time = 0.005  # 10ms ( estimated time distance between recorded mouse events on my PC )
        for i in range(len(events)):
            if i == 0 or isinstance(events[i].action, PlaceholderEvent) or isinstance(events[i - 1].action,
                                                                                      PlaceholderEvent):
                events[i].action.time = 0
            else:
                if events[i].action.event_type in ['keyboard', 'mouse']:
                    events[i].action.time = events[i - 1].action.time
                elif events[i].action.event_type == 'nseconds':
                    events[i].action.time = events[i - 1].action.time + events[i].action.wait_time
                else:
                    events[i].action.time = events[i - 1].action.time + execution_time

                if isinstance(events[i - 1].action, MoveEventV2):
                    events[i].action.time += events[i - 1].action.duration
                elif events[i - 1].action.event_type == 'nseconds':
                    events[i].action.time += events[i - 1].action.wait_time
                elif isinstance(events[i - 1].action, ForEvent):
                    events[i].action.time += for_event_duration
                    for_event_duration = 0
                elif isinstance(events[i - 1].action, RecordingEvent):
                    if events[i - 1].action != events[i].action:  # Happens when it's the only element in macro
                        events[i].action.time += recording_duration + execution_time
                        recording_duration = 0

            if not isinstance(events[i].action, PlaceholderEvent) and update_text:
                self.treeModel.itemFromIndex(events[i].index().siblingAtColumn(1)).setText(str(floor(
                    events[i].action.time * 100) / 100))  # self.treeModel.itemFromIndex(indexes[0].siblingAtColumn(1).

            if isinstance(events[i].action, ForEvent):
                for_event_duration = (self.updateTime(events[i].action.event_list, indentation + '   ',
                                                      update_text=update_text) + execution_time) * events[
                                         i].action.times
            elif isinstance(events[i].action, RecordingEvent):
                if len(events[i].action.events_final) > 0:
                    recording_duration = events[i].action.events_final[-1].time / events[i].action.speed_factor
                else:
                    recording_duration = 0
                # + execution_time to account for last action's duration. It could be a problem if ForEvent events were executed many times
        return float(events[-1].action.time + for_event_duration + recording_duration)

    def updateTime(self, events, indentation='', update_text=True):
        # print( 'updateTime, len(self.macroElements)', len( events ) )
        recording_duration = 0
        for_event_duration = 0
        execution_time = self.ui.execution_time.value() / 1000  # 5ms ( estimated time distance between recorded mouse events on my PC )
        for i in range( len(events) ):
            if (i == 0 or isinstance( events[i].action, PlaceholderEvent ) or isinstance( events[i-1].action, PlaceholderEvent )):
                if events[i].action.event_type == 'nseconds':
                    events[i].action.time = events[i].action.wait_time
                else:
                    events[i].action.time = 0
            else:
                if events[i].action.event_type in ['keyboard', 'mouse']:
                    events[i].action.time = events[i-1].action.time
                elif events[i].action.event_type == 'nseconds':
                    events[i].action.time = events[i-1].action.time + events[i].action.wait_time
                else:
                    events[i].action.time = events[i-1].action.time + execution_time

                if isinstance( events[i-1].action, MoveEventV2 ):
                    events[i].action.time += events[i-1].action.duration
                # elif events[i-1].action.event_type == 'nseconds':
                    # events[i].action.time += events[i-1].action.wait_time
                elif isinstance( events[i-1].action, ForEvent ):
                    events[i].action.time += for_event_duration
                    for_event_duration = 0
                elif isinstance( events[i-1].action, RecordingEvent ):
                    if events[i-1].action != events[i].action:  # Happens when it's the only element in macro
                        events[i].action.time += recording_duration + execution_time
                        recording_duration = 0

            if not isinstance( events[i].action, PlaceholderEvent ) and update_text:
                self.treeModel.itemFromIndex(events[i].index().siblingAtColumn(1)).setText( str(floor(events[i].action.time*1000)/1000) )  # self.treeModel.itemFromIndex(indexes[0].siblingAtColumn(1).

            if isinstance( events[i].action, ForEvent ):
                for_event_duration = (self.updateTime( events[i].action.event_list, indentation + '   ', update_text=update_text ) + execution_time) * events[i].action.times
            elif isinstance( events[i].action, RecordingEvent ):
                if len(events[i].action.events_final) > 0:
                    recording_duration = events[i].action.events_final[-1].time / events[i].action.speed_factor
                else:
                    recording_duration = 0
                # + execution_time to account for last action's duration. It could be a problem if ForEvent events were executed many times
        return float( events[-1].action.time + for_event_duration + recording_duration )

    def updateTime_testowy(self, events, indentation='', update_text=True):
        # print( 'updateTime, len(self.macroElements)', len( events ) )
        recording_duration = 0
        for_event_duration = 0
        execution_time = 0.005  # 10ms ( estimated time distance between recorded mouse events on my PC )
        for i in range( len(events) ):
            if (i == 0 or isinstance( events[i].action, PlaceholderEvent ) or isinstance( events[i-1].action, PlaceholderEvent )):
                if events[i].action.event_type == 'nseconds':
                    events[i].action.time = events[i].action.wait_time
                else:
                    events[i].action.time = 0
            else:
                if events[i].action.event_type in ['keyboard', 'mouse']:
                    events[i].action.time = events[i-1].action.time
                elif events[i].action.event_type == 'nseconds':
                    events[i].action.time = events[i-1].action.time + events[i].action.wait_time
                else:
                    events[i].action.time = events[i-1].action.time + execution_time

                if isinstance( events[i-1].action, MoveEventV2 ):
                    events[i].action.time += events[i-1].action.duration
                # elif events[i-1].action.event_type == 'nseconds':
                    # events[i].action.time += events[i-1].action.wait_time
                elif isinstance( events[i-1].action, ForEvent ):
                    events[i].action.time += for_event_duration
                    for_event_duration = 0
                elif isinstance( events[i-1].action, RecordingEvent ):
                    if events[i-1].action != events[i].action:  # Happens when it's the only element in macro
                        events[i].action.time += recording_duration + execution_time
                        recording_duration = 0

              # self.treeModel.itemFromIndex(indexes[0].siblingAtColumn(1).

            if isinstance( events[i].action, ForEvent ):
                for_event_duration = (self.updateTime( events[i].action.event_list, indentation + '   ', update_text=update_text ) + execution_time) * events[i].action.times
            elif isinstance( events[i].action, RecordingEvent ):
                if len(events[i].action.events_final) > 0:
                    recording_duration = events[i].action.events_final[-1].time / events[i].action.speed_factor
                else:
                    recording_duration = 0
                # + execution_time to account for last action's duration. It could be a problem if ForEvent events were executed many times

            if not isinstance( events[i].action, PlaceholderEvent ) and update_text and i > 0:
                if events[i].action.event_type != 'nseconds':
                    print( "events[i-1].index()", events[i-1].index() ) # index invalid????????????????????????????????????????????????????
                    print("self.treeModel.itemFromIndex(events[i - 1].index())", self.treeModel.itemFromIndex(events[i - 1].index()))
                    sibling_index = self.treeModel.itemFromIndex(events[i - 1].index())  # .index().siblingAtColumn(1)
                    sibling = self.treeModel.itemFromIndex(sibling_index)
                    sibling.setText( str(floor(events[i].action.time*100)/100) )
                else:
                    self.treeModel.itemFromIndex(events[i - 1].index().siblingAtColumn(1)).setText(str(floor(events[i-1].action.time * 100) / 100))

        return float( events[-1].action.time + for_event_duration + recording_duration )

    def previewMacro(self):
        print( 'previewMacro' )
        before = time.time()
        self.macroAbortEvent = threading.Event()
        self.macroThread = threading.Thread(target=lambda: self.macroPlay( self.macroElements ) )
        self.macroThread.start()
        self.macroThread.join()
        self.isMacroRunning = False
        self.releaseAllMouseButtons()
        keyboard.stash_state()

        print( 'Total macro duration:', time.time() - before )

    def macroPlay(self, target, speed_factor=1.0, include_clicks=True, include_moves=True, include_wheel=True, include_keyboard=True):
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
                x = self.playRecording(event.events_final, event.speed_factor * speed_factor, event.include_clicks,
                                       event.include_moves, event.include_wheel, event.include_keyboard)
                if isinstance(x, str):
                    return 'abort'

            elif isinstance(event, ForEvent):  # PSUJE CZASY? CHYBA NIE, DO TESTU
                before = time.time()
                for i in range(event.times):
                    x = self.macroPlay(event.event_list, speed_factor, include_clicks, include_moves, include_wheel,
                                       include_keyboard)
                    if isinstance(x, str):
                        return 'abort'
                    time.sleep(0.0025 / speed_factor)  # PAMIĘTAJ O TYM, JEŚLI CZAS PRZESTANIE SIĘ ZGADZAC
                for_events_duration += time.time() - before
            elif isinstance(event, PlaceholderEvent):
                pass
            else:
                print('Nieznany typ eventu', event)

        keyboard.restore_modifiers(state)
        # keyboard.release( self.recordDialog.recordingHotkey.keySequence().toString() )
        # keyboard.release( self.recordDialog.previewHotkey.keySequence().toString() )
        # print( time.time() - timedelta )
        # print("macroPlay")


app = QApplication( sys.argv )

window = MainWindow()
window.show()

sys.exit(app.exec_())

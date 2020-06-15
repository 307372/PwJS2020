import threading
import keyboard
import mouse
import time


class AutoclickerMethods:

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
                try:
                    keyboard.remove_hotkey(self.AC_Toggle)
                except KeyError:
                    pass
            keyboard.add_hotkey(hotkey, self.AC_Toggle)
            self.AC_Hotkey = hotkey
        else:
            print("autoclickerHotkeyChange ''")
            if self.AC_Hotkey != '':
                try:
                    keyboard.remove_hotkey(self.AC_Toggle)
                except KeyError:
                    pass
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

    # klawiatura:

    def AC_KeyboardStartPrep(self):
        print( "AC_KeyboardStartPrep" )
        if not self.isACKeyboardRunning and self.ui.AC_KeyboardKeySequence.keySequence().toString() != '':
            self.isACKeyboardRunning = True
            thread = threading.Thread(target=self.AC_KeyboardStart)
            thread.start()

    def AC_KeyboardStart(self):
        print( "AC_KeyboardStart" )
        time_delay = self.ui.AC_KeyboardMiliseconds.value() + self.ui.AC_KeyboardSeconds.value() * 1000 + self.ui.AC_KeyboardMinutes.value() * 60 * 1000 + self.ui.AC_KeyboardHours.value() * 60 * 60 * 1000
        self.AC_KeyboardThread = threading.Event()

        key = self.ui.AC_KeyboardKeySequence.keySequence().toString().lower()
        if key != '' and key != self.ui.AC_KeyboardHotkey.keySequence().toString().lower():
            key = keyboard.parse_hotkey(key)
            if '+' in key:
                key = keyboard.key_to_scan_codes(key)
            print( 'code:', keyboard.key_to_scan_codes(key), 'key:', key)
            if self.ui.AC_KeyboardClickUntilStopped.isChecked():
                while True:
                    keyboard.press_and_release( key )
                    if self.AC_KeyboardThread.wait(timeout=time_delay / 1000):
                        break
            elif self.ui.AC_KeyboardClickNTimes.isChecked():
                i = 0
                while i < self.ui.AC_KeyboardClickNTimesN.value():
                    i += 1
                    keyboard.send( key, do_press=True, do_release=False )
                    self.AC_KeyboardThread.wait(timeout=0.001)
                    keyboard.send( key, do_press=False, do_release=True )
                    print( i )
                    if self.AC_KeyboardThread.wait(timeout=time_delay / 1000):
                        break
            elif self.ui.AC_KeyboardHold.isChecked():
                keyboard.press( key )
                time.sleep(1)
                hook = keyboard.on_press_key( key, self.AC_KeyboardStop, suppress=False )  # kliknięcie 'key' przez usera dodatkowo stopuje AC
                if self.AC_KeyboardThread.wait(timeout=threading.TIMEOUT_MAX):  # ~1193h
                    keyboard.unhook( hook )
                    keyboard.release( key )

            else:
                print( 'Cos poszlo nie tak! Nic nie jest zaznaczone!' )

        keyboard.stash_state()
        self.isACKeyboardRunning = False

    def AC_KeyboardStop(self, idk='idk'):
        print("AC_KeyboardStop")
        self.AC_KeyboardThread.set()
        key = self.ui.AC_KeyboardKeySequence.keySequence().toString()
        try:
            keyboard.release( key )
        except KeyError:
            print( 'Cos poszlo nie tak! klawisz:', key )

        self.isACKeyboardRunning = False

    def AC_KeyboardToggle(self):
        print( "AC_KeyboardToggle" )
        if self.isACKeyboardRunning:
            self.AC_KeyboardStop()
        else:
            self.AC_KeyboardStartPrep()

    def AC_KeyboardHotkeyChange(self):
        hotkey = self.ui.AC_KeyboardHotkey.keySequence().toString()
        if hotkey != '':
            print( "AC_KeyboardHotkeyChange", hotkey )
            if self.AC_KeyboardHotkey != '':
                try:
                    keyboard.remove_hotkey(self.AC_KeyboardToggle)
                except KeyError:
                    pass
            keyboard.add_hotkey(hotkey, self.AC_KeyboardToggle)
            self.AC_KeyboardHotkey = hotkey
        else:
            print("AC_KeyboardHotkeyChange ''")
            if self.AC_KeyboardHotkey != '':
                try:
                    keyboard.remove_hotkey(self.AC_KeyboardToggle)
                except KeyError:
                    pass
            self.AC_KeyboardHotkey = hotkey


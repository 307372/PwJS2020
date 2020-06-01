import threading
import keyboard
import mouse


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
                keyboard.remove_hotkey(self.AC_Hotkey)
            keyboard.add_hotkey(hotkey, self.AC_Toggle)
            self.AC_Hotkey = hotkey
        else:
            print("autoclickerHotkeyChange ''")
            if self.AC_Hotkey != '':
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

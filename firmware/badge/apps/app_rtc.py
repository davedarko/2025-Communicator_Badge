"""Template app for badge applications. Copy this file and update to implement your own app."""

import uasyncio as aio  # type: ignore

from apps.base_app import BaseApp
from net.net import register_receiver, send, BROADCAST_ADDRESS
from net.protocols import Protocol, NetworkFrame
from ui.page import Page
import ui.styles as styles
import lvgl

import time
from libs import urtc

from machine import RTC, I2C

"""
All protocols must be defined in their apps with unique ports. Ports must fit in uint8.
Try to pick a protocol ID that isn't in use yet; good luck.
Structdef is the struct library format string. This is a subset of cpython struct.
https://docs.micropython.org/en/latest/library/struct.html
"""
# NEW_PROTOCOL = Protocol(port=<PORT>, name="<NAME>", structdef="!")


class RTCApp(BaseApp):
    """Define a new app to run on the badge."""
    
    def __init__(self, name: str, badge):
        """ Define any attributes of the class in here, after super().__init__() is called.
            self.badge will be available in the rest of the class methods for accessing the badge hardware.
            If you don't have anything else to add, you can delete this method.
        """
        super().__init__(name, badge)
        # You can also set the sleep time when running in the foreground or background. Uncomment and update.
        # Remember to make background sleep longer so this app doesn't interrupt other processing.
        # self.foreground_sleep_ms = 10
        # self.background_sleep_ms = 1000
        self.rtc = urtc.DS3231(self.badge.sao_i2c)


    def start(self):
        """ Register the app with the system.
            This is where to register any functions to be called when a message of that protocol is received.
            The app will start running in the background.
            If you don't have anything else to add, you can delete this method.
        """
        super().start()
        # register_receiver(NEW_PROTOCOL, self.receive_message)

    def run_foreground(self):
        """ Run one pass of the app's behavior when it is in the foreground (has keyboard input and control of the screen).
            You do not need to loop here, and the app will sleep for at least self.foreground_sleep_ms milliseconds between calls.
            Don't block in this function, for it will block reading the radio and keyboard.
            If the app only runs in the background, you can delete this method.
        """

        if self.badge.keyboard.f1():
            print("Scan ")
            # Scan the SAO I2C bus
            found_rtc = False
            
            
            addons = self.badge.sao_i2c.scan()
            for addon in addons:
                print(addon)
                if addon == 104:
                    found_rtc = True
            
            if found_rtc:
                print("found rtc, accessing: ")
                current_datetime = self.rtc.datetime()
                t = time.gmtime();

                self.badge.display.clear()
                self.page = Page()
                self.page.create_content()
                self.page.replace_screen()
                self.add_message(
                    "RTC: "
                    + str(current_datetime.year)
                    + "-" + str(current_datetime.month)
                    + "-" + str(current_datetime.day)
                    + " " + str(current_datetime.hour)
                    + ":" + str(current_datetime.minute)
                    + ":" + str(current_datetime.second),
                    20
                    )
                self.add_message(
                    "INT: "
                    + str(t[0])
                    + "-" + str(t[1])
                    + "-" + str(t[2])
                    + " " + str(t[3])
                    + ":" + str(t[4])
                    + ":" + str(t[5]),
                    40
                    )   
        if self.badge.keyboard.f2():
            print("Set Time ")           
            dt = self.rtc.datetime()
            mrtc = RTC()
            mrtc.datetime((
                dt.year,
                dt.month,
                dt.day,
                dt.weekday,
                dt.hour,
                dt.minute,
                dt.second,
                0
            ))

            
        if self.badge.keyboard.f3():
            print("Set RTC ")
            initial_time_tuple = time.localtime()
            initial_time_seconds = time.mktime(initial_time_tuple)
            # Convert to tuple compatible with the library
            initial_time = urtc.seconds2tuple(initial_time_seconds)

            # Sync the RTC
            self.rtc.datetime(initial_time)
            
        if self.badge.keyboard.f4():
            print(" ")
        ## Co-op multitasking: all you have to do is get out
        if self.badge.keyboard.f5():
            self.badge.display.clear()
            self.switch_to_background()
        

    def run_background(self):
        """ App behavior when running in the background.
            You do not need to loop here, and the app will sleep for at least self.background_sleep_ms milliseconds between calls.
            Don't block in this function, for it will block reading the radio and keyboard.
            If the app only does things when running in the foreground, you can delete this method.
        """
        super().run_background()

    def switch_to_foreground(self):
        """ Set the app as the active foreground app.
            This will be called by the Menu when the app is selected.
            Any one-time logic to run when the app comes to the foreground (such as setting up the screen) should go here.
            If you don't have special transition logic, you can delete this method.
        """
        super().switch_to_foreground()
        self.badge.display.clear()
        self.page = Page()
        ## Note this order is important: it renders top to bottom that the "content" section expands to fill empty space
        ## If you want to go fully clean-slate, you can draw straight onto the p.scr object, which should fit the full screen.
        self.page.create_infobar(["RTC Manager", "Scan and set timers"])
        self.page.create_content()
        self.page.create_menubar(["Scan", "Set internal", "Set RTC", "", "Done"])
        self.page.replace_screen()


    def switch_to_background(self):
        """ Set the app as a background app.
            This will be called when the app is first started in the background and when it stops being in the foreground.
            If you don't have special transition logic, you can delete this method.
        """
        self.page = None
        super().switch_to_background()
        
    def add_message(self, message, y):
        self.welcome = lvgl.label(self.page.content)
        self.welcome.align(lvgl.ALIGN.TOP_LEFT, 120, y)
        self.welcome.set_style_text_font(lvgl.font_montserrat_16, 0)
        self.welcome.set_text(message)
        
def addZeroStr(i):
    if i.length < 2:
        return '0' + i
    else:
        return i
    
def addZeroInt(i):
    if i < 10:
        return '0' + str(i)
    else:
        return str(i)



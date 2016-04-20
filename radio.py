#!/usr/bin/env python
#
# @file Simple loop to control MPD on the Raspberry Pi.
# @author Sander Steenhuis AKA Redsandro <http://www.redsandro.com/>
# @since 2013-04-07
# Last modified: 2016-04-18
#
# This is free software, and is released under the terms of the GPL version 2 or (at your option) any later version.
# See license.txt or <http://www.gnu.org/licenses/>.

'''
This is a simple loop to control the MPD backend on my Raspberry Pi internet radio.

There are two GPIO buttons for prev/next. Pressing both resets MPD (clears playlist and loads "Internet Radio.m3u").
This is convenient after playing music files from the library using a client such as GMPC or MPDroid.

LCD:
New titles will scroll once, then a clock appears for convenience.
'''

import RPi.GPIO as GPIO
import subprocess as sub
import time
from datetime import datetime
from i2cYwRobotLcd import i2cYwRobotLcd

BTN_PREV = 11
BTN_NEXT = 12

lcd = i2cYwRobotLcd()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(BTN_PREV, GPIO.IN)
GPIO.setup(BTN_NEXT, GPIO.IN)

print "GPIO version %s loaded." % (GPIO.VERSION)



STATE = 0
wait = 0
timeNow = 0
timeLoop = 0
timeLoopSec = 0
scrollPos = 0
scrollDelay = -4
buf_time = ''
buf_title = ''
currTitle = ''
timeReset = 0
timeStr = 0
timeBuff = 0



# Init mpc
def mpcReset():
    lcd.init()
    sub.Popen(['mpc', 'clear'])
    sub.Popen(['mpc', 'load', 'Internet Radio'])    # Make sure the playlist is available.
    sub.Popen(['mpc', 'repeat', 'on'])
    sub.Popen(['mpc', 'play'])

def getTitle():
    global currTitle
    proc = sub.Popen(['mpc', 'current'], stdout=sub.PIPE)
    out, err = proc.communicate()

    # Writing to I2C is slow though, so only write the title when it changed.
    if (out != currTitle):
        currTitle = out

def btnPlay(_STATE=0):
    global wait, STATE, scrollPos, scrollDelay
    STATE = _STATE
    lcd.init()
    scrollPos = scrollDelay

mpcReset()



def btnPressed(channel):
    global timeReset
    timeEv = time.time()
    print '%d pressed' % channel

    if GPIO.input(BTN_PREV) and GPIO.input(BTN_NEXT) and (timeReset + 2) < timeEv:
        print 'RESET!'
        timeReset = time.time()
        mpcReset()
        return 0
    elif GPIO.input(BTN_PREV):
        print "Play Previous"
        btnPlay(BTN_PREV)
        sub.Popen(['mpc', 'prev'])
    elif GPIO.input(BTN_NEXT):
        print "Play Next"
        btnPlay(BTN_NEXT)
        sub.Popen(['mpc', 'next'])


GPIO.add_event_detect(BTN_PREV, GPIO.RISING, callback=btnPressed, bouncetime=200)
GPIO.add_event_detect(BTN_NEXT, GPIO.RISING, callback=btnPressed, bouncetime=200)



while True:

    # Base actions on certain intervals
    timeNow = time.time()

    # Calculate clock
    if (round(timeNow % 1) == 0):
        timeStr = datetime.now().strftime('%b %d  %H:%M:%S')
    else:
        timeStr = datetime.now().strftime('%b %d  %H:%M %S')

    # Write clock if buffer updated
    if (timeStr != timeBuff):
        timeBuff = timeStr

        # Write clock to LCD if we're done scrolling.
        if (scrollPos >= lcd.LCD_BUF_WIDTH):
            lcd.writeString(timeStr, 1)
        else:
            lcd.writeString(' ', 1)


    # Execute every 500 ms
    if (timeNow > timeLoop):
        timeLoop = timeNow + 0.5

        # Scroll the contents of the display once.
        if (scrollPos < lcd.LCD_BUF_WIDTH):
            if (scrollPos >= 0):
                lcd.scrollDisplayLeft()
            scrollPos = scrollPos + 1

    # Execute every 1000 ms
    if (timeNow > timeLoopSec):
        timeLoopSec = timeNow + 1.0

        # Get the title from MPC. Yes, we do this every second.
        # Sometimes it takes a second before the name is known.
        # And some streams change the title, kinda like RDS.
        getTitle()

    # Write title to LCD only when buffer was updated
    if (buf_title != currTitle):
        if (wait == 0 and scrollPos == lcd.LCD_BUF_WIDTH):
            scrollPos = 0
            lcd.init()
        else:
            buf_title = currTitle
            lcd.writeString(buf_title, 0)

    # This loop needs to sleep as much as possible while still being snappy.
    # Not sleeping makes the buttons very sensitive, but time() will be called too often, causing python to use 80% cpu.
    time.sleep(0.10)

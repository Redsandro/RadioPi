#!/usr/bin/env python
#
# @file Simple loop to control MPD on the Raspberry Pi.
# @author Sander Steenhuis AKA Redsandro <http://www.redsandro.com/>
# @since 2013-04-07
# Last modified: 2016-04-20
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
import sys
import time
from datetime import datetime
from threading import Thread, Event
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
buffTitleRaw = ''
currTitle = ''
buffTitle = ''
timeReset = 0
timeStr = 0
timeBuff = 0
stopFlag = Event()



class LcdControl(Thread):

    title = "RadioPi ;)"
    idx = 0

    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        global timeBuff
        while not self.stopped.wait(0.25):
            if self.title != currTitle:
                self.title = currTitle
                self.idx = 0
            if self.idx <= len(self.title):
                lcd.writeString(self.title[self.idx:self.idx+16].ljust(16, ' '))
                self.idx = self.idx + 1
            else:
                lcd.writeString(self.title[0:16])

            # Calculate clock
            timeStr = datetime.now().strftime('%b %d  %H:%M:%S')
            if timeStr != timeBuff:
                timeBuff = timeStr
                lcd.writeString(timeBuff, 1)



# Init mpc
def mpcReset():
    sub.Popen(['mpc', 'clear'])
    sub.Popen(['mpc', 'load', 'Internet Radio'])    # Make sure the playlist is available.
    sub.Popen(['mpc', 'repeat', 'on'])
    sub.Popen(['mpc', 'play'])

def getTitle():
    global currTitle, buffTitleRaw
    proc = sub.Popen(['mpc', '-f', '%name%_-_%artist%_-_%title%', 'current'], stdout=sub.PIPE)
    out, err = proc.communicate()
    if out != buffTitleRaw:
        buffTitleRaw = out
        # TODO: Switch display bij mp3, title eerst
        mName, mArtist, mTitle = out.strip().split('_-_')
        name1 = mName if len(mName) else mArtist
        name2 = mTitle
        currTitle = '%s - %s' % (name1, name2) if len(name1) and len(name2) else name1 if len(name1) else name2

def btnPlay(_STATE=0):
    global STATE, currTitle
    STATE = _STATE
    currTitle = ''



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



mpcReset()
thread = LcdControl(stopFlag)
thread.start()

GPIO.add_event_detect(BTN_PREV, GPIO.RISING, callback=btnPressed, bouncetime=200)
GPIO.add_event_detect(BTN_NEXT, GPIO.RISING, callback=btnPressed, bouncetime=200)

try:
    while True:
        # Get the title from MPC. Yes, we do this every second.
        # Sometimes it takes a second before the name is known.
        # And some streams change the title, kinda like RDS.
        getTitle()
        time.sleep(1.0)
except KeyboardInterrupt:
    stopFlag.set()
    print 'User abort'
except:
    stopFlag.set()
    print "\nUnexpected error:", sys.exc_info()[0]
    raise

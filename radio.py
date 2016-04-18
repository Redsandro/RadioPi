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

lcd = i2cYwRobotLcd()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)
GPIO.setup(12, GPIO.IN)

print "GPIO version %s loaded." % (GPIO.VERSION)



state = 0
wait = 0
currTime = 0
eventTime = 0
eventTimeSec = 0
scrollPos = 0
scrollDelay = -4
buf_time = ''
buf_title = ''



# Init mpc
def mpcReset():
	lcd.init();
	scrollPos = scrollDelay
	sub.Popen(['mpc', 'clear'])
	sub.Popen(['mpc', 'load', 'Internet Radio'])	# Make sure the playlist is available.
	sub.Popen(['mpc', 'repeat', 'on'])
	sub.Popen(['mpc', 'play'])

mpcReset()



# The loop that controls the app
while True:

	# Ignore buttons for a moment
	if wait > 0:
		wait = wait - 1
	elif wait == 0:
		state = 0

	# Reset - Pressing both buttons
	if GPIO.input(11) and GPIO.input(12):
		wait = 20
		if state != 1112:
			state = 1112
			print "RESET!"
			mpcReset()
	# Prev - GPIO pin 11
	elif GPIO.input(11):
		if state != 11:
			wait = 6
			state = 11
			#if (scrollPos > 0):
			#	scrollPos = scrollPos - 40
			lcd.init();
			scrollPos = scrollDelay
			print "Play previous"
			sub.Popen(['mpc', 'prev'])
	# Next - GPIO pin 12
	elif GPIO.input(12):
		if state != 12:
			wait = 6
			state = 12
			#if (scrollPos > 0):
			#	scrollPos = scrollPos - 40
			lcd.init();
			scrollPos = scrollDelay
			print "Play next"
			sub.Popen(['mpc', 'next'])

	# Little trickery to execute intensive commands only every 500 ms.
	if (currTime <= eventTime):
		# Update the time every 100 ms.
		currTime = time.time()
	else:
		eventTime = currTime + 0.50

		# Scroll the contents of the display once.
		if (scrollPos < lcd.LCD_BUF_WIDTH):
			if (scrollPos >= 0):
				lcd.scrollDisplayLeft()
			scrollPos = scrollPos + 1

		# Code to execute only once every 1000 ms.
		if (currTime > eventTimeSec):
			eventTimeSec = currTime + 1.0

			# Add clock if we're done scrolling.
			currDateTime = datetime.now().strftime('%b %d  %H:%M:%S')
			if (scrollPos >= lcd.LCD_BUF_WIDTH):
				lcd.writeString(currDateTime, 1)
			else:
				lcd.writeString(' ', 1)

			# Get the title from MPC. Yes, we do this every second.
			# Sometimes it takes a second before the name is known.
			# And some streams change the title, kinda like RDS.
			proc = sub.Popen(['mpc', 'current'], stdout=sub.PIPE)
			out, err = proc.communicate()

			# Writing to I2C is slow though, so only write the title when it changed.
			if (out != buf_title):
				buf_title = out
				lcd.writeString(buf_title, 0)

	# This loop needs to sleep as much as possible while still being snappy.
	# Not sleeping makes the buttons very sensitive, but time() will be called too often, causing python to use 80% cpu.
	time.sleep(0.1)

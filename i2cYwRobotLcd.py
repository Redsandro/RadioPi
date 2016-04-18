#!/usr/bin/env python
#
# @file This class exports controls for the "1602 I2C LCD for Arduino" on the Raspberry Pi.
# @author Sander Steenhuis AKA Redsandro <http://www.redsandro.com/>
# @since 2016-04-16
# Last modified: 2016-04-18
# Based on code by
# @author Matt Hawkins <http://www.raspberrypi-spy.co.uk/>
# @since 2015-09-20
#
# This is free software, and is released under the terms of the GPL version 3 or (at your option) any later version.
# See license.txt or <http://www.gnu.org/licenses/>.

import time
import smbus

class i2cYwRobotLcd:

	# Decive parameters
	I2C_ADDR				= 0x27
	LCD_WIDTH				= 16	# Maximum characters per line
	LCD_BUF_WIDTH			= 40	# Buffer width

	# Mode
	LCD_CHR					= 0b00000001	# Send character
	LCD_CMD					= 0b00000000	# Send data

	LCD_LINES				= (0x80, 0xC0, 0x94, 0xD4)

	# Backlight control
	LCD_ON					= 0x08
	LCD_OFF					= 0x00
	LCD_BACKLIGHT			= LCD_ON

	# Display controls
	LCD_DISPLAYON           = 0x04
	LCD_DISPLAYOFF          = 0x00
	LCD_CURSORON            = 0x02
	LCD_CURSOROFF           = 0x00
	LCD_BLINKON             = 0x01
	LCD_BLINKOFF            = 0x00

	# Timing constants
	E_DELAY					= 0.001

	# Commands
	LCD_CLEARDISPLAY        = 0x01
	LCD_RETURNHOME          = 0x02
	LCD_ENTRYMODESET        = 0x04
	LCD_DISPLAYCONTROL      = 0x08
	LCD_CURSORSHIFT         = 0x10
	LCD_FUNCTIONSET         = 0x20
	LCD_SETCGRAMADDR        = 0x40
	LCD_SETDDRAMADDR        = 0x80

	# Display and cursor control
	LCD_DISPLAYMOVE			= 0x08
	LCD_CURSORMOVE			= 0x00
	LCD_MOVERIGHT			= 0x04
	LCD_MOVELEFT			= 0x00
	CURSOR_OFF				= 0x0C
	CURSOR_ON				= 0x0E

	def __init__(self, addr=0x27, port=1):

		self.I2C_ADDR		= addr

		# Open I2C interface
		self.bus = smbus.SMBus(port)
		self.init()

	def init(self):
		# Initialise display
		self.writeByte(0x33) # 110011 Initialise
		self.writeByte(0x32) # 110010 Initialise
		self.writeByte(0x06) # 000110 Cursor move direction
		self.writeByte(self.CURSOR_OFF) # 001100 Cursor Off
		self.writeByte(0x28) # 101000 Data length, number of lines, font size
		self.writeByte(0x01) # 000001 Clear display
		time.sleep(self.E_DELAY)

	def writeByte(self, bits, char=False):

		mode = self.LCD_CMD if char == False else self.LCD_CHR
		bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
		bits_low = mode | ((bits<<4) & 0xF0) | self.LCD_BACKLIGHT

		self.lcd_toggle_enable(bits_high)
		self.lcd_toggle_enable(bits_low)

	def lcd_toggle_enable(self, bits):
			# I don't get this. Can't do anything without it though. I should ask Matt Hawkins some day.
			self.bus.write_byte(self.I2C_ADDR, (bits | self.LCD_DISPLAYON))
			self.bus.write_byte(self.I2C_ADDR, (bits & ~self.LCD_DISPLAYON))

	def toggleBacklight(self, enable=True):

		self.LCD_BACKLIGHT = self.LCD_ON if (enable) else self.LCD_OFF

		bits_high = self.LCD_CMD | (self.CURSOR_OFF & 0xF0) | self.LCD_BACKLIGHT
		bits_low = self.LCD_CMD | ((self.CURSOR_OFF<<4) & 0xF0) | self.LCD_BACKLIGHT

		self.bus.write_byte(self.I2C_ADDR, bits_high)
		self.bus.write_byte(self.I2C_ADDR, bits_low)

	def writeString(self, message, line=0):
		''' Send string to display '''

		# Pad buffer with spaces to overwrite previous string
		message = message.ljust(self.LCD_BUF_WIDTH, ' ')

		# Move cursor to line (0..3)
		self.writeByte(self.LCD_LINES[line])

		for i in range(self.LCD_BUF_WIDTH):
			self.writeByte(ord(message[i]), True)

	def scrollDisplayRight(self):
		''' Scroll display buffer to the right '''
		self.writeByte(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT)

	def scrollDisplayLeft(self):
		''' Scroll display buffer to the left '''
		self.writeByte(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT)

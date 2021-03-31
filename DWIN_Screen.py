import time
import math
import serial
import struct


class T5UIC1_LCD:
	address = 0x2A
	DWIN_BufTail = [0xCC, 0x33, 0xC3, 0x3C]
	DWIN_SendBuf = []
	databuf = [None] * 26
	recnum = 0

	RECEIVED_NO_DATA = 0x00
	RECEIVED_SHAKE_HAND_ACK = 0x01

	FHONE = b'\xAA'

	DWIN_WIDTH = 272
	DWIN_HEIGHT = 480

	# 3-.0：The font size, 0x00-0x09, corresponds to the font size below:
	# 0x00=6*12   0x01=8*16   0x02=10*20  0x03=12*24  0x04=14*28
	# 0x05=16*32  0x06=20*40  0x07=24*48  0x08=28*56  0x09=32*64

	font6x12 = 0x00
	font8x16 = 0x01
	font10x20 = 0x02
	font12x24 = 0x03
	font14x28 = 0x04
	font16x32 = 0x05
	font20x40 = 0x06
	font24x48 = 0x07
	font28x56 = 0x08
	font32x64 = 0x09

	# Color
	Color_White = 0xFFFF
	Color_Yellow = 0xFF0F
	Color_Bg_Window = 0x31E8  # Popup background color
	Color_Bg_Blue = 0x1125  # Dark blue background color
	Color_Bg_Black = 0x0841  # Black background color
	Color_Bg_Red = 0xF00F  # Red background color
	Popup_Text_Color = 0xD6BA  # Popup font background color
	Line_Color = 0x3A6A  # Split line color
	Rectangle_Color = 0xEE2F  # Blue square cursor color
	Percent_Color = 0xFE29  # Percentage color
	BarFill_Color = 0x10E4  # Fill color of progress bar
	Select_Color = 0x33BB  # Selected color

	DWIN_FONT_MENU = font8x16
	DWIN_FONT_STAT = font10x20
	DWIN_FONT_HEAD = font10x20

	# Dwen serial screen initialization
	# Passing parameters: serial port number
	# DWIN screen uses serial port 1 to send
	def __init__(self, USARTx):
		self.MYSERIAL1 = serial.Serial(USARTx, 115200, timeout=1)
		# self.bus = SMBus(1)
		# self.DWIN_SendBuf = self.FHONE
		print("\nDWIN handshake ")
		while not self.Handshake():
			pass
		print("DWIN OK.")
		self.JPG_ShowAndCache(0)
		self.Frame_SetDir(1)
		self.UpdateLCD()

	def Byte(self, bval):
		self.DWIN_SendBuf += int(bval).to_bytes(1, byteorder='big')

	def Word(self, wval):
		self.DWIN_SendBuf += int(wval).to_bytes(2, byteorder='big')

	def Long(self, lval):
		self.DWIN_SendBuf += int(lval).to_bytes(4, byteorder='big')

	def D64(self, value):
		self.DWIN_SendBuf += int(value).to_bytes(8, byteorder='big')

	def String(self, string):
		self.DWIN_SendBuf += string.encode('utf-8')

	# Send the data in the buffer and the packet end
	def Send(self):
		# for i in self.DWIN_BufTail:
		# 	self.Byte(i)
		# self.bus.write_i2c_block_data(self.address, 0, self.DWIN_SendBuf)
		# self.bus.write_i2c_block_data(self.address, 0, self.DWIN_BufTail)

		self.MYSERIAL1.write(self.DWIN_SendBuf)
		self.MYSERIAL1.write(self.DWIN_BufTail)

		self.DWIN_SendBuf = self.FHONE
		time.sleep(0.001)

	def Read(self, lend=1):
		bit = self.bus.read_i2c_block_data(self.address, 0, lend)
		if lend == 1:
			return bytes(bit)
		return bit

	# /*-------------------------------------- System variable function --------------------------------------*/

	# Handshake (1: Success, 0: Fail)
	def Handshake(self):
		i = 0
		self.Byte(0x00)
		self.Send()
		time.sleep(0.1)
		# while (self.recnum < 26):
		while (self.MYSERIAL1.in_waiting and self.recnum < 26):
			# self.databuf[self.recnum] = struct.unpack('B', self.Read())[0]
			self.databuf[self.recnum] = struct.unpack('B', self.MYSERIAL1.read())[0]

			# ignore the invalid data
			if self.databuf[0] != 0xAA:  # prevent the program from running.
				if(self.recnum > 0):
					self.recnum = 0
					self.databuf = [None] * 26
				continue
			time.sleep(.010)
			self.recnum += 1
		return (self.recnum >= 3 and self.databuf[0] == 0xAA and self.databuf[1] == 0 and chr(self.databuf[2]) == 'O' and chr(self.databuf[3]) == 'K')

	# Set the backlight luminance
	#  luminance: (0x00-0xFF)
	def Backlight_SetLuminance(self, luminance):
		self.Byte(0x30)
		self.Byte(_MAX(luminance, 0x1F))
		self.Send()

	# Set screen display direction
	#  dir: 0=0°, 1=90°, 2=180°, 3=270°
	def Frame_SetDir(self, dir):
		self.Byte(0x34)
		self.Byte(0x5A)
		self.Byte(0xA5)
		self.Byte(dir)
		self.Send()

	# Update display
	def UpdateLCD(self):
		self.Byte(0x3D)
		self.Send()

	# /*---------------------------------------- Drawing functions ----------------------------------------*/

	# Clear screen
	#  color: Clear screen color
	def Frame_Clear(self, color):
		self.Byte(0x01)
		self.Word(color)
		self.Send()

	# Draw a point
	#  width: point width   0x01-0x0F
	#  height: point height 0x01-0x0F
	#  x,y: upper left point
	def Draw_Point(self, width, height, x, y):
		self.Byte(0x02)
		self.Byte(width)
		self.Byte(height)
		self.Word(x)
		self.Word(y)
		self.Send()

	# ___________________________________Draw points ____________________________________________\\
	# Command: frame header + command + color of drawing point + pixel size of drawing point (Nx, Ny) + position of drawing point [(X1,Y1)+(X2,Y2)+.........]+ End of frame
	# Set point; processing time=0.4*Nx*Ny*number of set points uS.
	# Color: Set point color.
	# Nx: Actual pixel size in X direction, 0x01-0x0F.
	# Ny: Actual pixel size in Y direction, 0x01-0x0F.
	# (Xn, Yn): Set point coordinate sequence.
	# Example: AA 02 F8 00 04 04 00 08 00 08 CC 33 C3 3C
	# /**************Drawing point protocol command can draw multiple points at a time (this function only draws pixels in one position) ********** *****/
	def DrawPoint(self, Color, Nx, Ny, X1, Y1):			  # Draw some
		self.Byte(0x02)
		self.Word(Color)
		self.Byte(int(Nx))
		self.Byte(int(Ny))
		self.Word(int(X1))
		self.Word(int(Y1))
		self.Send()

	#  Draw a line
	#   color: Line segment color
	#   xStart/yStart: Start point
	#   xEnd/yEnd: End point
	def Draw_Line(self, color, xStart, yStart, xEnd, yEnd):
		self.Byte(0x03)
		self.Word(color)
		self.Word(xStart)
		self.Word(yStart)
		self.Word(xEnd)
		self.Word(yEnd)
		self.Send()

	#  Draw a rectangle
	#   mode: 0=frame, 1=fill, 2=XOR fill
	#   color: Rectangle color
	#   xStart/yStart: upper left point
	#   xEnd/yEnd: lower right point
	def Draw_Rectangle(self, mode, color, xStart, yStart, xEnd, yEnd):
		self.Byte(0x05)
		self.Byte(mode)
		self.Word(color)
		self.Word(xStart)
		self.Word(yStart)
		self.Word(xEnd)
		self.Word(yEnd)
		self.Send()

	#  Move a screen area
	#   mode: 0, circle shift; 1, translation
	#   dir: 0=left, 1=right, 2=up, 3=down
	#   dis: Distance
	#   color: Fill color
	#   xStart/yStart: upper left point
	#   xEnd/yEnd: bottom right point
	def Frame_AreaMove(self, mode, dir, dis, color, xStart, yStart, xEnd, yEnd):
		self.Byte(0x09)
		self.Byte((mode << 7) | dir)
		self.Word(dis)
		self.Word(color)
		self.Word(xStart)
		self.Word(yStart)
		self.Word(xEnd)
		self.Word(yEnd)
		self.Send()

	# ____________________________Draw a circle________________________________\\
	# Color: circle color
	# x0: the abscissa of the center of the circle
	# y0: ordinate of the center of the circle
	# r: circle radius
	def Draw_Circle(self, Color, x0, y0, r):  # Draw a circle
		b = 0
		a = 0
		while(a <= b):
			b = math.sqrt(r * r - a * a)
			while(a == 0):
				b = b - 1
				break
			self.DrawPoint(Color, 1, 1, x0 + a, y0 + b)		               # Draw some sector 1
			self.DrawPoint(Color, 1, 1, x0 + b, y0 + a)		               # Draw some sector 2
			self.DrawPoint(Color, 1, 1, x0 + b, y0 - a)		               # Draw some sector 3
			self.DrawPoint(Color, 1, 1, x0 + a, y0 - b)		               # Draw some sector 4

			self.DrawPoint(Color, 1, 1, x0 - a, y0 - b)		              # Draw some sector 5
			self.DrawPoint(Color, 1, 1, x0 - b, y0 - a)		              # Draw some sector 6
			self.DrawPoint(Color, 1, 1, x0 - b, y0 + a)		              # Draw some sector 7
			self.DrawPoint(Color, 1, 1, x0 - a, y0 + b)		              # Draw some sector 8
			a += 1

	# ____________________________Circular Filling________________________________\\
	# FColor: circle fill color
	# x0: the abscissa of the center of the circle
	# y0: ordinate of the center of the circle
	# r: circle radius
	def CircleFill(self, FColor, x0, y0, r):  # Round filling
		b = 0
		for i in range(r, 0, -1):
			a = 0
			while(a <= b):
				b = math.sqrt(i * i - a * a)
				while(a == 0):
					b = b - 1
					break
				self.DrawPoint(FColor, 2, 2, x0 + a, y0 + b)  # Draw some sector 1
				self.DrawPoint(FColor, 2, 2, x0 + b, y0 + a)  # raw some sector 2
				self.DrawPoint(FColor, 2, 2, x0 + b, y0 - a)  # Draw some sector 3
				self.DrawPoint(FColor, 2, 2, x0 + a, y0 - b)  # Draw some sector 4

				self.DrawPoint(FColor, 2, 2, x0 - a, y0 - b)  # Draw some sector 5
				self.DrawPoint(FColor, 2, 2, x0 - b, y0 - a)  # Draw some sector 6
				self.DrawPoint(FColor, 2, 2, x0 - b, y0 + a)  # Draw some sector 7
				self.DrawPoint(FColor, 2, 2, x0 - a, y0 + b)  # Draw some sector 8
				a = a + 2

	# /*---------------------------------------- Text related functions ----------------------------------------*/

	#  Draw a string
	#   widthAdjust: True=self-adjust character width; False=no adjustment
	#   bShow: True=display background color; False=don't display background color
	#   size: Font size
	#   color: Character color
	#   bColor: Background color
	#   x/y: Upper-left coordinate of the string
	#   *string: The string
	def Draw_String(self, widthAdjust, bShow, size, color, bColor, x, y, string):
		self.Byte(0x11)
		# Bit 7: widthAdjust
		# Bit 6: bShow
		# Bit 5-4: Unused (0)
		# Bit 3-0: size
		self.Byte((widthAdjust * 0x80) | (bShow * 0x40) | size)
		self.Word(color)
		self.Word(bColor)
		self.Word(x)
		self.Word(y)
		self.String(string)
		self.Send()

	#  Draw a positive integer
	#   bShow: True=display background color; False=don't display background color
	#   zeroFill: True=zero fill; False=no zero fill
	#   zeroMode: 1=leading 0 displayed as 0; 0=leading 0 displayed as a space
	#   size: Font size
	#   color: Character color
	#   bColor: Background color
	#   iNum: Number of digits
	#   x/y: Upper-left coordinate
	#   value: Integer value
	def Draw_IntValue(self, bShow, zeroFill, zeroMode, size, color, bColor, iNum, x, y, value):
		self.Byte(0x14)
		# Bit 7: bshow
		# Bit 6: 1 = signed; 0 = unsigned number;
		# Bit 5: zeroFill
		# Bit 4: zeroMode
		# Bit 3-0: size
		self.Byte((bShow * 0x80) | (zeroFill * 0x20) | (zeroMode * 0x10) | size)
		self.Word(color)
		self.Word(bColor)
		self.Byte(iNum)
		self.Byte(0)  # fNum
		self.Word(x)
		self.Word(y)
		self.D64(value)
		self.Send()

	#  Draw a floating point number
	#   bShow: True=display background color; False=don't display background color
	#   zeroFill: True=zero fill; False=no zero fill
	#   zeroMode: 1=leading 0 displayed as 0; 0=leading 0 displayed as a space
	#   size: Font size
	#   color: Character color
	#   bColor: Background color
	#   iNum: Number of whole digits
	#   fNum: Number of decimal digits
	#   x/y: Upper-left point
	#   value: Float value
	def Draw_FloatValue(self, bShow, zeroFill, zeroMode, size, color, bColor, iNum, fNum, x, y, value):
		self.Byte(0x14)
		self.Byte((bShow * 0x80) | (zeroFill * 0x20) | (zeroMode * 0x10) | size)
		self.Word(color)
		self.Word(bColor)
		self.Byte(iNum)
		self.Byte(fNum)
		self.Word(x)
		self.Word(y)
		self.Long(value)
		self.Send()

	def Draw_Signed_Float(self, size, bColor, iNum, fNum, x, y, value):
		if value < 0:
			self.Draw_String(False, True, size, self.Color_White, bColor, x - 6, y, "-")
			self.Draw_FloatValue(True, True, 0, size, self.Color_White, bColor, iNum, fNum, x, y, -value)
		else:
			self.Draw_String(False, True, size, self.Color_White, bColor, x - 6, y, " ")
			self.Draw_FloatValue(True, True, 0, size, self.Color_White, bColor, iNum, fNum, x, y, value)

	# /*---------------------------------------- Picture related functions ----------------------------------------*/

	# Draw JPG and cached in #0 virtual display area
	# id: Picture ID
	def JPG_ShowAndCache(self, id):
		self.Word(0x2200)
		self.Byte(id)
		self.Send()  # AA 23 00 00 00 00 08 00 01 02 03 CC 33 C3 3C

	#  Draw an Icon
	#   libID: Icon library ID
	#   picID: Icon ID
	#   x/y: Upper-left point
	def ICON_Show(self, libID, picID, x, y):
		if x > self.DWIN_WIDTH - 1:
			x = self.DWIN_WIDTH - 1
		if y > self.DWIN_HEIGHT - 1:
			y = self.DWIN_HEIGHT - 1
		self.Byte(0x23)
		self.Word(x)
		self.Word(y)
		self.Byte(0x80 | libID)
		self.Byte(picID)
		self.Send()

	# Unzip the JPG picture to a virtual display area
	#  n: Cache index
	#  id: Picture ID
	def JPG_CacheToN(self, n, id):
		self.Byte(0x25)
		self.Byte(n)
		self.Byte(id)
		self.Send()

	def JPG_CacheTo1(self, id):
		self.JPG_CacheToN(1, id)

	#  Copy area from virtual display area to current screen
	#   cacheID: virtual area number
	#   xStart/yStart: Upper-left of virtual area
	#   xEnd/yEnd: Lower-right of virtual area
	#   x/y: Screen paste point
	def Frame_AreaCopy(self, cacheID, xStart, yStart, xEnd, yEnd, x, y):
		self.Byte(0x27)
		self.Byte(0x80 | cacheID)
		self.Word(xStart)
		self.Word(yStart)
		self.Word(xEnd)
		self.Word(yEnd)
		self.Word(x)
		self.Word(y)
		self.Send()

	def Frame_TitleCopy(self, id, x1, y1, x2, y2):
		self.Frame_AreaCopy(id, x1, y1, x2, y2, 14, 8)

	#  Animate a series of icons
	#   animID: Animation ID; 0x00-0x0F
	#   animate: True on; False off;
	#   libID: Icon library ID
	#   picIDs: Icon starting ID
	#   picIDe: Icon ending ID
	#   x/y: Upper-left point
	#   interval: Display time interval, unit 10mS
	def ICON_Animation(self, animID, animate, libID, picIDs, picIDe, x, y, interval):
		if x > self.DWIN_WIDTH - 1:
			x = self.DWIN_WIDTH - 1
		if y > self.DWIN_HEIGHT - 1:
			y = self.DWIN_HEIGHT - 1
		self.Byte(0x28)
		self.Word(x)
		self.Word(y)
		# Bit 7: animation on or off
		# Bit 6: start from begin or end
		# Bit 5-4: unused (0)
		# Bit 3-0: animID
		self.Byte((animate * 0x80) | 0x40 | animID)
		self.Byte(libID)
		self.Byte(picIDs)
		self.Byte(picIDe)
		self.Byte(interval)
		self.Send()

	#  Animation Control
	#   state: 16 bits, each bit is the state of an animation id
	def ICON_AnimationControl(self, state):
		self.Byte(0x28)
		self.Word(state)
		self.Send()

	# ____________________________Display QR code ________________________________\\
	# QR_Pixel: The pixel size occupied by each point of the QR code: 0x01-0x0F (1-16)
	# (Nx, Ny): The coordinates of the upper left corner displayed by the QR code
	# str: multi-bit data
	# /**************The size of the QR code is (46*QR_Pixel)*(46*QR_Pixle) dot matrix************/
	def QR_Code(self, QR_Pixel, Xs, Ys, data):	    # Display QR code
		self.Byte(0x21)  # Display QR code instruction
		self.Word(Xs)  # Two-dimensional code Xs coordinate high eight
		self.Word(Ys)  # The Ys coordinate of the QR code is eight high

		if(QR_Pixel <= 6):  # Set the upper limit of pixels according to the actual screen size
			self.Byte(QR_Pixel)  # Two-dimensional code pixel size
		else:
			self.Byte(0x06)  # The pixel size of the QR code exceeds the default of 1
		self.String(data)
		self.Send()
	# /*---------------------------------------- Memory functions ----------------------------------------*/
	#  The LCD has an additional 32KB SRAM and 16KB Flash

	#  Data can be written to the sram and save to one of the jpeg page files

	#  Write Data Memory
	#   command 0x31
	#   Type: Write memory selection; 0x5A=SRAM; 0xA5=Flash
	#   Address: Write data memory address; 0x000-0x7FFF for SRAM; 0x000-0x3FFF for Flash
	#   Data: data
	#
	#   Flash writing returns 0xA5 0x4F 0x4B

	#  Read Data Memory
	#   command 0x32
	#   Type: Read memory selection; 0x5A=SRAM; 0xA5=Flash
	#   Address: Read data memory address; 0x000-0x7FFF for SRAM; 0x000-0x3FFF for Flash
	#   Length: leangth of data to read; 0x01-0xF0
	#
	#   Response:
	#     Type, Address, Length, Data

	#  Write Picture Memory
	#   Write the contents of the 32KB SRAM data memory into the designated image memory space
	#   Issued: 0x5A, 0xA5, PIC_ID
	#   Response: 0xA5 0x4F 0x4B
	#
	#   command 0x33
	#   0x5A, 0xA5
	#   PicId: Picture Memory location, 0x00-0x0F
	#
	#   Flash writing returns 0xA5 0x4F 0x4B
	# def sendPicture(self, PicId, SRAM, Address, data):
	# 	self.Byte(0x31)
	# 	if SRAM:
	# 		self.Byte(0x5A)
	# 	else:
	# 		self.Byte(0xA5)
	# 	self.Word(Address)
	# 	self.DWIN_SendBuf += data
	# 	self.Send()

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

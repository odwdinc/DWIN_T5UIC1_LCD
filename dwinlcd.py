import time
import multitimer
import atexit

from encoder import Encoder
from RPi import GPIO

from printerInterface import PrinterData
from DWIN_Screen import T5UIC1_LCD


def current_milli_time():
	return round(time.time() * 1000)


def _MAX(lhs, rhs):
	if lhs > rhs:
		return lhs
	else:
		return rhs


def _MIN(lhs, rhs):
	if lhs < rhs:
		return lhs
	else:
		return rhs


class select_t:
	now = 0
	last = 0

	def set(self, v):
		self.now = self.last = v

	def reset(self):
		self.set(0)

	def changed(self):
		c = (self.now != self.last)
		if c:
			self.last = self.now
			return c

	def dec(self):
		if (self.now):
			self.now -= 1
		return self.changed()

	def inc(self, v):
		if (self.now < (v - 1)):
			self.now += 1
		else:
			self.now = (v - 1)
		return self.changed()


class DWIN_LCD:

	TROWS = 6
	MROWS = TROWS - 1  # Total rows, and other-than-Back
	TITLE_HEIGHT = 30  # Title bar height
	MLINE = 53         # Menu line height
	LBLX = 60          # Menu item label X
	MENU_CHR_W = 8
	STAT_CHR_W = 10

	dwin_abort_flag = False  # Flag to reset feedrate, return to Home

	MSG_STOP_PRINT = "Stop Print"
	MSG_PAUSE_PRINT = "Pausing..."

	DWIN_SCROLL_UP = 2
	DWIN_SCROLL_DOWN = 3

	select_page = select_t()
	select_file = select_t()
	select_print = select_t()
	select_prepare = select_t()

	select_control = select_t()
	select_axis = select_t()
	select_temp = select_t()
	select_motion = select_t()
	select_tune = select_t()
	select_PLA = select_t()
	select_ABS = select_t()

	index_file = MROWS
	index_prepare = MROWS
	index_control = MROWS
	index_leveling = MROWS
	index_tune = MROWS

	MainMenu = 0
	SelectFile = 1
	Prepare = 2
	Control = 3
	Leveling = 4
	PrintProcess = 5
	AxisMove = 6
	TemperatureID = 7
	Motion = 8
	Info = 9
	Tune = 10
	PLAPreheat = 11
	ABSPreheat = 12
	MaxSpeed = 13
	MaxSpeed_value = 14
	MaxAcceleration = 15
	MaxAcceleration_value = 16
	MaxJerk = 17
	MaxJerk_value = 18
	Step = 19
	Step_value = 20

	# Last Process ID
	Last_Prepare = 21

	# Back Process ID
	Back_Main = 22
	Back_Print = 23

	# Date variable ID
	Move_X = 24
	Move_Y = 25
	Move_Z = 26
	Extruder = 27
	ETemp = 28
	Homeoffset = 29
	BedTemp = 30
	FanSpeed = 31
	PrintSpeed = 32

	Print_window = 33
	Popup_Window = 34

	MINUNITMULT = 10

	ENCODER_DIFF_NO = 0  # no state
	ENCODER_DIFF_CW = 1  # clockwise rotation
	ENCODER_DIFF_CCW = 2  # counterclockwise rotation
	ENCODER_DIFF_ENTER = 3   # click
	ENCODER_WAIT = 80
	ENCODER_WAIT_ENTER = 300
	EncoderRateLimit = True


	dwin_zoffset = 0.0
	last_zoffset = 0.0

	# Picture ID
	Start_Process = 0
	Language_English = 1
	Language_Chinese = 2

	# ICON ID
	ICON = 0x09

	ICON_LOGO = 0
	ICON_Print_0 = 1
	ICON_Print_1 = 2
	ICON_Prepare_0 = 3
	ICON_Prepare_1 = 4
	ICON_Control_0 = 5
	ICON_Control_1 = 6
	ICON_Leveling_0 = 7
	ICON_Leveling_1 = 8
	ICON_HotendTemp = 9
	ICON_BedTemp = 10
	ICON_Speed = 11
	ICON_Zoffset = 12
	ICON_Back = 13
	ICON_File = 14
	ICON_PrintTime = 15
	ICON_RemainTime = 16
	ICON_Setup_0 = 17
	ICON_Setup_1 = 18
	ICON_Pause_0 = 19
	ICON_Pause_1 = 20
	ICON_Continue_0 = 21
	ICON_Continue_1 = 22
	ICON_Stop_0 = 23
	ICON_Stop_1 = 24
	ICON_Bar = 25
	ICON_More = 26

	ICON_Axis = 27
	ICON_CloseMotor = 28
	ICON_Homing = 29
	ICON_SetHome = 30
	ICON_PLAPreheat = 31
	ICON_ABSPreheat = 32
	ICON_Cool = 33
	ICON_Language = 34

	ICON_MoveX = 35
	ICON_MoveY = 36
	ICON_MoveZ = 37
	ICON_Extruder = 38

	ICON_Temperature = 40
	ICON_Motion = 41
	ICON_WriteEEPROM = 42
	ICON_ReadEEPROM = 43
	ICON_ResumeEEPROM = 44
	ICON_Info = 45

	ICON_SetEndTemp = 46
	ICON_SetBedTemp = 47
	ICON_FanSpeed = 48
	ICON_SetPLAPreheat = 49
	ICON_SetABSPreheat = 50

	ICON_MaxSpeed = 51
	ICON_MaxAccelerated = 52
	ICON_MaxJerk = 53
	ICON_Step = 54
	ICON_PrintSize = 55
	ICON_Version = 56
	ICON_Contact = 57
	ICON_StockConfiguraton = 58
	ICON_MaxSpeedX = 59
	ICON_MaxSpeedY = 60
	ICON_MaxSpeedZ = 61
	ICON_MaxSpeedE = 62
	ICON_MaxAccX = 63
	ICON_MaxAccY = 64
	ICON_MaxAccZ = 65
	ICON_MaxAccE = 66
	ICON_MaxSpeedJerkX = 67
	ICON_MaxSpeedJerkY = 68
	ICON_MaxSpeedJerkZ = 69
	ICON_MaxSpeedJerkE = 70
	ICON_StepX = 71
	ICON_StepY = 72
	ICON_StepZ = 73
	ICON_StepE = 74
	ICON_Setspeed = 75
	ICON_SetZOffset = 76
	ICON_Rectangle = 77
	ICON_BLTouch = 78
	ICON_TempTooLow = 79
	ICON_AutoLeveling = 80
	ICON_TempTooHigh = 81
	ICON_NoTips_C = 82
	ICON_NoTips_E = 83
	ICON_Continue_C = 84
	ICON_Continue_E = 85
	ICON_Cancel_C = 86
	ICON_Cancel_E = 87
	ICON_Confirm_C = 88
	ICON_Confirm_E = 89
	ICON_Info_0 = 90
	ICON_Info_1 = 91

	MENU_CHAR_LIMIT = 24
	STATUS_Y = 360

	MOTION_CASE_RATE = 1
	MOTION_CASE_ACCEL = 2
	MOTION_CASE_JERK = MOTION_CASE_ACCEL + 0
	MOTION_CASE_STEPS = MOTION_CASE_JERK + 1
	MOTION_CASE_TOTAL = MOTION_CASE_STEPS

	PREPARE_CASE_MOVE = 1
	PREPARE_CASE_DISA = 2
	PREPARE_CASE_HOME = 3
	PREPARE_CASE_ZOFF = PREPARE_CASE_HOME + 1
	PREPARE_CASE_PLA = PREPARE_CASE_ZOFF + 1
	PREPARE_CASE_ABS = PREPARE_CASE_PLA + 1
	PREPARE_CASE_COOL = PREPARE_CASE_ABS + 1
	PREPARE_CASE_LANG = PREPARE_CASE_COOL + 0
	PREPARE_CASE_TOTAL = PREPARE_CASE_LANG

	CONTROL_CASE_TEMP = 1
	CONTROL_CASE_MOVE = 2
	CONTROL_CASE_INFO = 3
	CONTROL_CASE_TOTAL = 3

	TUNE_CASE_SPEED = 1
	TUNE_CASE_TEMP = (TUNE_CASE_SPEED + 1)
	TUNE_CASE_BED = (TUNE_CASE_TEMP + 1)
	TUNE_CASE_FAN = (TUNE_CASE_BED + 0)
	TUNE_CASE_ZOFF = (TUNE_CASE_FAN + 1)
	TUNE_CASE_TOTAL = TUNE_CASE_ZOFF

	TEMP_CASE_TEMP = (0 + 1)
	TEMP_CASE_BED = (TEMP_CASE_TEMP + 1)
	TEMP_CASE_FAN = (TEMP_CASE_BED + 0)
	TEMP_CASE_PLA = (TEMP_CASE_FAN + 1)
	TEMP_CASE_ABS = (TEMP_CASE_PLA + 1)
	TEMP_CASE_TOTAL = TEMP_CASE_ABS

	PREHEAT_CASE_TEMP = (0 + 1)
	PREHEAT_CASE_BED = (PREHEAT_CASE_TEMP + 1)
	PREHEAT_CASE_FAN = (PREHEAT_CASE_BED + 0)
	PREHEAT_CASE_SAVE = (PREHEAT_CASE_FAN + 1)
	PREHEAT_CASE_TOTAL = PREHEAT_CASE_SAVE

	# Dwen serial screen initialization
	# Passing parameters: serial port number
	# DWIN screen uses serial port 1 to send
	def __init__(self, USARTx, encoder_pins, button_pin, octoPrint_API_Key):
		GPIO.setmode(GPIO.BCM)
		self.encoder = Encoder(encoder_pins[0], encoder_pins[1])
		self.button_pin = button_pin
		GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(self.button_pin, GPIO.BOTH, callback=self.encoder_has_data)
		self.encoder.callback = self.encoder_has_data
		self.EncodeLast = 0
		self.EncodeMS = current_milli_time() + self.ENCODER_WAIT
		self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
		self.next_rts_update_ms = 0
		self.last_cardpercentValue = 101
		self.lcd = T5UIC1_LCD(USARTx)
		self.checkkey = self.MainMenu
		self.pd = PrinterData(octoPrint_API_Key)
		self.timer = multitimer.MultiTimer(interval=2, function=self.EachMomentUpdate)
		self.HMI_ShowBoot()
		print("Boot looks good")
		print("Testing Web-services")
		self.pd.init_Webservices()
		while self.pd.status is None:
			print("No Web-services")
			self.pd.init_Webservices()
			self.HMI_ShowBoot("Web-service still loading")
		self.HMI_Init()
		self.HMI_StartFrame(False)

	def lcdExit(self):
		print("Shutting down the LCD")
		self.lcd.JPG_ShowAndCache(0)
		self.lcd.Frame_SetDir(1)
		self.lcd.UpdateLCD()
		self.timer.stop()
		GPIO.remove_event_detect(self.button_pin)

	def MBASE(self, L):
		return 49 + self.MLINE * L

	def HMI_SetLanguageCache(self):
		self.lcd.JPG_CacheTo1(self.Language_English)

	def HMI_SetLanguage(self):
		self.HMI_SetLanguageCache()

	def HMI_ShowBoot(self, mesg=None):
		if mesg:
			self.lcd.Draw_String(
				False, False, self.lcd.DWIN_FONT_STAT,
				self.lcd.Color_White, self.lcd.Color_Bg_Black,
				10, 50,
				mesg
			)
		for t in range(0, 100, 2):
			self.lcd.ICON_Show(self.ICON, self.ICON_Bar, 15, 260)
			self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 15 + t * 242 / 100, 260, 257, 280)
			self.lcd.UpdateLCD()
			time.sleep(.020)

	def HMI_Init(self):
		# HMI_SDCardInit()

		self.HMI_SetLanguage()
		self.timer.start()
		atexit.register(self.lcdExit)

	def HMI_StartFrame(self, with_update):
		self.last_status = self.pd.status
		if self.pd.status == 'printing':
			self.Goto_PrintProcess()
		elif self.pd.status in ['operational', 'complete', 'standby', 'cancelled']:
			self.Goto_MainMenu()
		else:
			self.Goto_MainMenu()
		self.Draw_Status_Area(with_update)

	def HMI_MainMenu(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if(self.select_page.inc(4)):
				if self.select_page.now == 0:
					self.ICON_Print()
				if self.select_page.now == 1:
					self.ICON_Print()
					self.ICON_Prepare()
				if self.select_page.now == 2:
					self.ICON_Prepare()
					self.ICON_Control()
				if self.select_page.now == 3:
					self.ICON_Control()
					if self.pd.HAS_ONESTEP_LEVELING:
						self.ICON_Leveling(True)
					else:
						self.ICON_StartInfo(True)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_page.dec()):
				if self.select_page.now == 0:
					self.ICON_Print()
					self.ICON_Prepare()
				elif self.select_page.now == 1:
					self.ICON_Prepare()
					self.ICON_Control()
				elif self.select_page.now == 2:
					self.ICON_Control()
					if self.pd.HAS_ONESTEP_LEVELING:
						self.ICON_Leveling(False)
					else:
						self.ICON_StartInfo(False)
				elif self.select_page.now == 3:
					if self.pd.HAS_ONESTEP_LEVELING:
						self.ICON_Leveling(True)
					else:
						self.ICON_StartInfo(True)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_page.now == 0:  # Print File
				self.checkkey = self.SelectFile
				self.Draw_Print_File_Menu()
			if self.select_page.now == 1:  # Prepare
				self.checkkey = self.Prepare
				self.select_prepare.reset()
				self.index_prepare = self.MROWS
				self.Draw_Prepare_Menu()
			if self.select_page.now == 2:  # Control
				self.checkkey = self.Control
				self.select_control.reset()
				self.index_control = self.MROWS
				self.Draw_Control_Menu()
			if self.select_page.now == 3:  # Leveling or Info
				if self.pd.HAS_ONESTEP_LEVELING:
					self.checkkey = self.Leveling
					self.HMI_Leveling()
				else:
					self.checkkey = self.Info
					self.Draw_Info_Menu()

		self.lcd.UpdateLCD()

	def HMI_SelectFile(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		fullCnt = len(self.pd.GetFiles(refresh=True))

		if (encoder_diffState == self.ENCODER_DIFF_CW and fullCnt):
			if (self.select_file.inc(1 + fullCnt)):
				itemnum = self.select_file.now - 1  # -1 for "Back"
				if (self.select_file.now > self.MROWS and self.select_file.now > self.index_file):  # Cursor past the bottom
					self.index_file = self.select_file.now  # New bottom line
					self.Scroll_Menu(self.DWIN_SCROLL_UP)
					self.Draw_SDItem(itemnum, self.MROWS)  # Draw and init the shift name
				else:
					self.Move_Highlight(1, self.select_file.now + self.MROWS - self.index_file)  # Just move highlight
		elif (encoder_diffState == self.ENCODER_DIFF_CCW and fullCnt):
			if (self.select_file.dec()):
				itemnum = self.select_file.now - 1  # -1 for "Back"
				if (self.select_file.now < self.index_file - self.MROWS):  # Cursor past the top
					self.index_file -= 1  # New bottom line
					self.Scroll_Menu(self.DWIN_SCROLL_DOWN)
					if (self.index_file == self.MROWS):
						self.Draw_Back_First()
					else:
						self.Draw_SDItem(itemnum, 0)  # Draw the item (and init shift name)
				else:
					self.Move_Highlight(-1, self.select_file.now + self.MROWS - self.index_file)  # Just move highlight
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if (self.select_file.now == 0):  # Back
				self.select_page.set(0)
				self.Goto_MainMenu()
			else:
				filenum = self.select_file.now - 1
				# Reset highlight for next entry
				self.select_print.reset()
				self.select_file.reset()

				# // Start choice and print SD file
				self.pd.HMI_flag.heat_flag = True
				self.pd.HMI_flag.print_finish = False
				self.pd.HMI_ValueStruct.show_mode = 0

				self.pd.openAndPrintFile(filenum)
				self.Goto_PrintProcess()

		self.lcd.UpdateLCD()

	def HMI_Prepare(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_prepare.inc(1 + self.PREPARE_CASE_TOTAL)):
				if (self.select_prepare.now > self.MROWS and self.select_prepare.now > self.index_prepare):
					self.index_prepare = self.select_prepare.now

					# Scroll up and draw a blank bottom line
					self.Scroll_Menu(self.DWIN_SCROLL_UP)
					self.Draw_Menu_Icon(self.MROWS, self.ICON_Axis + self.select_prepare.now - 1)

					# Draw "More" icon for sub-menus
					if (self.index_prepare < 7):
						self.Draw_More_Icon(self.MROWS - self.index_prepare + 1)

					if self.pd.HAS_HOTEND:
						if (self.index_prepare == self.PREPARE_CASE_ABS):
							self.Item_Prepare_ABS(self.MROWS)
					if self.pd.HAS_PREHEAT:
						if (self.index_prepare == self.PREPARE_CASE_COOL):
							self.Item_Prepare_Cool(self.MROWS)
				else:
					self.Move_Highlight(1, self.select_prepare.now + self.MROWS - self.index_prepare)

		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_prepare.dec()):
				if (self.select_prepare.now < self.index_prepare - self.MROWS):
					self.index_prepare -= 1
					self.Scroll_Menu(self.DWIN_SCROLL_DOWN)

					if (self.index_prepare == self.MROWS):
						self.Draw_Back_First()
					else:
						self.Draw_Menu_Line(0, self.ICON_Axis + self.select_prepare.now - 1)

					if (self.index_prepare < 7):
						self.Draw_More_Icon(self.MROWS - self.index_prepare + 1)

					if (self.index_prepare == 6):
						self.Item_Prepare_Move(0)
					elif (self.index_prepare == 7):
						self.Item_Prepare_Disable(0)
					elif (self.index_prepare == 8):
						self.Item_Prepare_Home(0)
				else:
					self.Move_Highlight(-1, self.select_prepare.now + self.MROWS - self.index_prepare)

		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if (self.select_prepare.now == 0):  # Back
				self.select_page.set(1)
				self.Goto_MainMenu()

			elif self.select_prepare.now == self.PREPARE_CASE_MOVE:  # Axis move
				self.checkkey = self.AxisMove
				self.select_axis.reset()
				self.Draw_Move_Menu()
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 1, 216, self.MBASE(1), self.pd.current_position.x * self.MINUNITMULT
				)
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 1, 216, self.MBASE(2), self.pd.current_position.y * self.MINUNITMULT
				)
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 1, 216, self.MBASE(3), self.pd.current_position.z * self.MINUNITMULT
				)
				self.pd.sendGCode("G92 E0")
				self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale = 0
				self.lcd.Draw_Signed_Float(self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216, self.MBASE(4), 0)
			elif self.select_prepare.now == self.PREPARE_CASE_DISA:  # Disable steppers
				self.pd.sendGCode("M84")
			elif self.select_prepare.now == self.PREPARE_CASE_HOME:  # Homing
				self.checkkey = self.Last_Prepare
				self.index_prepare = self.MROWS
				self.pd.current_position.homing()
				self.pd.HMI_flag.home_flag = True
				self.Popup_Window_Home()
				self.pd.sendGCode("G28")
			elif self.select_prepare.now == self.PREPARE_CASE_ZOFF:  # Z-offset
				self.checkkey = self.Homeoffset
				if self.pd.HAS_BED_PROBE:
					self.pd.probe_calibrate()

				self.pd.HMI_ValueStruct.show_mode = -4

				self.lcd.Draw_Signed_Float(
					self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
					self.MBASE(self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare),
					self.pd.HMI_ValueStruct.offset_value
				)
				self.EncoderRateLimit = False

			elif self.select_prepare.now == self.PREPARE_CASE_PLA:  # PLA preheat
				self.pd.preheat("PLA")

			elif self.select_prepare.now == self.PREPARE_CASE_ABS:  # ABS preheat
				self.pd.preheat("ABS")

			elif self.select_prepare.now == self.PREPARE_CASE_COOL:  # Cool
				if self.pd.HAS_FAN:
					self.pd.zero_fan_speeds()
				self.pd.disable_all_heaters()

			elif self.select_prepare.now == self.PREPARE_CASE_LANG:  # Toggle Language
				self.HMI_ToggleLanguage()
				self.Draw_Prepare_Menu()
		self.lcd.UpdateLCD()

	def HMI_Control(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_control.inc(1 + self.CONTROL_CASE_TOTAL)):
				if (self.select_control.now > self.MROWS and self.select_control.now > self.index_control):
					self.index_control = self.select_control.now
					self.Scroll_Menu(self.DWIN_SCROLL_UP)
					self.Draw_Menu_Icon(self.MROWS, self.ICON_Temperature + self.index_control - 1)
					self.Draw_More_Icon(self.CONTROL_CASE_TEMP + self.MROWS - self.index_control)  # Temperature >
					self.Draw_More_Icon(self.CONTROL_CASE_MOVE + self.MROWS - self.index_control)  # Motion >
					if (self.index_control > self.MROWS):
						self.Draw_More_Icon(self.CONTROL_CASE_INFO + self.MROWS - self.index_control)  # Info >
						self.lcd.Frame_AreaCopy(1, 0, 104, 24, 114, self.LBLX, self.MBASE(self.CONTROL_CASE_INFO - 1))
				else:
					self.Move_Highlight(1, self.select_control.now + self.MROWS - self.index_control)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_control.dec()):
				if (self.select_control.now < self.index_control - self.MROWS):
					self.index_control -= 1
					self.Scroll_Menu(self.DWIN_SCROLL_DOWN)
					if (self.index_control == self.MROWS):
						self.Draw_Back_First()
					else:
						self.Draw_Menu_Line(0, self.ICON_Temperature + self.select_control.now - 1)
					self.Draw_More_Icon(0 + self.MROWS - self.index_control + 1)  # Temperature >
					self.Draw_More_Icon(1 + self.MROWS - self.index_control + 1)  # Motion >
				else:
					self.Move_Highlight(-1, self.select_control.now + self.MROWS - self.index_control)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if (self.select_control.now == 0):  # Back
				self.select_page.set(2)
				self.Goto_MainMenu()
			if (self.select_control.now == self.CONTROL_CASE_TEMP):  # Temperature
				self.checkkey = self.TemperatureID
				self.pd.HMI_ValueStruct.show_mode = -1
				self.select_temp.reset()
				self.Draw_Temperature_Menu()
			if (self.select_control.now == self.CONTROL_CASE_MOVE):  # Motion
				self.checkkey = self.Motion
				self.select_motion.reset()
				self.Draw_Motion_Menu()
			if (self.select_control.now == self.CONTROL_CASE_INFO):  # Info
				self.checkkey = self.Info
				self.Draw_Info_Menu()

		self.lcd.UpdateLCD()

	def HMI_Info(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.pd.HAS_ONESTEP_LEVELING:
				self.checkkey = self.Control
				self.select_control.set(self.CONTROL_CASE_INFO)
				self.Draw_Control_Menu()
			else:
				self.select_page.set(3)
				self.Goto_MainMenu()
		self.lcd.UpdateLCD()

	def HMI_Printing(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (self.pd.HMI_flag.done_confirm_flag):
			if (encoder_diffState == self.ENCODER_DIFF_ENTER):
				self.pd.HMI_flag.done_confirm_flag = False
				self.dwin_abort_flag = True  # Reset feedrate, return to Home
			return

		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_print.inc(3)):
				if self.select_print.now == 0:
					self.ICON_Tune()
				elif self.select_print.now == 1:
					self.ICON_Tune()
					if (self.pd.printingIsPaused()):
						self.ICON_Continue()
					else:
						self.ICON_Pause()
				elif self.select_print.now == 2:
					if (self.pd.printingIsPaused()):
						self.ICON_Continue()
					else:
						self.ICON_Pause()
					self.ICON_Stop()
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_print.dec()):
				if self.select_print.now == 0:
					self.ICON_Tune()
					if (self.pd.printingIsPaused()):
						self.ICON_Continue()
					else:
						self.ICON_Pause()
				elif self.select_print.now == 1:
					if (self.pd.printingIsPaused()):
						self.ICON_Continue()
					else:
						self.ICON_Pause()
					self.ICON_Stop()
				elif self.select_print.now == 2:
					self.ICON_Stop()
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_print.now == 0:  # Tune
				self.checkkey = self.Tune
				self.pd.HMI_ValueStruct.show_mode = 0
				self.select_tune.reset()
				self.index_tune = self.MROWS
				self.Draw_Tune_Menu()
			elif self.select_print.now == 1:  # Pause
				if (self.pd.HMI_flag.pause_flag):
					self.ICON_Pause()
					self.pd.resume_job()
				else:
					self.pd.HMI_flag.select_flag = True
					self.checkkey = self.Print_window
					self.Popup_window_PauseOrStop()
			elif self.select_print.now == 2:  # Stop
				self.pd.HMI_flag.select_flag = True
				self.checkkey = self.Print_window
				self.Popup_window_PauseOrStop()
		self.lcd.UpdateLCD()

	# Pause and Stop window */
	def HMI_PauseOrStop(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (encoder_diffState == self.ENCODER_DIFF_CW):
			self.Draw_Select_Highlight(False)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.Draw_Select_Highlight(True)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if (self.select_print.now == 1):  # pause window
				if (self.pd.HMI_flag.select_flag):
					self.pd.HMI_flag.pause_action = True
					self.ICON_Continue()
					self.pd.pause_job()
				self.Goto_PrintProcess()
			elif (self.select_print.now == 2):  # stop window
				if (self.pd.HMI_flag.select_flag):
					self.dwin_abort_flag = True  # Reset feedrate, return to Home
					self.pd.cancel_job()
					self.Goto_MainMenu()
				else:
					self.Goto_PrintProcess()  # cancel stop
		self.lcd.UpdateLCD()

	# Tune  */
	def HMI_Tune(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_tune.inc(1 + self.TUNE_CASE_TOTAL)):
				if (self.select_tune.now > self.MROWS and self.select_tune.now > self.index_tune):
					self.index_tune = self.select_tune.now
					self.Scroll_Menu(self.DWIN_SCROLL_UP)
				else:
					self.Move_Highlight(1, self.select_tune.now + self.MROWS - self.index_tune)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_tune.dec()):
				if (self.select_tune.now < self.index_tune - self.MROWS):
					self.index_tune -= 1
					self.Scroll_Menu(self.DWIN_SCROLL_DOWN)
					if (self.index_tune == self.MROWS):
						self.Draw_Back_First()
				else:
					self.Move_Highlight(-1, self.select_tune.now + self.MROWS - self.index_tune)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_tune.now == 0:  # Back
				self.select_print.set(0)
				self.Goto_PrintProcess()
			elif self.select_tune.now == self.TUNE_CASE_SPEED:  # Print speed
				self.checkkey = self.PrintSpeed
				self.pd.HMI_ValueStruct.print_speed = self.pd.feedrate_percentage
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.TUNE_CASE_SPEED + self.MROWS - self.index_tune),
					self.pd.feedrate_percentage
				)
				self.EncoderRateLimit = False
			elif self.select_tune.now == self.TUNE_CASE_ZOFF:   #z offset
				self.checkkey = self.Homeoffset
				self.lcd.Draw_Signed_Float(
					self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
					self.MBASE(self.TUNE_CASE_ZOFF + self.MROWS - self.index_tune),
					self.pd.HMI_ValueStruct.offset_value
				)

		self.lcd.UpdateLCD()

	def HMI_PrintSpeed(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.print_speed += 1

		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.print_speed -= 1

		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.checkkey = self.Tune
			self.encoderRate = True
			self.pd.set_feedrate(self.pd.HMI_ValueStruct.print_speed)

		self.lcd.Draw_IntValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
			3, 216, self.MBASE(self.select_tune.now + self.MROWS - self.index_tune),
			self.pd.HMI_ValueStruct.print_speed
		)

	def HMI_AxisMove(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if self.pd.PREVENT_COLD_EXTRUSION:
			# popup window resume
			if (self.pd.HMI_flag.ETempTooLow_flag):
				if (encoder_diffState == self.ENCODER_DIFF_ENTER):
					self.pd.HMI_flag.ETempTooLow_flag = False
					self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale = 0
					self.Draw_Move_Menu()
					self.lcd.Draw_FloatValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 1, 216, self.MBASE(1),
						self.pd.HMI_ValueStruct.Move_X_scale
					)
					self.lcd.Draw_FloatValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 1, 216, self.MBASE(2),
						self.pd.HMI_ValueStruct.Move_Y_scale
					)
					self.lcd.Draw_FloatValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 1, 216, self.MBASE(3),
						self.pd.HMI_ValueStruct.Move_Z_scale
					)
					self.lcd.Draw_Signed_Float(
						self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216, self.MBASE(4), 0
					)
					self.lcd.UpdateLCD()
				return
		# Avoid flicker by updating only the previous menu
		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_axis.inc(1 + 4)):
				self.Move_Highlight(1, self.select_axis.now)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_axis.dec()):
				self.Move_Highlight(-1, self.select_axis.now)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_axis.now == 0:  # Back
				self.checkkey = self.Prepare
				self.select_prepare.set(1)
				self.index_prepare = self.MROWS
				self.Draw_Prepare_Menu()

			elif self.select_axis.now == 1:  # axis move
				self.checkkey = self.Move_X
				self.pd.HMI_ValueStruct.Move_X_scale = self.pd.current_position.x * self.MINUNITMULT
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 1, 216, self.MBASE(1),
					self.pd.HMI_ValueStruct.Move_X_scale
				)
				self.EncoderRateLimit = False
			elif self.select_axis.now == 2:  # Y axis move
				self.checkkey = self.Move_Y
				self.pd.HMI_ValueStruct.Move_Y_scale = self.pd.current_position.y * self.MINUNITMULT
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 1, 216, self.MBASE(2),
					self.pd.HMI_ValueStruct.Move_Y_scale
				)
				self.EncoderRateLimit = False
			elif self.select_axis.now == 3:  # Z axis move
				self.checkkey = self.Move_Z
				self.pd.HMI_ValueStruct.Move_Z_scale = self.pd.current_position.z * self.MINUNITMULT
				self.lcd.Draw_FloatValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 1, 216, self.MBASE(3),
					self.pd.HMI_ValueStruct.Move_Z_scale
				)
				self.EncoderRateLimit = False
			elif self.select_axis.now == 4:  # Extruder
				# window tips
				if self.pd.PREVENT_COLD_EXTRUSION:
					if (self.pd.thermalManager['temp_hotend'][0]['celsius'] < self.pd.EXTRUDE_MINTEMP):
						self.pd.HMI_flag.ETempTooLow_flag = True
						self.Popup_Window_ETempTooLow()
						self.lcd.UpdateLCD()
						return
				self.checkkey = self.Extruder
				self.pd.HMI_ValueStruct.Move_E_scale = self.pd.current_position.e * self.MINUNITMULT
				self.lcd.Draw_Signed_Float(
					self.lcd.font8x16, self.lcd.Select_Color, 3, 1, 216, self.MBASE(4),
					self.pd.HMI_ValueStruct.Move_E_scale
				)
				self.EncoderRateLimit = False
		self.lcd.UpdateLCD()

	def HMI_Move_X(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.checkkey = self.AxisMove
			self.EncoderRateLimit = True
			self.lcd.Draw_FloatValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 1, 216, self.MBASE(1),
				self.pd.HMI_ValueStruct.Move_X_scale
			)
			self.pd.moveAbsolute('X',self.pd.current_position.x, 5000)
			self.lcd.UpdateLCD()
			return
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.Move_X_scale += 1
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.Move_X_scale -= 1

		if self.pd.HMI_ValueStruct.Move_X_scale < (self.pd.X_MIN_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_X_scale = (self.pd.X_MIN_POS) * self.MINUNITMULT

		if self.pd.HMI_ValueStruct.Move_X_scale > (self.pd.X_MAX_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_X_scale = (self.pd.X_MAX_POS) * self.MINUNITMULT

		self.pd.current_position.x = self.pd.HMI_ValueStruct.Move_X_scale / 10
		self.lcd.Draw_FloatValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
			3, 1, 216, self.MBASE(1), self.pd.HMI_ValueStruct.Move_X_scale)
		self.lcd.UpdateLCD()

	def HMI_Move_Y(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.checkkey = self.AxisMove
			self.EncoderRateLimit = True
			self.lcd.Draw_FloatValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 1, 216, self.MBASE(2),
				self.pd.HMI_ValueStruct.Move_Y_scale
			)

			self.pd.moveAbsolute('Y',self.pd.current_position.y, 5000)
			self.lcd.UpdateLCD()
			return
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.Move_Y_scale += 1
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.Move_Y_scale -= 1

		if self.pd.HMI_ValueStruct.Move_Y_scale < (self.pd.Y_MIN_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_Y_scale = (self.pd.Y_MIN_POS) * self.MINUNITMULT

		if self.pd.HMI_ValueStruct.Move_Y_scale > (self.pd.Y_MAX_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_Y_scale = (self.pd.Y_MAX_POS) * self.MINUNITMULT

		self.pd.current_position.y = self.pd.HMI_ValueStruct.Move_Y_scale / 10
		self.lcd.Draw_FloatValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
			3, 1, 216, self.MBASE(2), self.pd.HMI_ValueStruct.Move_Y_scale)
		self.lcd.UpdateLCD()

	def HMI_Move_Z(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.checkkey = self.AxisMove
			self.EncoderRateLimit = True
			self.lcd.Draw_FloatValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 1, 216, self.MBASE(3),
				self.pd.HMI_ValueStruct.Move_Z_scale
			)
			self.pd.moveAbsolute('Z',self.pd.current_position.z, 600)
			self.lcd.UpdateLCD()
			return
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.Move_Z_scale += 1
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.Move_Z_scale -= 1

		if self.pd.HMI_ValueStruct.Move_Z_scale < (self.pd.Z_MIN_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_Z_scale = (self.pd.Z_MIN_POS) * self.MINUNITMULT

		if self.pd.HMI_ValueStruct.Move_Z_scale > (self.pd.Z_MAX_POS) * self.MINUNITMULT:
			self.pd.HMI_ValueStruct.Move_Z_scale = (self.pd.Z_MAX_POS) * self.MINUNITMULT

		self.pd.current_position.z = self.pd.HMI_ValueStruct.Move_Z_scale / 10
		self.lcd.Draw_FloatValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
			3, 1, 216, self.MBASE(3), self.pd.HMI_ValueStruct.Move_Z_scale)
		self.lcd.UpdateLCD()

	def HMI_Move_E(self):
		self.pd.last_E_scale = 0
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.checkkey = self.AxisMove
			self.EncoderRateLimit = True
			self.pd.last_E_scale = self.pd.HMI_ValueStruct.Move_E_scale
			self.lcd.Draw_Signed_Float(
				self.lcd.font8x16, self.lcd.Color_Bg_Black, 3, 1, 216,
				self.MBASE(4), self.pd.HMI_ValueStruct.Move_E_scale
			)
			self.pd.moveAbsolute('E',self.pd.current_position.e, 300)
			self.lcd.UpdateLCD()
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.Move_E_scale += 1
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.Move_E_scale -= 1

		if ((self.pd.HMI_ValueStruct.Move_E_scale - self.pd.last_E_scale) > (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT):
			self.pd.HMI_ValueStruct.Move_E_scale = self.pd.last_E_scale + (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT
		elif ((self.pd.last_E_scale - self.pd.HMI_ValueStruct.Move_E_scale) > (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT):
			self.pd.HMI_ValueStruct.Move_E_scale = self.pd.last_E_scale - (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT
		self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale / 10
		self.lcd.Draw_Signed_Float(self.lcd.font8x16, self.lcd.Select_Color, 3, 1, 216, self.MBASE(4), self.pd.HMI_ValueStruct.Move_E_scale)
		self.lcd.UpdateLCD()

	def HMI_Temperature(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_temp.inc(1 + self.TEMP_CASE_TOTAL)):
				self.Move_Highlight(1, self.select_temp.now)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_temp.dec()):
				self.Move_Highlight(-1, self.select_temp.now)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_temp.now == 0:  # back
				self.checkkey = self.Control
				self.select_control.set(1)
				self.index_control = self.MROWS
				self.Draw_Control_Menu()
			elif self.select_temp.now == self.TEMP_CASE_TEMP:  # Nozzle temperature
				self.checkkey = self.ETemp
				self.pd.HMI_ValueStruct.E_Temp = self.pd.thermalManager['temp_hotend'][0]['target']
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(1),
					self.pd.thermalManager['temp_hotend'][0]['target']
				)
				self.EncoderRateLimit = False
			elif self.select_temp.now == self.TEMP_CASE_BED:  # Bed temperature
				self.checkkey = self.BedTemp
				self.pd.HMI_ValueStruct.Bed_Temp = self.pd.thermalManager['temp_bed']['target']
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(2),
					self.pd.thermalManager['temp_bed']['target']
				)
				self.EncoderRateLimit = False
			elif self.select_temp.now == self.TEMP_CASE_FAN:  # Fan speed
				self.checkkey = self.FanSpeed
				self.pd.HMI_ValueStruct.Fan_speed = self.pd.thermalManager['fan_speed'][0]
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(3), self.pd.thermalManager['fan_speed'][0]
				)
				self.EncoderRateLimit = False

			elif self.select_temp.now == self.TEMP_CASE_PLA:  # PLA preheat setting
				self.checkkey = self.PLAPreheat
				self.select_PLA.reset()
				self.pd.HMI_ValueStruct.show_mode = -2

				self.Clear_Main_Window()
				self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "PLA Settings"
				self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_TEMP))
				self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_TEMP))
				self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 71, self.MBASE(self.PREHEAT_CASE_TEMP))  # PLA nozzle temp
				if self.pd.HAS_HEATED_BED:
					self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_BED) + 3)
					self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_BED) + 3)
					self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 54, self.MBASE(self.PREHEAT_CASE_BED) + 3)  # PLA bed temp
				if self.pd.HAS_FAN:
					self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_FAN))
					self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_FAN))  # PLA fan speed

				self.lcd.Frame_AreaCopy(1, 97, 165, 229, 177, self.LBLX, self.MBASE(self.PREHEAT_CASE_SAVE))  # Save PLA configuration

				self.Draw_Back_First()
				i = 1
				self.Draw_Menu_Line(i, self.ICON_SetEndTemp)
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(i),
					self.pd.material_preset[0].hotend_temp
				)
				if self.pd.HAS_HEATED_BED:
					i += 1
					self.Draw_Menu_Line(i, self.ICON_SetBedTemp)
					self.lcd.Draw_IntValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 216, self.MBASE(i),
						self.pd.material_preset[0].bed_temp
					)
				if self.pd.HAS_FAN:
					i += 1
					self.Draw_Menu_Line(i, self.ICON_FanSpeed)
					self.lcd.Draw_IntValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 216, self.MBASE(i),
						self.pd.material_preset[0].fan_speed
					)
				i += 1
				self.Draw_Menu_Line(i, self.ICON_WriteEEPROM)
			elif self.select_temp.now == self.TEMP_CASE_ABS:  # ABS preheat setting
				self.checkkey = self.ABSPreheat
				self.select_ABS.reset()
				self.pd.HMI_ValueStruct.show_mode = -3
				self.Clear_Main_Window()
				self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "ABS Settings"
				self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_TEMP))
				self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_TEMP))
				self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 71, self.MBASE(self.PREHEAT_CASE_TEMP))  # ABS nozzle temp
				if self.pd.HAS_HEATED_BED:
					self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_BED) + 3)
					self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_BED) + 3)
					self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 54, self.MBASE(self.PREHEAT_CASE_BED) + 3)  # ABS bed temp
				if self.pd.HAS_FAN:
					self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX, self.MBASE(self.PREHEAT_CASE_FAN))
					self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX + 27, self.MBASE(self.PREHEAT_CASE_FAN))  # ABS fan speed

				self.lcd.Frame_AreaCopy(1, 97, 165, 229, 177, self.LBLX, self.MBASE(self.PREHEAT_CASE_SAVE))
				self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 33, self.MBASE(self.PREHEAT_CASE_SAVE))  # Save ABS configuration

				self.Draw_Back_First()
				i = 1
				self.Draw_Menu_Line(i, self.ICON_SetEndTemp)
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(i),
					self.pd.material_preset[1].hotend_temp
				)
				if self.pd.HAS_HEATED_BED:
					i += 1
					self.Draw_Menu_Line(i, self.ICON_SetBedTemp)
					self.lcd.Draw_IntValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 216, self.MBASE(i),
						self.pd.material_preset[1].bed_temp
					)
				if self.pd.HAS_FAN:
					i += 1
					self.Draw_Menu_Line(i, self.ICON_FanSpeed)
					self.lcd.Draw_IntValue(
						True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
						3, 216, self.MBASE(i),
						self.pd.material_preset[1].fan_speed
					)
				i += 1
				self.Draw_Menu_Line(i, self.ICON_WriteEEPROM)

		self.lcd.UpdateLCD()

	def HMI_PLAPreheatSetting(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		# Avoid flicker by updating only the previous menu
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_PLA.inc(1 + self.PREHEAT_CASE_TOTAL)):
				self.Move_Highlight(1, self.select_PLA.now)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_PLA.dec()):
				self.Move_Highlight(-1, self.select_PLA.now)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):

			if self.select_PLA.now == 0:  # Back
				self.checkkey = self.TemperatureID
				self.select_temp.now = self.TEMP_CASE_PLA
				self.pd.HMI_ValueStruct.show_mode = -1
				self.Draw_Temperature_Menu()
			elif self.select_PLA.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
				self.checkkey = self.ETemp
				self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[0].hotend_temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_TEMP),
					self.pd.material_preset[0].hotend_temp
				)
				self.EncoderRateLimit = False
			elif self.select_PLA.now == self.PREHEAT_CASE_BED:  # Bed temperature
				self.checkkey = self.BedTemp
				self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[0].bed_temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_BED),
					self.pd.material_preset[0].bed_temp
				)
				self.EncoderRateLimit = False
			elif self.select_PLA.now == self.PREHEAT_CASE_FAN:  # Fan speed
				self.checkkey = self.FanSpeed
				self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[0].fan_speed
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_FAN),
					self.pd.material_preset[0].fan_speed
				)
				self.EncoderRateLimit = False
			elif self.select_PLA.now == self.PREHEAT_CASE_SAVE:  # Save PLA configuration
				success = self.pd.save_settings()
				self.HMI_AudioFeedback(success)
		self.lcd.UpdateLCD()

	def HMI_ABSPreheatSetting(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		# Avoid flicker by updating only the previous menu
		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_ABS.inc(1 + self.PREHEAT_CASE_TOTAL)):
				self.Move_Highlight(1, self.select_ABS.now)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_ABS.dec()):
				self.Move_Highlight(-1, self.select_ABS.now)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):

			if self.select_ABS.now == 0:  # Back
				self.checkkey = self.TemperatureID
				self.select_temp.now = self.TEMP_CASE_ABS
				self.pd.HMI_ValueStruct.show_mode = -1
				self.Draw_Temperature_Menu()

			elif self.select_ABS.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
				self.checkkey = self.ETemp
				self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[1].hotend_temp
				print(self.pd.HMI_ValueStruct.E_Temp)
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_TEMP),
					self.pd.material_preset[1].hotend_temp
				)
				self.EncoderRateLimit = False
			elif self.select_ABS.now == self.PREHEAT_CASE_BED:  # Bed temperature
				self.checkkey = self.BedTemp
				self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[1].bed_temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_BED),
					self.pd.material_preset[1].bed_temp
				)
				self.EncoderRateLimit = False
			elif self.select_ABS.now == self.PREHEAT_CASE_FAN:  # Fan speed
				self.checkkey = self.FanSpeed
				self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[1].fan_speed
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
					3, 216, self.MBASE(self.PREHEAT_CASE_FAN),
					self.pd.material_preset[1].fan_speed
				)
				self.EncoderRateLimit = False
			elif self.select_ABS.now == self.PREHEAT_CASE_SAVE:  # Save PLA configuration
				success = self.pd.save_settings()
				self.HMI_AudioFeedback(success)
		self.lcd.UpdateLCD()

	def HMI_ETemp(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if self.pd.HMI_ValueStruct.show_mode == -1:
			temp_line = self.TEMP_CASE_TEMP
		elif self.pd.HMI_ValueStruct.show_mode == -2:
			temp_line = self.PREHEAT_CASE_TEMP
		elif self.pd.HMI_ValueStruct.show_mode == -3:
			temp_line = self.PREHEAT_CASE_TEMP
		else:
			temp_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

		if (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.EncoderRateLimit = True
			if (self.pd.HMI_ValueStruct.show_mode == -1):  # temperature
				self.checkkey = self.TemperatureID
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(temp_line),
					self.pd.HMI_ValueStruct.E_Temp
				)
			elif (self.pd.HMI_ValueStruct.show_mode == -2):
				self.checkkey = self.PLAPreheat
				self.pd.material_preset[0].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(temp_line),
					self.pd.material_preset[0].hotend_temp
				)
				return
			elif (self.pd.HMI_ValueStruct.show_mode == -3):
				self.checkkey = self.ABSPreheat
				self.pd.material_preset[1].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(temp_line),
					self.pd.material_preset[1].hotend_temp
				)
				return
			else:  # tune
				self.checkkey = self.Tune
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(temp_line),
					self.pd.HMI_ValueStruct.E_Temp
				)
				self.pd.setTargetHotend(self.pd.HMI_ValueStruct.E_Temp, 0)
			return

		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.E_Temp += 1

		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.E_Temp -= 1

		# E_Temp limit
		if self.pd.HMI_ValueStruct.E_Temp > self.pd.MAX_E_TEMP:
			self.pd.HMI_ValueStruct.E_Temp = self.pd.MAX_E_TEMP
		if self.pd.HMI_ValueStruct.E_Temp < self.pd.MIN_E_TEMP:
			self.pd.HMI_ValueStruct.E_Temp = self.pd.MIN_E_TEMP
		# E_Temp value
		self.lcd.Draw_IntValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
			3, 216, self.MBASE(temp_line),
			self.pd.HMI_ValueStruct.E_Temp
		)

	def HMI_BedTemp(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

		if self.pd.HMI_ValueStruct.show_mode == -1:
			bed_line = self.TEMP_CASE_BED
		elif self.pd.HMI_ValueStruct.show_mode == -2:
			bed_line = self.PREHEAT_CASE_BED
		elif self.pd.HMI_ValueStruct.show_mode == -3:
			bed_line = self.PREHEAT_CASE_BED
		else:
			bed_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

		if (encoder_diffState == self.ENCODER_DIFF_ENTER):
			self.EncoderRateLimit = True
			if (self.pd.HMI_ValueStruct.show_mode == -1):  # temperature
				self.checkkey = self.TemperatureID
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(bed_line),
					self.pd.HMI_ValueStruct.Bed_Temp
				)
			elif (self.pd.HMI_ValueStruct.show_mode == -2):
				self.checkkey = self.PLAPreheat
				self.pd.material_preset[0].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(bed_line),
					self.pd.material_preset[0].bed_temp
				)
				return
			elif (self.pd.HMI_ValueStruct.show_mode == -3):
				self.checkkey = self.ABSPreheat
				self.pd.material_preset[1].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(bed_line),
					self.pd.material_preset[1].bed_temp
				)
				return
			else:  # tune
				self.checkkey = self.Tune
				self.lcd.Draw_IntValue(
					True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
					3, 216, self.MBASE(bed_line),
					self.pd.HMI_ValueStruct.Bed_Temp
				)
				self.pd.setTargetHotend(self.pd.HMI_ValueStruct.Bed_Temp, 0)
			return

		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.Bed_Temp += 1

		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.Bed_Temp -= 1

		# Bed_Temp limit
		if self.pd.HMI_ValueStruct.Bed_Temp > self.pd.BED_MAX_TARGET:
			self.pd.HMI_ValueStruct.Bed_Temp = self.pd.BED_MAX_TARGET
		if self.pd.HMI_ValueStruct.Bed_Temp < self.pd.MIN_BED_TEMP:
			self.pd.HMI_ValueStruct.Bed_Temp = self.pd.MIN_BED_TEMP
		# Bed_Temp value
		self.lcd.Draw_IntValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Select_Color,
			3, 216, self.MBASE(bed_line),
			self.pd.HMI_ValueStruct.Bed_Temp
		)

# ---------------------Todo--------------------------------#

	def HMI_Motion(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		if (encoder_diffState == self.ENCODER_DIFF_CW):
			if (self.select_motion.inc(1 + self.MOTION_CASE_TOTAL)):
				self.Move_Highlight(1, self.select_motion.now)
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			if (self.select_motion.dec()):
				self.Move_Highlight(-1, self.select_motion.now)
		elif (encoder_diffState == self.ENCODER_DIFF_ENTER):
			if self.select_motion.now == 0:  # back
				self.checkkey = self.Control
				self.select_control.set(self.CONTROL_CASE_MOVE)
				self.index_control = self.MROWS
				self.Draw_Control_Menu()
		self.lcd.UpdateLCD()

	def HMI_Zoffset(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return
		zoff_line = 0
		if self.pd.HMI_ValueStruct.show_mode == -4:
			zoff_line = self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare
		else:
			zoff_line = self.TUNE_CASE_ZOFF + self.MROWS - self.index_tune

		if (encoder_diffState == self.ENCODER_DIFF_ENTER): #if (applyencoder(encoder_diffstate, offset_value))
			self.EncoderRateLimit = True
			if self.pd.HAS_BED_PROBE:
				self.pd.offset_z(self.dwin_zoffset)
			else:
				self.pd.setZOffset(self.dwin_zoffset) # manually set

			self.checkkey = self.Prepare if self.pd.HMI_ValueStruct.show_mode == -4 else self.Tune
			self.lcd.Draw_Signed_Float(
				self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202, self.MBASE(zoff_line),
				self.pd.HMI_ValueStruct.offset_value
			)

			self.lcd.UpdateLCD()
			return

		elif (encoder_diffState == self.ENCODER_DIFF_CW):
			self.pd.HMI_ValueStruct.offset_value += 1
		elif (encoder_diffState == self.ENCODER_DIFF_CCW):
			self.pd.HMI_ValueStruct.offset_value -= 1

		if (self.pd.HMI_ValueStruct.offset_value < (self.pd.Z_PROBE_OFFSET_RANGE_MIN) * 100):
			self.pd.HMI_ValueStruct.offset_value = self.pd.Z_PROBE_OFFSET_RANGE_MIN * 100
		elif (self.pd.HMI_ValueStruct.offset_value > (self.pd.Z_PROBE_OFFSET_RANGE_MAX) * 100):
			self.pd.HMI_ValueStruct.offset_value = self.pd.Z_PROBE_OFFSET_RANGE_MAX * 100

		self.last_zoffset = self.dwin_zoffset
		self.dwin_zoffset = self.pd.HMI_ValueStruct.offset_value / 100.0
		if self.pd.HAS_BED_PROBE:
			self.pd.add_mm('Z', self.dwin_zoffset - self.last_zoffset)

		self.lcd.Draw_Signed_Float(
			self.lcd.font8x16, self.lcd.Select_Color, 2, 2, 202,
			self.MBASE(zoff_line),
			self.pd.HMI_ValueStruct.offset_value
		)
		self.lcd.UpdateLCD()

	def HMI_MaxSpeed(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_MaxAcceleration(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_MaxJerk(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_Step(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_MaxFeedspeedXYZE(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_MaxAccelerationXYZE(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_MaxJerkXYZE(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	def HMI_StepXYZE(self):
		encoder_diffState = self.get_encoder_state()
		if (encoder_diffState == self.ENCODER_DIFF_NO):
			return

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

	def Draw_Status_Area(self, with_update):
		#  Clear the bottom area of the screen
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, self.STATUS_Y, self.lcd.DWIN_WIDTH, self.lcd.DWIN_HEIGHT - 1)
		#
		#  Status Area
		#
		if self.pd.HAS_HOTEND:
			self.lcd.ICON_Show(self.ICON, self.ICON_HotendTemp, 13, 381)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.DWIN_FONT_STAT,
				self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 33, 382,
				self.pd.thermalManager['temp_hotend'][0]['celsius']
			)
			self.lcd.Draw_String(
				False, False, self.lcd.DWIN_FONT_STAT,
				self.lcd.Color_White, self.lcd.Color_Bg_Black,
				33 + 3 * self.STAT_CHR_W + 5, 383,
				"/"
			)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.DWIN_FONT_STAT,
				self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 33 + 4 * self.STAT_CHR_W + 6, 382,
				self.pd.thermalManager['temp_hotend'][0]['target']
			)

		if self.pd.HOTENDS > 1:
			self.lcd.ICON_Show(self.ICON, self.ICON_HotendTemp, 13, 381)

		if self.pd.HAS_HEATED_BED:
			self.lcd.ICON_Show(self.ICON, self.ICON_BedTemp, 158, 381)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.DWIN_FONT_STAT, self.lcd.Color_White,
				self.lcd.Color_Bg_Black, 3, 178, 382,
				self.pd.thermalManager['temp_bed']['celsius']
			)
			self.lcd.Draw_String(
				False, False, self.lcd.DWIN_FONT_STAT, self.lcd.Color_White,
				self.lcd.Color_Bg_Black, 178 + 3 * self.STAT_CHR_W + 5, 383,
				"/"
			)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.DWIN_FONT_STAT,
				self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 178 + 4 * self.STAT_CHR_W + 6, 382,
				self.pd.thermalManager['temp_bed']['target']
			)

		self.lcd.ICON_Show(self.ICON, self.ICON_Speed, 13, 429)
		self.lcd.Draw_IntValue(
			True, True, 0, self.lcd.DWIN_FONT_STAT,
			self.lcd.Color_White, self.lcd.Color_Bg_Black, 3, 33 + 2 * self.STAT_CHR_W, 429,
			self.pd.feedrate_percentage
		)
		self.lcd.Draw_String(
			False, False, self.lcd.DWIN_FONT_STAT,
			self.lcd.Color_White, self.lcd.Color_Bg_Black, 33 + 5 * self.STAT_CHR_W + 2, 429,
			"%"
		)

		if self.pd.HAS_ZOFFSET_ITEM:
			self.lcd.ICON_Show(self.ICON, self.ICON_Zoffset, 158, 428)
			self.lcd.Draw_Signed_Float(self.lcd.DWIN_FONT_STAT, self.lcd.Color_Bg_Black, 2, 2, 178, 429, self.pd.BABY_Z_VAR * 100)

		# if with_update:
		# 	self.lcd.UpdateLCD()
		# 	time.sleep(.005)

	def Draw_Title(self, title):
		self.lcd.Draw_String(False, False, self.lcd.DWIN_FONT_HEAD, self.lcd.Color_White, self.lcd.Color_Bg_Blue, 14, 4, title)

	def Draw_Popup_Bkgd_105(self):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Window, 14, 105, 258, 374)

	def Draw_More_Icon(self, line):
		self.lcd.ICON_Show(self.ICON, self.ICON_More, 226, self.MBASE(line) - 3)

	def Draw_Menu_Cursor(self, line):
		self.lcd.Draw_Rectangle(1, self.lcd.Rectangle_Color, 0, self.MBASE(line) - 18, 14, self.MBASE(line + 1) - 20)

	def Draw_Menu_Icon(self, line, icon):
		self.lcd.ICON_Show(self.ICON, icon, 26, self.MBASE(line) - 3)

	def Draw_Menu_Line(self, line, icon=False, label=False):
		if (label):
			self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, self.LBLX, self.MBASE(line) - 1, label)
		if (icon):
			self.Draw_Menu_Icon(line, icon)
		self.lcd.Draw_Line(self.lcd.Line_Color, 16, self.MBASE(line) + 33, 256, self.MBASE(line) + 34)

	# The "Back" label is always on the first line
	def Draw_Back_Label(self):
		self.lcd.Frame_AreaCopy(1, 226, 179, 256, 189, self.LBLX, self.MBASE(0))

	# Draw "Back" line at the top
	def Draw_Back_First(self, is_sel=True):
		self.Draw_Menu_Line(0, self.ICON_Back)
		self.Draw_Back_Label()
		if (is_sel):
			self.Draw_Menu_Cursor(0)

	def draw_move_en(self, line):
		self.lcd.Frame_AreaCopy(1, 69, 61, 102, 71, self.LBLX, line)  # "Move"

	def draw_max_en(self, line):
		self.lcd.Frame_AreaCopy(1, 245, 119, 269, 129, self.LBLX, line)  # "Max"

	def draw_max_accel_en(self, line):
		self.draw_max_en(line)
		self.lcd.Frame_AreaCopy(1, 1, 135, 79, 145, self.LBLX + 27, line)  # "Acceleration"

	def draw_speed_en(self, inset, line):
		self.lcd.Frame_AreaCopy(1, 184, 119, 224, 132, self.LBLX + inset, line)  # "Speed"

	def draw_jerk_en(self, line):
		self.lcd.Frame_AreaCopy(1, 64, 119, 106, 129, self.LBLX + 27, line)  # "Jerk"

	def draw_steps_per_mm(self, line):
		self.lcd.Frame_AreaCopy(1, 1, 151, 101, 161, self.LBLX, line)  # "Steps-per-mm"

	# Display an SD item
	def Draw_SDItem(self, item, row=0):
		fl = self.pd.GetFiles()[item]
		self.Draw_Menu_Line(row, self.ICON_File, fl)

	def Draw_Select_Highlight(self, sel):
		self.pd.HMI_flag.select_flag = sel
		if sel:
			c1 = self.lcd.Select_Color
			c2 = self.lcd.Color_Bg_Window
		else:
			c1 = self.lcd.Color_Bg_Window
			c2 = self.lcd.Select_Color
		self.lcd.Draw_Rectangle(0, c1, 25, 279, 126, 318)
		self.lcd.Draw_Rectangle(0, c1, 24, 278, 127, 319)
		self.lcd.Draw_Rectangle(0, c2, 145, 279, 246, 318)
		self.lcd.Draw_Rectangle(0, c2, 144, 278, 247, 319)

	def Draw_Popup_Bkgd_60(self):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Window, 14, 60, 258, 330)

	def Draw_Printing_Screen(self):
		self.lcd.Frame_AreaCopy(1, 40, 2, 92, 14, 14, 9)  # Tune
		self.lcd.Frame_AreaCopy(1, 0, 44, 96, 58, 41, 188)  # Pause
		self.lcd.Frame_AreaCopy(1, 98, 44, 152, 58, 176, 188)  # Stop

	def Draw_Print_ProgressBar(self, Percentrecord=None):
		if not Percentrecord:
			Percentrecord = self.pd.getPercent()
		self.lcd.ICON_Show(self.ICON, self.ICON_Bar, 15, 93)
		self.lcd.Draw_Rectangle(1, self.lcd.BarFill_Color, 16 + Percentrecord * 240 / 100, 93, 256, 113)
		self.lcd.Draw_IntValue(True, True, 0, self.lcd.font8x16, self.lcd.Percent_Color, self.lcd.Color_Bg_Black, 2, 117, 133, Percentrecord)
		self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Percent_Color, self.lcd.Color_Bg_Black, 133, 133, "%")

	def Draw_Print_ProgressElapsed(self):
		elapsed = self.pd.duration()  # print timer
		self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 2, 42, 212, elapsed / 3600)
		self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 58, 212, ":")
		self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 2, 66, 212, (elapsed % 3600) / 60)

	def Draw_Print_ProgressRemain(self):
		remain_time = self.pd.remain()
		if not remain_time: return #time remaining is None during warmup.
		self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 2, 176, 212, remain_time / 3600)
		self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 192, 212, ":")
		self.lcd.Draw_IntValue(True, True, 1, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, 2, 200, 212, (remain_time % 3600) / 60)

	def Draw_Print_File_Menu(self):
		self.Clear_Title_Bar()
		self.lcd.Frame_TitleCopy(1, 52, 31, 137, 41)  # "Print file"
		self.Redraw_SD_List()

	def Draw_Prepare_Menu(self):
		self.Clear_Main_Window()
		scroll = self.MROWS - self.index_prepare
		self.lcd.Frame_TitleCopy(1, 178, 2, 229, 14)  # "Prepare"
		self.Draw_Back_First(self.select_prepare.now == 0)  # < Back
		if scroll + self.PREPARE_CASE_MOVE <= self.MROWS:
			self.Item_Prepare_Move(self.PREPARE_CASE_MOVE)  # Move >
		if scroll + self.PREPARE_CASE_DISA <= self.MROWS:
			self.Item_Prepare_Disable(self.PREPARE_CASE_DISA)  # Disable Stepper
		if scroll + self.PREPARE_CASE_HOME <= self.MROWS:
			self.Item_Prepare_Home(self.PREPARE_CASE_HOME)  # Auto Home
		if self.pd.HAS_ZOFFSET_ITEM:
			if scroll + self.PREPARE_CASE_ZOFF <= self.MROWS:
				self.Item_Prepare_Offset(self.PREPARE_CASE_ZOFF)  # Edit Z-Offset / Babystep / Set Home Offset
		if self.pd.HAS_HOTEND:
			if scroll + self.PREPARE_CASE_PLA <= self.MROWS:
				self.Item_Prepare_PLA(self.PREPARE_CASE_PLA)  # Preheat PLA
			if scroll + self.PREPARE_CASE_ABS <= self.MROWS:
				self.Item_Prepare_ABS(self.PREPARE_CASE_ABS)  # Preheat ABS
		if self.pd.HAS_PREHEAT:
			if scroll + self.PREPARE_CASE_COOL <= self.MROWS:
				self.Item_Prepare_Cool(self.PREPARE_CASE_COOL)  # Cooldown
		if (self.select_prepare.now):
			self.Draw_Menu_Cursor(self.select_prepare.now)

	def Draw_Control_Menu(self):
		self.Clear_Main_Window()
		self.Draw_Back_First(self.select_control.now == 0)
		self.lcd.Frame_TitleCopy(1, 128, 2, 176, 12)  # "Control"
		self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX, self.MBASE(self.CONTROL_CASE_TEMP))  # Temperature >
		self.lcd.Frame_AreaCopy(1, 84, 89, 128, 99, self.LBLX, self.MBASE(self.CONTROL_CASE_MOVE))  # Motion >
		self.lcd.Frame_AreaCopy(1, 0, 104, 25, 115, self.LBLX, self.MBASE(self.CONTROL_CASE_INFO))  # Info >

		if self.select_control.now and self.select_control.now < self.MROWS:
			self.Draw_Menu_Cursor(self.select_control.now)

		# # Draw icons and lines
		self.Draw_Menu_Line(1, self.ICON_Temperature)
		self.Draw_More_Icon(1)
		self.Draw_Menu_Line(2, self.ICON_Motion)
		self.Draw_More_Icon(2)
		self.Draw_Menu_Line(3, self.ICON_Info)
		self.Draw_More_Icon(3)

	def Draw_Info_Menu(self):
		self.Clear_Main_Window()

		self.lcd.Draw_String(
			False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
			(self.lcd.DWIN_WIDTH - len(self.pd.MACHINE_SIZE) * self.MENU_CHR_W) / 2, 122,
			self.pd.MACHINE_SIZE
		)
		self.lcd.Draw_String(
			False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
			(self.lcd.DWIN_WIDTH - len(self.pd.SHORT_BUILD_VERSION) * self.MENU_CHR_W) / 2, 195,
			self.pd.SHORT_BUILD_VERSION
		)
		self.lcd.Frame_TitleCopy(1, 190, 16, 215, 26)  # "Info"
		self.lcd.Frame_AreaCopy(1, 120, 150, 146, 161, 124, 102)
		self.lcd.Frame_AreaCopy(1, 146, 151, 254, 161, 82, 175)
		self.lcd.Frame_AreaCopy(1, 0, 165, 94, 175, 89, 248)
		self.lcd.Draw_String(
			False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
			(self.lcd.DWIN_WIDTH - len(self.pd.CORP_WEBSITE_E) * self.MENU_CHR_W) / 2, 268,
			self.pd.CORP_WEBSITE_E
		)
		self.Draw_Back_First()
		for i in range(3):
			self.lcd.ICON_Show(self.ICON, self.ICON_PrintSize + i, 26, 99 + i * 73)
			self.lcd.Draw_Line(self.lcd.Line_Color, 16, self.MBASE(2) + i * 73, 256, 156 + i * 73)

	def Draw_Tune_Menu(self):
		self.Clear_Main_Window()
		self.lcd.Frame_AreaCopy(1, 94, 2, 126, 12, 14, 9)
		self.lcd.Frame_AreaCopy(1, 1, 179, 92, 190, self.LBLX, self.MBASE(self.TUNE_CASE_SPEED))  # Print speed
		if self.pd.HAS_HOTEND:
			self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX, self.MBASE(self.TUNE_CASE_TEMP))  # Hotend...
			self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 44, self.MBASE(self.TUNE_CASE_TEMP))  # Temperature
		if self.pd.HAS_HEATED_BED:
			self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX, self.MBASE(self.TUNE_CASE_BED))  # Bed...
			self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 27, self.MBASE(self.TUNE_CASE_BED))  # ...Temperature
		if self.pd.HAS_FAN:
		 	self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX, self.MBASE(self.TUNE_CASE_FAN))  # Fan speed
		if self.pd.HAS_ZOFFSET_ITEM:
		 	self.lcd.Frame_AreaCopy(1, 93, 179, 141, 189, self.LBLX, self.MBASE(self.TUNE_CASE_ZOFF))  # Z-offset
		self.Draw_Back_First(self.select_tune.now == 0)
		if (self.select_tune.now):
			self.Draw_Menu_Cursor(self.select_tune.now)

		self.Draw_Menu_Line(self.TUNE_CASE_SPEED, self.ICON_Speed)
		self.lcd.Draw_IntValue(
			True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
			3, 216, self.MBASE(self.TUNE_CASE_SPEED), self.pd.feedrate_percentage)

		if self.pd.HAS_HOTEND:
			self.Draw_Menu_Line(self.TUNE_CASE_TEMP, self.ICON_HotendTemp)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 216, self.MBASE(self.TUNE_CASE_TEMP),
				self.pd.thermalManager['temp_hotend'][0]['target']
			)

		if self.pd.HAS_HEATED_BED:
			self.Draw_Menu_Line(self.TUNE_CASE_BED, self.ICON_BedTemp)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 216, self.MBASE(self.TUNE_CASE_BED), self.pd.thermalManager['temp_bed']['target'])

		if self.pd.HAS_FAN:
		 	self.Draw_Menu_Line(self.TUNE_CASE_FAN, self.ICON_FanSpeed)
		 	self.lcd.Draw_IntValue(
		 		True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
		 		3, 216, self.MBASE(self.TUNE_CASE_FAN),
		 		self.pd.thermalManager['fan_speed'][0]
		 	)
		if self.pd.HAS_ZOFFSET_ITEM:
		 	self.Draw_Menu_Line(self.TUNE_CASE_ZOFF, self.ICON_Zoffset)
		 	self.lcd.Draw_Signed_Float(
		 		self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202, self.MBASE(self.TUNE_CASE_ZOFF), self.pd.BABY_Z_VAR * 100
		 	)

	def Draw_Temperature_Menu(self):
		self.Clear_Main_Window()
		self.lcd.Frame_TitleCopy(1, 56, 16, 141, 28)  # "Temperature"
		if self.pd.HAS_HOTEND:
			self.lcd.Frame_AreaCopy(1, 197, 104, 238, 114, self.LBLX, self.MBASE(self.TEMP_CASE_TEMP))  # Nozzle...
			self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 44, self.MBASE(self.TEMP_CASE_TEMP))  # ...Temperature
		if self.pd.HAS_HEATED_BED:
			self.lcd.Frame_AreaCopy(1, 240, 104, 264, 114, self.LBLX, self.MBASE(self.TEMP_CASE_BED))  # Bed...
			self.lcd.Frame_AreaCopy(1, 1, 89, 83, 101, self.LBLX + 27, self.MBASE(self.TEMP_CASE_BED))  # ...Temperature
		if self.pd.HAS_FAN:
			self.lcd.Frame_AreaCopy(1, 0, 119, 64, 132, self.LBLX, self.MBASE(self.TEMP_CASE_FAN))  # Fan speed
		if self.pd.HAS_HOTEND:
			self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.MBASE(self.TEMP_CASE_PLA))  # Preheat...
			self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX + 52, self.MBASE(self.TEMP_CASE_PLA))  # ...PLA
			self.lcd.Frame_AreaCopy(1, 131, 119, 182, 132, self.LBLX + 79, self.MBASE(self.TEMP_CASE_PLA))  # PLA setting
			self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.MBASE(self.TEMP_CASE_ABS))  # Preheat...
			self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 52, self.MBASE(self.TEMP_CASE_ABS))  # ...ABS
			self.lcd.Frame_AreaCopy(1, 131, 119, 182, 132, self.LBLX + 81, self.MBASE(self.TEMP_CASE_ABS))  # ABS setting

		self.Draw_Back_First(self.select_temp.now == 0)
		if (self.select_temp.now):
			self.Draw_Menu_Cursor(self.select_temp.now)

		# Draw icons and lines
		i = 0
		if self.pd.HAS_HOTEND:
			i += 1
			self.Draw_Menu_Line(self.ICON_SetEndTemp + (self.TEMP_CASE_TEMP) - 1)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 216, self.MBASE(i),
				self.pd.thermalManager['temp_hotend'][0]['target']
			)
		if self.pd.HAS_HEATED_BED:
			i += 1
			self.Draw_Menu_Line(self.ICON_SetEndTemp + (self.TEMP_CASE_BED) - 1)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 216, self.MBASE(i),
				self.pd.thermalManager['temp_bed']['target']
			)
		if self.pd.HAS_FAN:
			i += 1
			self.Draw_Menu_Line(self.ICON_SetEndTemp + (self.TEMP_CASE_FAN) - 1)
			self.lcd.Draw_IntValue(
				True, True, 0, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black,
				3, 216, self.MBASE(i),
				self.pd.thermalManager['fan_speed'][0]
			)
		if self.pd.HAS_HOTEND:
			# PLA/ABS items have submenus
			i += 1
			self.Draw_Menu_Line(self.ICON_SetEndTemp + (self.TEMP_CASE_PLA) - 1)
			self.Draw_More_Icon(i)
			i += 1
			self.Draw_Menu_Line(self.ICON_SetEndTemp + (self.TEMP_CASE_ABS) - 1)
			self.Draw_More_Icon(i)

	def Draw_Motion_Menu(self):
		self.Clear_Main_Window()
		self.lcd.Frame_TitleCopy(1, 144, 16, 189, 26)  # "Motion"
		self.draw_max_en(self.MBASE(self.MOTION_CASE_RATE))
		self.draw_speed_en(27, self.MBASE(self.MOTION_CASE_RATE))  # "Max Speed"
		self.draw_max_accel_en(self.MBASE(self.MOTION_CASE_ACCEL))  # "Max Acceleration"
		self.draw_steps_per_mm(self.MBASE(self.MOTION_CASE_STEPS))  # "Steps-per-mm"

		self.Draw_Back_First(self.select_motion.now == 0)
		if (self.select_motion.now):
			self.Draw_Menu_Cursor(self.select_motion.now)

		i = 1
		self.Draw_Menu_Line(self.ICON_MaxSpeed + (self.MOTION_CASE_RATE) - 1)
		self.Draw_More_Icon(i)
		i += 1
		self.Draw_Menu_Line(self.ICON_MaxSpeed + (self.MOTION_CASE_ACCEL) - 1)
		self.Draw_More_Icon(i)
		i += 1
		self.Draw_Menu_Line(self.ICON_MaxSpeed + (self.MOTION_CASE_STEPS) - 1)
		self.Draw_More_Icon(i)

	def Draw_Move_Menu(self):
		self.Clear_Main_Window()
		self.lcd.Frame_TitleCopy(1, 231, 2, 265, 12)  # "Move"
		self.draw_move_en(self.MBASE(1))
		self.say_x(36, self.MBASE(1))  # "Move X"
		self.draw_move_en(self.MBASE(2))
		self.say_y(36, self.MBASE(2))  # "Move Y"
		self.draw_move_en(self.MBASE(3))
		self.say_z(36, self.MBASE(3))  # "Move Z"
		if self.pd.HAS_HOTEND:
			self.lcd.Frame_AreaCopy(1, 123, 192, 176, 202, self.LBLX, self.MBASE(4))  # "Extruder"

		self.Draw_Back_First(self.select_axis.now == 0)
		if (self.select_axis.now):
			self.Draw_Menu_Cursor(self.select_axis.now)

		# Draw separators and icons
		for i in range(4):
			self.Draw_Menu_Line(i + 1, self.ICON_MoveX + i)

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

	def Goto_MainMenu(self):
		self.checkkey = self.MainMenu
		self.Clear_Main_Window()

		self.lcd.Frame_AreaCopy(1, 0, 2, 39, 12, 14, 9)
		self.lcd.ICON_Show(self.ICON, self.ICON_LOGO, 71, 52)

		self.ICON_Print()
		self.ICON_Prepare()
		self.ICON_Control()
		if self.pd.HAS_ONESTEP_LEVELING:
			self.ICON_Leveling(self.select_page.now == 3)
		else:
			self.ICON_StartInfo(self.select_page.now == 3)

	def Goto_PrintProcess(self):
		self.checkkey = self.PrintProcess
		self.Clear_Main_Window()
		self.Draw_Printing_Screen()

		self.ICON_Tune()
		if (self.pd.printingIsPaused()):
			self.ICON_Continue()
		else:
			self.ICON_Pause()
		self.ICON_Stop()

		# Copy into filebuf string before entry
		name = self.pd.file_name
		if name:
			npos = _MAX(0, self.lcd.DWIN_WIDTH - len(name) * self.MENU_CHR_W) / 2
			self.lcd.Draw_String(False, False, self.lcd.font8x16, self.lcd.Color_White, self.lcd.Color_Bg_Black, npos, 60, name)

		self.lcd.ICON_Show(self.ICON, self.ICON_PrintTime, 17, 193)
		self.lcd.ICON_Show(self.ICON, self.ICON_RemainTime, 150, 191)

		self.Draw_Print_ProgressBar()
		self.Draw_Print_ProgressElapsed()
		self.Draw_Print_ProgressRemain()

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

	def Clear_Title_Bar(self):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Blue, 0, 0, self.lcd.DWIN_WIDTH, 30)

	def Clear_Menu_Area(self):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, self.STATUS_Y)

	def Clear_Main_Window(self):
		self.Clear_Title_Bar()
		self.Clear_Menu_Area()

	def Clear_Popup_Area(self):
		self.Clear_Title_Bar()
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, self.lcd.DWIN_HEIGHT)

	def Popup_window_PauseOrStop(self):
		self.Clear_Main_Window()
		self.Draw_Popup_Bkgd_60()
		if(self.select_print.now == 1):
			self.lcd.Draw_String(
				False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
				(272 - 8 * 11) / 2, 150,
				self.MSG_PAUSE_PRINT
			)
		elif (self.select_print.now == 2):
			self.lcd.Draw_String(
				False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
				(272 - 8 * 10) / 2, 150,
				self.MSG_STOP_PRINT
			)
		self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 26, 280)
		self.lcd.ICON_Show(self.ICON, self.ICON_Cancel_E, 146, 280)
		self.Draw_Select_Highlight(True)

	def Popup_Window_Home(self, parking=False):
		self.Clear_Main_Window()
		self.Draw_Popup_Bkgd_60()
		self.lcd.ICON_Show(self.ICON, self.ICON_BLTouch, 101, 105)
		if parking:
			self.lcd.Draw_String(
				False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
				(272 - 8 * (7)) / 2, 230, "Parking")
		else:
			self.lcd.Draw_String(
				False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
				(272 - 8 * (10)) / 2, 230, "Homing XYZ")

		self.lcd.Draw_String(
			False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color, self.lcd.Color_Bg_Window,
			(272 - 8 * 23) / 2, 260, "Please wait until done.")

	def Popup_Window_ETempTooLow(self):
		self.Clear_Main_Window()
		self.Draw_Popup_Bkgd_60()
		self.lcd.ICON_Show(self.ICON, self.ICON_TempTooLow, 102, 105)
		self.lcd.Draw_String(
			False, True, self.lcd.font8x16, self.lcd.Popup_Text_Color,
			self.lcd.Color_Bg_Window, 20, 235,
			"Nozzle is too cold"
		)
		self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 86, 280)

	def Erase_Menu_Cursor(self, line):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, self.MBASE(line) - 18, 14, self.MBASE(line + 1) - 20)

	def Erase_Menu_Text(self, line):
		self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, self.LBLX, self.MBASE(line) - 14, 271, self.MBASE(line) + 28)

	def Move_Highlight(self, ffrom, newline):
		self.Erase_Menu_Cursor(newline - ffrom)
		self.Draw_Menu_Cursor(newline)

	def Add_Menu_Line(self):
		self.Move_Highlight(1, self.MROWS)
		self.lcd.Draw_Line(self.lcd.Line_Color, 16, self.MBASE(self.MROWS + 1) - 20, 256, self.MBASE(self.MROWS + 1) - 19)

	def Scroll_Menu(self, dir):
		self.lcd.Frame_AreaMove(1, dir, self.MLINE, self.lcd.Color_Bg_Black, 0, 31, self.lcd.DWIN_WIDTH, 349)
		if dir == self.DWIN_SCROLL_DOWN:
			self.Move_Highlight(-1, 0)
		elif dir == self.DWIN_SCROLL_UP:
			self.Add_Menu_Line()

	# Redraw the first set of SD Files
	def Redraw_SD_List(self):
		self.select_file.reset()
		self.index_file = self.MROWS
		self.Clear_Menu_Area()  # Leave title bar unchanged
		self.Draw_Back_First()
		fl = self.pd.GetFiles()
		ed = len(fl)
		if ed > 0:
			if ed > self.MROWS:
				ed = self.MROWS
			for i in range(ed):
				self.Draw_SDItem(i, i + 1)
		else:
			self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Red, 10, self.MBASE(3) - 10, self.lcd.DWIN_WIDTH - 10, self.MBASE(4))
			self.lcd.Draw_String(False, False, self.lcd.font16x32, self.lcd.Color_Yellow, self.lcd.Color_Bg_Red, ((self.lcd.DWIN_WIDTH) - 8 * 16) / 2, self.MBASE(3), "No Media")

	def CompletedHoming(self):
		self.pd.HMI_flag.home_flag = False
		if (self.checkkey == self.Last_Prepare):
			self.checkkey = self.Prepare
			self.select_prepare.now = self.PREPARE_CASE_HOME
			self.index_prepare = self.MROWS
			self.Draw_Prepare_Menu()
		elif (self.checkkey == self.Back_Main):
			self.pd.HMI_ValueStruct.print_speed = self.pd.feedrate_percentage = 100
			# dwin_zoffset = TERN0(HAS_BED_PROBE, probe.offset.z)
			# planner.finish_and_disable()
			self.Goto_MainMenu()

	def say_x(self, inset, line):
		self.lcd.Frame_AreaCopy(1, 95, 104, 102, 114, self.LBLX + inset, line)  # "X"

	def say_y(self, inset, line):
		self.lcd.Frame_AreaCopy(1, 104, 104, 110, 114, self.LBLX + inset, line)  # "Y"

	def say_z(self, inset, line):
		self.lcd.Frame_AreaCopy(1, 112, 104, 120, 114, self.LBLX + inset, line)  # "Z"

	def say_e(self, inset, line):
		self.lcd.Frame_AreaCopy(1, 237, 119, 244, 129, self.LBLX + inset, line)  # "E"

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

	def ICON_Print(self):
		if self.select_page.now == 0:
			self.lcd.ICON_Show(self.ICON, self.ICON_Print_1, 17, 130)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 17, 130, 126, 229)
			self.lcd.Frame_AreaCopy(1, 1, 451, 31, 463, 57, 201)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Print_0, 17, 130)
			self.lcd.Frame_AreaCopy(1, 1, 423, 31, 435, 57, 201)

	def ICON_Prepare(self):
		if self.select_page.now == 1:
			self.lcd.ICON_Show(self.ICON, self.ICON_Prepare_1, 145, 130)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 130, 254, 229)
			self.lcd.Frame_AreaCopy(1, 33, 451, 82, 466, 175, 201)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Prepare_0, 145, 130)
			self.lcd.Frame_AreaCopy(1, 33, 423, 82, 438, 175, 201)

	def ICON_Control(self):
		if self.select_page.now == 2:
			self.lcd.ICON_Show(self.ICON, self.ICON_Control_1, 17, 246)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 17, 246, 126, 345)
			self.lcd.Frame_AreaCopy(1, 85, 451, 132, 463, 48, 318)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Control_0, 17, 246)
			self.lcd.Frame_AreaCopy(1, 85, 423, 132, 434, 48, 318)

	def ICON_Leveling(self, show):
		if show:
			self.lcd.ICON_Show(self.ICON, self.ICON_Leveling_1, 145, 246)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 246, 254, 345)
			self.lcd.Frame_AreaCopy(1, 84, 437, 120, 449, 182, 318)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Leveling_0, 145, 246)
			self.lcd.Frame_AreaCopy(1, 84, 465, 120, 478, 182, 318)

	def ICON_StartInfo(self, show):
		if show:
			self.lcd.ICON_Show(self.ICON, self.ICON_Info_1, 145, 246)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 145, 246, 254, 345)
			self.lcd.Frame_AreaCopy(1, 132, 451, 159, 466, 186, 318)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Info_0, 145, 246)
			self.lcd.Frame_AreaCopy(1, 132, 423, 159, 435, 186, 318)

	def ICON_Tune(self):
		if (self.select_print.now == 0):
			self.lcd.ICON_Show(self.ICON, self.ICON_Setup_1, 8, 252)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 8, 252, 87, 351)
			self.lcd.Frame_AreaCopy(1, 0, 466, 34, 476, 31, 325)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Setup_0, 8, 252)
			self.lcd.Frame_AreaCopy(1, 0, 438, 32, 448, 31, 325)

	def ICON_Continue(self):
		if (self.select_print.now == 1):
			self.lcd.ICON_Show(self.ICON, self.ICON_Continue_1, 96, 252)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 96, 252, 175, 351)
			self.lcd.Frame_AreaCopy(1, 1, 452, 32, 464, 121, 325)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Continue_0, 96, 252)
			self.lcd.Frame_AreaCopy(1, 1, 424, 31, 434, 121, 325)

	def ICON_Pause(self):
		if (self.select_print.now == 1):
			self.lcd.ICON_Show(self.ICON, self.ICON_Pause_1, 96, 252)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 96, 252, 175, 351)
			self.lcd.Frame_AreaCopy(1, 177, 451, 216, 462, 116, 325)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Pause_0, 96, 252)
			self.lcd.Frame_AreaCopy(1, 177, 423, 215, 433, 116, 325)

	def ICON_Stop(self):
		if (self.select_print.now == 2):
			self.lcd.ICON_Show(self.ICON, self.ICON_Stop_1, 184, 252)
			self.lcd.Draw_Rectangle(0, self.lcd.Color_White, 184, 252, 263, 351)
			self.lcd.Frame_AreaCopy(1, 218, 452, 249, 466, 209, 325)
		else:
			self.lcd.ICON_Show(self.ICON, self.ICON_Stop_0, 184, 252)
			self.lcd.Frame_AreaCopy(1, 218, 423, 247, 436, 209, 325)

	def Item_Prepare_Move(self, row):
		self.draw_move_en(self.MBASE(row))  # "Move >"
		self.Draw_Menu_Line(row, self.ICON_Axis)
		self.Draw_More_Icon(row)

	def Item_Prepare_Disable(self, row):
		self.lcd.Frame_AreaCopy(1, 103, 59, 200, 74, self.LBLX, self.MBASE(row))  # Disable Stepper"
		self.Draw_Menu_Line(row, self.ICON_CloseMotor)

	def Item_Prepare_Home(self, row):
		self.lcd.Frame_AreaCopy(1, 202, 61, 271, 71, self.LBLX, self.MBASE(row))  # Auto Home"
		self.Draw_Menu_Line(row, self.ICON_Homing)

	def Item_Prepare_Offset(self, row):
		if self.pd.HAS_BED_PROBE:
			self.lcd.Frame_AreaCopy(1, 93, 179, 141, 189, self.LBLX, self.MBASE(row))  # "Z-Offset"
			self.lcd.Draw_Signed_Float(self.lcd.font8x16, self.lcd.Color_Bg_Black, 2, 2, 202, self.MBASE(row), self.pd.BABY_Z_VAR * 100)
		else:
			self.lcd.Frame_AreaCopy(1, 1, 76, 106, 86, self.LBLX, self.MBASE(row))  # "..."
		self.Draw_Menu_Line(row, self.ICON_SetHome)

	def Item_Prepare_PLA(self, row):
		self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.MBASE(row))  # Preheat"
		self.lcd.Frame_AreaCopy(1, 157, 76, 181, 86, self.LBLX + 52, self.MBASE(row))  # PLA"
		self.Draw_Menu_Line(row, self.ICON_PLAPreheat)

	def Item_Prepare_ABS(self, row):
		self.lcd.Frame_AreaCopy(1, 107, 76, 156, 86, self.LBLX, self.MBASE(row))  # "Preheat"
		self.lcd.Frame_AreaCopy(1, 172, 76, 198, 86, self.LBLX + 52, self.MBASE(row))  # "ABS"
		self.Draw_Menu_Line(row, self.ICON_ABSPreheat)

	def Item_Prepare_Cool(self, row):
		self.lcd.Frame_AreaCopy(1, 200, 76, 264, 86, self.LBLX, self.MBASE(row))  # "Cooldown"
		self.Draw_Menu_Line(row, self.ICON_Cool)

	# --------------------------------------------------------------#
	# --------------------------------------------------------------#

	def EachMomentUpdate(self):
		# variable update
		update = self.pd.update_variable()
		if self.last_status != self.pd.status:
			self.last_status = self.pd.status
			print(self.pd.status)
			if self.pd.status == 'printing':
				self.Goto_PrintProcess()
			elif self.pd.status in ['operational', 'complete', 'standby', 'cancelled']:
				self.Goto_MainMenu()

		if (self.checkkey == self.PrintProcess):
			if (self.pd.HMI_flag.print_finish and not self.pd.HMI_flag.done_confirm_flag):
				self.pd.HMI_flag.print_finish = False
				self.pd.HMI_flag.done_confirm_flag = True
				# show percent bar and value
				self.Draw_Print_ProgressBar(0)
				# show print done confirm
				self.lcd.Draw_Rectangle(1, self.lcd.Color_Bg_Black, 0, 250, self.lcd.DWIN_WIDTH - 1, self.STATUS_Y)
				self.lcd.ICON_Show(self.ICON, self.ICON_Confirm_E, 86, 283)
			elif (self.pd.HMI_flag.pause_flag != self.pd.printingIsPaused()):
				# print status update
				self.pd.HMI_flag.pause_flag = self.pd.printingIsPaused()
				if (self.pd.HMI_flag.pause_flag):
					self.ICON_Continue()
				else:
					self.ICON_Pause()
			self.Draw_Print_ProgressBar()
			self.Draw_Print_ProgressElapsed()
			self.Draw_Print_ProgressRemain()

		if self.pd.HMI_flag.home_flag:
			if self.pd.ishomed():
				self.CompletedHoming()

		if update:
			self.Draw_Status_Area(update)
		self.lcd.UpdateLCD()

	def encoder_has_data(self, val):
		if self.checkkey == self.MainMenu:
			self.HMI_MainMenu()
		elif self.checkkey == self.SelectFile:
			self.HMI_SelectFile()
		elif self.checkkey == self.Prepare:
			self.HMI_Prepare()
		elif self.checkkey == self.Control:
			self.HMI_Control()
		elif self.checkkey == self.PrintProcess:
			self.HMI_Printing()
		elif self.checkkey == self.Print_window:
			self.HMI_PauseOrStop()
		elif self.checkkey == self.AxisMove:
			self.HMI_AxisMove()
		elif self.checkkey == self.TemperatureID:
			self.HMI_Temperature()
		elif self.checkkey == self.Motion:
			self.HMI_Motion()
		elif self.checkkey == self.Info:
			self.HMI_Info()
		elif self.checkkey == self.Tune:
			self.HMI_Tune()
		elif self.checkkey == self.PLAPreheat:
			self.HMI_PLAPreheatSetting()
		elif self.checkkey == self.ABSPreheat:
			self.HMI_ABSPreheatSetting()
		elif self.checkkey == self.MaxSpeed:
			self.HMI_MaxSpeed()
		elif self.checkkey == self.MaxAcceleration:
			self.HMI_MaxAcceleration()
		elif self.checkkey == self.MaxJerk:
			self.HMI_MaxJerk()
		elif self.checkkey == self.Step:
			self.HMI_Step()
		elif self.checkkey == self.Move_X:
			self.HMI_Move_X()
		elif self.checkkey == self.Move_Y:
			self.HMI_Move_Y()
		elif self.checkkey == self.Move_Z:
			self.HMI_Move_Z()
		elif self.checkkey == self.Extruder:
			self.HMI_Move_E()
		elif self.checkkey == self.ETemp:
			self.HMI_ETemp()
		elif self.checkkey == self.Homeoffset:
			self.HMI_Zoffset()
		elif self.checkkey == self.BedTemp:
			self.HMI_BedTemp()
		# elif self.checkkey == self.FanSpeed:
		# 	self.HMI_FanSpeed()
		elif self.checkkey == self.PrintSpeed:
			self.HMI_PrintSpeed()
		elif self.checkkey == self.MaxSpeed_value:
			self.HMI_MaxFeedspeedXYZE()
		elif self.checkkey == self.MaxAcceleration_value:
			self.HMI_MaxAccelerationXYZE()
		elif self.checkkey == self.MaxJerk_value:
			self.HMI_MaxJerkXYZE()
		elif self.checkkey == self.Step_value:
			self.HMI_StepXYZE()

	def get_encoder_state(self):
		if self.EncoderRateLimit:
			if self.EncodeMS > current_milli_time():
				return self.ENCODER_DIFF_NO
			self.EncodeMS = current_milli_time() + self.ENCODER_WAIT

		if self.encoder.value < self.EncodeLast:
			self.EncodeLast = self.encoder.value
			return self.ENCODER_DIFF_CW
		elif self.encoder.value > self.EncodeLast:
			self.EncodeLast = self.encoder.value
			return self.ENCODER_DIFF_CCW
		elif not GPIO.input(self.button_pin):
			if self.EncodeEnter > current_milli_time(): # prevent double clicks
				return self.ENCODER_DIFF_NO
			self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
			return self.ENCODER_DIFF_ENTER
		else:
			return self.ENCODER_DIFF_NO

	def HMI_AudioFeedback(self, success=True):
		if (success):
			self.pd.buzzer.tone(100, 659)
			self.pd.buzzer.tone(10, 0)
			self.pd.buzzer.tone(100, 698)
		else:
			self.pd.buzzer.tone(40, 440)

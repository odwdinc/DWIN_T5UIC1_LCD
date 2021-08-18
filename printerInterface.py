from asyncio.tasks import sleep
import threading
import errno
import select
import socket
import json
import requests
from requests.exceptions import ConnectionError
import atexit
import time
import asyncio

class xyze_t:
	x = 0.0
	y = 0.0
	z = 0.0
	e = 0.0
	home_x = False
	home_y = False
	home_z = False

	def homing(self):
		self.home_x = False
		self.home_y = False
		self.home_z = False


class AxisEnum:
	X_AXIS = 0
	A_AXIS = 0
	Y_AXIS = 1
	B_AXIS = 1
	Z_AXIS = 2
	C_AXIS = 2
	E_AXIS = 3
	X_HEAD = 4
	Y_HEAD = 5
	Z_HEAD = 6
	E0_AXIS = 3
	E1_AXIS = 4
	E2_AXIS = 5
	E3_AXIS = 6
	E4_AXIS = 7
	E5_AXIS = 8
	E6_AXIS = 9
	E7_AXIS = 10
	ALL_AXES = 0xFE
	NO_AXIS = 0xFF


class HMI_value_t:
	E_Temp = 0
	Bed_Temp = 0
	Fan_speed = 0
	print_speed = 100
	Max_Feedspeed = 0.0
	Max_Acceleration = 0.0
	Max_Jerk = 0.0
	Max_Step = 0.0
	Move_X_scale = 0.0
	Move_Y_scale = 0.0
	Move_Z_scale = 0.0
	Move_E_scale = 0.0
	offset_value = 0.0
	show_mode = 0  # -1: Temperature control    0: Printing temperature


class HMI_Flag_t:
	language = 0
	pause_flag = False
	pause_action = False
	print_finish = False
	done_confirm_flag = False
	select_flag = False
	home_flag = False
	heat_flag = False  # 0: heating done  1: during heating
	ETempTooLow_flag = False
	leveling_offset_flag = False
	feedspeed_axis = AxisEnum()
	acc_axis = AxisEnum()
	jerk_axis = AxisEnum()
	step_axis = AxisEnum()


class buzz_t:
	def tone(self, t, n):
		pass


class material_preset_t:
	def __init__(self, name, hotend_temp, bed_temp, fan_speed=100):
		self.name = name
		self.hotend_temp = hotend_temp
		self.bed_temp = bed_temp
		self.fan_speed = fan_speed


class KlippySocket:
	def __init__(self, uds_filename, callback=None):
		self.webhook_socket_create(uds_filename)
		self.lock = threading.Lock()
		self.poll = select.poll()
		self.stop_threads = False
		self.poll.register(self.webhook_socket, select.POLLIN | select.POLLHUP)
		self.socket_data = ""
		self.t = threading.Thread(target=self.polling)
		self.callback = callback
		self.lines = []
		self.t.start()
		atexit.register(self.klippyExit)

	def klippyExit(self):
		print("Shuting down Klippy Socket")
		self.stop_threads = True
		self.t.join()

	def webhook_socket_create(self, uds_filename):
		self.webhook_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.webhook_socket.setblocking(0)
		print("Waiting for connect to %s\n" % (uds_filename,))
		while 1:
			try:
				self.webhook_socket.connect(uds_filename)
			except socket.error as e:
				if e.errno == errno.ECONNREFUSED:
					time.sleep(0.1)
					continue
				print(
					"Unable to connect socket %s [%d,%s]\n" % (
						uds_filename, e.errno,
						errno.errorcode[e.errno]
					))
				exit(-1)
			break
		print("Connection.\n")

	def process_socket(self):
		data = self.webhook_socket.recv(4096).decode()
		if not data:
			print("Socket closed\n")
			exit(0)
		parts = data.split('\x03')
		parts[0] = self.socket_data + parts[0]
		self.socket_data = parts.pop()
		for line in parts:
			if self.callback:
				self.callback(line)

	def queue_line(self, line):
		with self.lock:
			self.lines.append(line)

	def send_line(self):
		if len(self.lines) == 0:
			return
		line = self.lines.pop(0).strip()
		if not line or line.startswith('#'):
			return
		try:
			m = json.loads(line)
		except JSONDecodeError:
			print("ERROR: Unable to parse line\n")
			return
		cm = json.dumps(m, separators=(',', ':'))
		wdm = '{}\x03'.format(cm)
		self.webhook_socket.send(wdm.encode())

	def polling(self):
		while True:
			if self.stop_threads:
				break
			res = self.poll.poll(1000.)
			for fd, event in res:
				self.process_socket()
			with self.lock:
				self.send_line()


class MoonrakerSocket:
	def __init__(self, address, port, api_key):
		self.s = requests.Session()
		self.s.headers.update({
			'X-Api-Key': api_key,
			'Content-Type': 'application/json'
		})
		self.base_address = 'http://' + address + ':' + str(port)


class PrinterData:
	event_loop = None
	HAS_HOTEND = True
	HOTENDS = 1
	HAS_HEATED_BED = True
	HAS_FAN = False
	HAS_ZOFFSET_ITEM = True
	HAS_ONESTEP_LEVELING = False
	HAS_PREHEAT = True
	HAS_BED_PROBE = False
	PREVENT_COLD_EXTRUSION = True
	EXTRUDE_MINTEMP = 170
	EXTRUDE_MAXLENGTH = 200

	HEATER_0_MAXTEMP = 275
	HEATER_0_MINTEMP = 5
	HOTEND_OVERSHOOT = 15

	MAX_E_TEMP = (HEATER_0_MAXTEMP - (HOTEND_OVERSHOOT))
	MIN_E_TEMP = HEATER_0_MINTEMP

	BED_OVERSHOOT = 10
	BED_MAXTEMP = 150
	BED_MINTEMP = 5

	BED_MAX_TARGET = (BED_MAXTEMP - (BED_OVERSHOOT))
	MIN_BED_TEMP = BED_MINTEMP

	X_MIN_POS = 0.0
	Y_MIN_POS = 0.0
	Z_MIN_POS = 0.0
	Z_MAX_POS = 200

	Z_PROBE_OFFSET_RANGE_MIN = -20
	Z_PROBE_OFFSET_RANGE_MAX = 20

	buzzer = buzz_t()

	BABY_Z_VAR = 0
	feedrate_percentage = 100
	temphot = 0
	tempbed = 0

	HMI_ValueStruct = HMI_value_t()
	HMI_flag = HMI_Flag_t()

	current_position = xyze_t()

	thermalManager = {
		'temp_bed': {'celsius': 20, 'target': 120},
		'temp_hotend': [{'celsius': 20, 'target': 120}],
		'fan_speed': [100]
	}

	material_preset = [
		material_preset_t('PLA', 200, 60),
		material_preset_t('ABS', 210, 100)
	]
	files = None
	MACHINE_SIZE = "220x220x250"
	SHORT_BUILD_VERSION = "1.00"
	CORP_WEBSITE_E = "https://www.klipper3d.org/"

	def __init__(self, API_Key, URL='127.0.0.1'):
		self.op = MoonrakerSocket(URL, 80, API_Key)
		self.status = None
		print(self.op.base_address)
		self.ks = KlippySocket('/tmp/klippy_uds', callback=self.klippy_callback)
		subscribe = {
			"id": 4001,
			"method": "objects/subscribe",
			"params": {
				"objects": {
					"toolhead": [
						"position"
					]
				},
				"response_template": {}
			}
		}
		self.klippy_z_offset = '{"id": 4002, "method": "objects/query", "params": {"objects": {"configfile": ["config"]}}}'
		self.klippy_home = '{"id": 4003, "method": "objects/query", "params": {"objects": {"toolhead": ["homed_axes"]}}}'

		self.ks.queue_line(json.dumps(subscribe))
		self.ks.queue_line(self.klippy_z_offset)
		self.ks.queue_line(self.klippy_home)

		self.event_loop = asyncio.new_event_loop()
		threading.Thread(target=self.event_loop.run_forever, daemon=True).start()

	# ------------- Klipper Function ----------

	def klippy_callback(self, line):
		klippyData = json.loads(line)
		status = None
		if 'result' in klippyData:
			if 'status' in klippyData['result']:
				status = klippyData['result']['status']
		if 'params' in klippyData:
			if 'status' in klippyData['params']:
				status = klippyData['params']['status']

		if status:
			if 'toolhead' in status:
				if 'position' in status['toolhead']:
					self.current_position.x = status['toolhead']['position'][0]
					self.current_position.y = status['toolhead']['position'][1]
					self.current_position.z = status['toolhead']['position'][2]
					self.current_position.e = status['toolhead']['position'][3]
				if 'homed_axes' in status['toolhead']:
					if 'x' in status['toolhead']['homed_axes']:
						self.current_position.home_x = True
					if 'y' in status['toolhead']['homed_axes']:
						self.current_position.home_y = True
					if 'z' in status['toolhead']['homed_axes']:
						self.current_position.home_z = True

			if 'configfile' in status:
				if 'config' in status['configfile']:
					if 'bltouch' in status['configfile']['config']:
						if 'z_offset' in status['configfile']['config']['bltouch']:
							if status['configfile']['config']['bltouch']['z_offset']:
								self.BABY_Z_VAR = float(status['configfile']['config']['bltouch']['z_offset'])

			# print(status)

	def ishomed(self):
		if self.current_position.home_x and self.current_position.home_y and self.current_position.home_z:
			return True
		else:
			self.ks.queue_line(self.klippy_home)
			return False

	def offset_z(self, new_offset):
#		print('new z offset:', new_offset)
		self.BABY_Z_VAR = new_offset
		self.sendGCode('ACCEPT')

	def add_mm(self, axs, new_offset):
		gc = 'TESTZ Z={}'.format(new_offset)
		print(axs, gc)
		self.sendGCode(gc)

	def probe_calibrate(self):
		self.sendGCode('G28')
		self.sendGCode('PROBE_CALIBRATE')
		self.sendGCode('G1 Z0')

	# ------------- OctoPrint Function ----------

	def getREST(self, path):
		r = self.op.s.get(self.op.base_address + path)
		d = r.content.decode('utf-8')
		try:
			return json.loads(d)
		except JSONDecodeError:
			print('Decoding JSON has failed')
		return None

	async def _postREST(self, path, json):
		self.op.s.post(self.op.base_address + path, json=json)

	def postREST(self, path, json):
		self.event_loop.call_soon_threadsafe(asyncio.create_task,self._postREST(path,json))

	def init_Webservices(self):
		try:
			requests.get(self.op.base_address)
		except ConnectionError:
			print('Web site does not exist')
			return
		else:
			print('Web site exists')
		if self.getREST('/api/printer') is None:
			return
		self.update_variable()
		#alternative approach
		#full_version = self.getREST('/printer/info')['result']['software_version']
		#self.SHORT_BUILD_VERSION = '-'.join(full_version.split('-',2)[:2])
		self.SHORT_BUILD_VERSION = self.getREST('/machine/update/status?refresh=false')['result']['version_info']['klipper']['version']

		data = self.getREST('/printer/objects/query?toolhead')['result']['status']
		toolhead = data['toolhead']
		volume = toolhead['axis_maximum'] #[x,y,z,w]
		self.MACHINE_SIZE = "{}x{}x{}".format(
			int(volume[0]),
			int(volume[1]),
			int(volume[2])
		)
		self.X_MAX_POS = int(volume[0])
		self.Y_MAX_POS = int(volume[1])

	def GetFiles(self, refresh=False):
		if not self.files or refresh:
			self.files = self.getREST('/server/files/list')["result"]
		names = []
		for fl in self.files:
			names.append(fl["path"])
		return names

	def update_variable(self):
		query = '/printer/objects/query?extruder&heater_bed&gcode_move&fan'
		data = self.getREST(query)['result']['status']
		gcm = data['gcode_move']
		z_offset = gcm['homing_origin'][2] #z offset
		flow_rate = gcm['extrude_factor'] * 100 #flow rate percent
		self.absolute_moves = gcm['absolute_coordinates'] #absolute or relative
		self.absolute_extrude = gcm['absolute_extrude'] #absolute or relative
		speed = gcm['speed'] #current speed in mm/s
		print_speed = gcm['speed_factor'] * 100 #print speed percent
		bed = data['heater_bed'] #temperature, target
		extruder = data['extruder'] #temperature, target
		fan = data['fan']
		Update = False
		try:
			if self.thermalManager['temp_bed']['celsius'] != int(bed['temperature']):
				self.thermalManager['temp_bed']['celsius'] = int(bed['temperature'])
				Update = True
			if self.thermalManager['temp_bed']['target'] != int(bed['target']):
				self.thermalManager['temp_bed']['target'] = int(bed['target'])
				Update = True
			if self.thermalManager['temp_hotend'][0]['celsius'] != int(extruder['temperature']):
				self.thermalManager['temp_hotend'][0]['celsius'] = int(extruder['temperature'])
				Update = True
			if self.thermalManager['temp_hotend'][0]['target'] != int(extruder['target']):
				self.thermalManager['temp_hotend'][0]['target'] = int(extruder['target'])
				Update = True
			if self.thermalManager['fan_speed'][0] != int(fan['speed'] * 100):
				self.thermalManager['fan_speed'][0] = int(fan['speed'] * 100)
				Update = True
			if self.BABY_Z_VAR != z_offset:
				self.BABY_Z_VAR = z_offset
				self.HMI_ValueStruct.offset_value = z_offset * 100
				Update = True
		except:
			pass #missing key, shouldn't happen, fixes misses on conditionals ¯\_(ツ)_/¯
		self.job_Info = self.getREST('/printer/objects/query?virtual_sdcard&print_stats')['result']['status']
		if self.job_Info:
			self.file_name = self.job_Info['print_stats']['filename']
			self.status = self.job_Info['print_stats']['state']
			self.HMI_flag.print_finish = self.getPercent() == 100.0
		return Update

	def printingIsPaused(self):
		return self.job_Info['print_stats']['state'] == "paused" or self.job_Info['print_stats']['state'] == "pausing"

	def getPercent(self):
		if self.job_Info['virtual_sdcard']['is_active']:
			return self.job_Info['virtual_sdcard']['progress'] * 100
		else:
			return 0

	def duration(self):
		if self.job_Info['virtual_sdcard']['is_active']:
			return self.job_Info['print_stats']['print_duration']
		return 0

	def remain(self):
		percent = self.getPercent()
		duration = self.duration()
		if percent:
			total = duration / (percent / 100)
			return total - duration
		return 0

	def openAndPrintFile(self, filenum):
		self.file_name = self.files[filenum]['path']
		self.postREST('/printer/print/start', json={'filename': self.file_name})

	def cancel_job(self): #fixed
		print('Canceling job:')
		self.postREST('/printer/print/cancel', json=None)

	def pause_job(self): #fixed
		print('Pausing job:')
		self.postREST('/printer/print/pause', json=None)

	def resume_job(self): #fixed
		print('Resuming job:')
		self.postREST('printer/print/resume', json=None)

	def set_feedrate(self, fr):
		self.feedrate_percentage = fr
		self.sendGCode('M220 S%s' % fr)

	def home(self, homeZ=False): #fixed using gcode
		script = 'G28 X Y'
		if homeZ:
			script += (' Z')
		self.sendGCode(script)

	def moveRelative(self, axis, distance, speed):
		self.sendGCode('%s \n%s %s%s F%s%s' % ('G91', 'G1', axis, distance, speed,
			'\nG90' if self.absolute_moves else ''))

	def moveAbsolute(self, axis, position, speed):
		self.sendGCode('%s \n%s %s%s F%s%s' % ('G90', 'G1', axis, position, speed,
			'\nG91' if not self.absolute_moves else ''))

	def sendGCode(self, gcode):
		self.postREST('/printer/gcode/script', json={'script': gcode})

	def disable_all_heaters(self):
		self.setExtTemp(0)
		self.setBedTemp(0)

	def zero_fan_speeds(self):
		pass

	def preheat(self, profile):
		if profile == "PLA":
			self.preHeat(self.material_preset[0].bed_temp, self.material_preset[0].hotend_temp)
		elif profile == "ABS":
			self.preHeat(self.material_preset[1].bed_temp, self.material_preset[1].hotend_temp)

	def save_settings(self):
		print('saving settings')
		return True

	def setExtTemp(self, target, toolnum=0):
		self.sendGCode('M104 T%s S%s' % (toolnum, target))

	def setBedTemp(self, target):
		self.sendGCode('M140 S%s' % target)

	def preHeat(self, bedtemp, exttemp, toolnum=0):
# these work but invoke a wait which hangs the screen until they finish.
#		self.sendGCode('M140 S%s\nM190 S%s' % (bedtemp, bedtemp))
#		self.sendGCode('M104 T%s S%s\nM109 T%s S%s' % (toolnum, exttemp, toolnum, exttemp))
		self.setBedTemp(bedtemp)
		self.setExtTemp(exttemp)

	def setZOffset(self, offset):
		self.sendGCode('SET_GCODE_OFFSET Z=%s MOVE=1' % offset)
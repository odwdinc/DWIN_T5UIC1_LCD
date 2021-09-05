import requests
import json


class MoonrakerAPI():
	def __init__(self, address, port, api_key):
		self.s = requests.Session()
		self.s.headers.update({
			'Content-Type': 'application/json'
		})
		self.base_address = 'http://' + address + ':' + str(port)

	def getREST(self, path, compat=False):
		r = self.s.get(self.base_address + path)
		d = r.content.decode('utf-8')
		try:
			if compat:
				return json.loads(d)
			else:
				return json.loads(d)['result']
		except json.JSONDecodeError:
			print('Decoding JSON has failed')
		return None

	def postREST(self, path, json):
		self.s.post(self.base_address + path, json=json)

	def get_printer_info(self):
		data = self.getREST('/printer/objects/query?extruder&heater_bed')['status']
		state = {
			'temperature': {
				'bed': {
					'actual': data['heater_bed']['temperature'],
					'target': data['heater_bed']['target'],
				},
				'tool0': {
					'actual': data['extruder']['temperature'],
					'target': data['extruder']['target'],
				}
			}
		}
		return state

	def get_printer_profile(self):
		ppp = {}
		machine_info = self.getREST('/machine/update/status?refresh=false')
		ppp['model'] = machine_info['version_info']['klipper']['version']
		toolhead_info = self.getREST('/printer/objects/query?toolhead')['status']['toolhead']
		volume = toolhead_info['axis_maximum']
		ppp['volume'] = {
			'depth': volume[0],
			'width': volume[1],
			'height': volume[2],
		}
		return ppp

	def get_files(self):
		data = self.getREST('/server/files/list')
		for fl in data:
			fl['name'] = fl['path'] 
			fl['display'] = fl['path']
		return {
			'files': data
		}

	def get_job(self):
		data = self.getREST('/printer/objects/query?virtual_sdcard&print_stats')['status']
		state_map = {
			'paused': 'Paused',
			'pausing': 'Pausing',
			'printing': 'Printing',
			'operational': 'Operational',
			'complete': 'Operational',
			'standby': 'Operational',
			'cancelled': 'Operational',
		}
		state = state_map[data['print_stats']['state']]
		virtual_sdcard = data['virtual_sdcard']
		print_stats = data['print_stats']
		total_print_time = print_stats['print_duration'] / virtual_sdcard['progress']
		return {
			'job': {
				'file': {
					'name': data['print_stats']['filename']
				}
			},
			'state': state,
			'progress': {
				'completion': virtual_sdcard['progress']*100 if virtual_sdcard['is_active'] else 0,
				'printTimeLeft': total_print_time - print_stats['print_duration'],
				'printTime': print_stats['print_duration'],
			}
		}

	def print_file_local(self, filename):
		return self.postREST('/printer/print/start', json={'filename': filename})

	def send_gcode(self, gcode):
		return self.postREST('/printer/gcode/script', json={'script': gcode})

	def cancel_job(self):
		return self.postREST('/printer/print/cancel')

	def pause_job(self):
		return self.postREST('/printer/print/pause')

	def resume_job(self):
		return self.postREST('/printer/print/resume')

	def set_feedrate(self, fr):
		self.send_gcode('M220 S{}'.format(fr))

	def set_printhead(self, data):
		pass

	def set_printhead_axes(self, axes):
		axes = ''.join(i.upper() for i in axes)
		return self.send_gcode('G28 ' + axes)

	def set_bed_temp(self, temp=0):
		self.send_gcode('SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={}'.format(temp))

	def set_tool_temp(self, temp=0):
		self.send_gcode('SET_HEATER_TEMPERATURE HEATER=extruder TARGET={}'.format(temp))

	def set_tool(self, data):
		pass

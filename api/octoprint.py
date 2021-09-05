import requests
import json


class OctoPrintAPI():
	def __init__(self, address, port, api_key):
		self.s = requests.Session()
		self.s.headers.update({
			'X-Api-Key': api_key,
			'Content-Type': 'application/json'
		})
		self.base_address = 'http://' + address + ':' + str(port)

	def getREST(self, path):
		r = self.s.get(self.base_address + path)
		d = r.content.decode('utf-8')
		try:
			return json.loads(d)
		except json.JSONDecodeError:
			print('Decoding JSON has failed')
		return None

	def postREST(self, path, json):
		self.s.post(self.base_address + path, json=json)

	def get_printer_info(self):
		return self.getREST('/api/printer')

	def get_printer_profile(self):
		return self.getREST('/api/printerprofiles/_default')

	def get_files(self):
		return self.getREST('/api/files')

	def get_job(self):
		return self.getREST('/api/job')

	def print_file_local(self, filename):
		return self.postREST('/api/files/local/' + filename, json={'command': 'select', 'print': True})

	def send_gcode(self, gcode):
		return self.postREST('/api/printer/command', json={'command': gcode})

	def cancel_job(self):
		return self.postREST('/api/job', json={'command': 'cancel'})

	def pause_job(self):
		return self.postREST('/api/job', json={'command': 'pause'})

	def resume_job(self):
		return self.pause_job()

	def set_feedrate(self, fr):
		return self.postREST('/api/printer/printhead', json={'command': 'feedrate', 'factor': fr})

	def set_printhead(self, data):
		return self.postREST('/api/printer/printhead', json=data)

	def set_printhead_axes(self, axes):
		return self.set_printhead({'command': 'home', 'axes': axes})

	def set_bed_temp(self, temp=0):
		self.postREST('/api/printer/bed', json={'command': 'target', 'target': temp})

	def set_tool_temp(self, temp=0):
		self.postREST('/api/printer/tool', json={'command': 'target', 'targets': {"tool0": temp}})

	def set_tool(self, data):
		return self.postREST('/api/printer/tool', data)

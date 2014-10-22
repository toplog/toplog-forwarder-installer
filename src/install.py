 #!/usr/bin/env python
import pprint #TODO:REMOVE THIS
import urllib
import httplib
import json
import re
import os.path
import readline, glob

#TODO:REMOVE THIS
global toplog_server
toplog_server = "toplog.demo"


def request_toplog(endpoint, method):
	#endpoint = urllib.quote(endpoint)
	headers = {"Accept": "application/json"}
	connection = httplib.HTTPConnection(globals()["toplog_server"])
	request = connection.request(method, endpoint, '', headers)
	response = connection.getresponse()
	if(response.status != 404):
		body = response.read()
		data = json.loads(body)
	else:
		data = False
	connection.close()
	return data

def create_stream(token, path, user_type_id, stream_name):
	endpoint = "/streams?access_token=%(token)s&configuration_id=%(user_type_id)s&name=%(stream_name)s" % vars()
	response = request_toplog(endpoint, 'POST')

	if response:
		for file_config in response['files']:
			file_config['paths'] = [path]
			file_config['fields']['key'] = token
			return response
	else:
		print "Error: Could not create stream '%(stream_name)'. Please try again" % vars()
		exit()


def change_config():
	config_complete = False
	is_multiple = False
	token_valid = False
	while not config_complete:
		while not token_valid:
			print "Please enter your authentication token:"
			token = raw_input()
			endpoint = "/logs?access_token=%(token)s" % vars()
			types = request_toplog(endpoint, 'GET')
			if types:
				token_valid = True
			else:
				print "Error, authentication token not valid. Please re-enter or generate a new token"

		type_selected = False
		print "You have created the following log types:"
		for (type_id, name) in types.items():
			print "%(type_id)s: %(name)s\n" % vars()

		while not type_selected:
			print "Please enter the corresponding id number of the log type you wish to forward"
			user_type_id = raw_input()
			if(user_type_id.isdigit() and user_type_id in types):
				type_selected = True
			else:
				print "Error, log type not found"

		path_selected = False
		print "Please enter full path to the log file you wish to forward (example: /path/to/my.log)"

		while not path_selected:
			readline.set_completer_delims(' \t\n;')
			readline.parse_and_bind("tab: complete")
			path = raw_input()
			if os.path.isfile(path):
				path_selected = True
			else:
				print "File not found, please try again"

		print "Please enter a name for your stream:"
		stream_name = raw_input()
		stream_config = create_stream(token, path, user_type_id, stream_name)
		if is_multiple:
			previous_config['files'].append(stream_config['files'][0])

		confirm_valid = False
		while not confirm_valid:
			print "Would you like to create another stream [yes/no]?"
			confirm = raw_input()
			if (confirm.lower() == "y" or confirm.lower() == "yes"):
				if not is_multiple:
					previous_config = stream_config
					is_multiple = True
				confirm_valid = True
			elif (confirm.lower() == "n" or confirm.lower() == "no"):
				config_complete = True
				confirm_valid = True
			else:
				print "Error, invalid response. Please only enter 'yes' or 'no'"

		pprint.pprint(stream_config)

change_config()

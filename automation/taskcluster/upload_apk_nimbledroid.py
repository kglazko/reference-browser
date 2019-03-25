# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
This script talks to the taskcluster secrets service to obtain the
Nimbledroid account key and upload Klar and Focus apk to Nimbledroid for perf analysis.
"""

import taskcluster
import requests
import json
import urllib2
import os

url = "https://nimbledroid.com/api/v2/apks"

def uploadApk(apk,key):
	headers = {"Accept":"*/*"}
	payload = {'auto_scenarios':'false'}
	response = requests.post(url, auth=(key, ''), headers=headers, files=apk, data=payload)

	if response.status_code != 201:
		print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
		exit(1)

	# Print Response Details
	print 'Response Status Code:', response.status_code

	print ''
	print('Reponse Payload:')
	print json.dumps(response.json(), indent=4)

# Get JSON data from taskcluster secrets service
secrets = taskcluster.Secrets({'baseUrl': 'http://taskcluster/secrets/v1'})
data = secrets.get('project/mobile/reference-browser/nimbledroid')

rb_file_arm = {'apk': open('app/build/outputs/apk/geckoNightlyArm/debug/app-geckoNightly-arm-debug.apk')}

cwd = os.getcwd()
print cwd
# also upload the latest geckoview example from:
uploadApk(rb_file_arm, data['secret']['api_key'])
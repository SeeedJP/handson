# -*- coding: utf-8 -*-

WIO_SERVER_URL = "https://us.wio.seeed.io"
NODE_TOKEN = "8b0283811a669b90b7f3b8793454aaaa"
GENERIC_DOUT_PORT = "D0"

TURN_ON_URL = "{}/v1/node/GenericDOut{}/onoff/1?access_token={}".format(WIO_SERVER_URL, GENERIC_DOUT_PORT, NODE_TOKEN)
TURN_OFF_URL = "{}/v1/node/GenericDOut{}/onoff/0?access_token={}".format(WIO_SERVER_URL, GENERIC_DOUT_PORT, NODE_TOKEN)
GET_STATUS_URL = "{}/v1/node/GenericDOut{}/onoff_status?access_token={}".format(WIO_SERVER_URL, GENERIC_DOUT_PORT, NODE_TOKEN)

SAMPLE_APPLIANCES = [
	{
		"endpointId": "111-11111-11111-1001",
		"friendlyName": "テレビ",
		"manufacturerName": "Seeed",
		"description": "Wio Nodeの汎用デジタル出力",
		"displayCategories": [
			"SWITCH"
		],
		"capabilities": [
			{
				"type": "AlexaInterface",
				"interface": "Alexa.PowerController",
				"version": "3",
				"properties": {
					"supported": [
						{ "name" : "powerState" }
					],
					"proactivelyReported": False,
					"retrievable": True
				}
			},
			{
				"type": "AlexaInterface",
				"interface": "Alexa.EndpointHealth",
				"version": "3",
				"properties": {
					"supported":[
						{ "name":"connectivity" }
					],
					"proactivelyReported": False,
					"retrievable": True
				}
			}
		],
	}
]

import logging
import re
import sys
import time
import json
import uuid
import urllib.request

from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(request,context):
	try:
		logger.info("Directive:")
		logger.info(json.dumps(request, indent=4, sort_keys=True))

		if request["directive"]["header"]["name"] == "Discover":
			response = handleDiscovery(request)
		else:
			response = handleNonDiscovery(request)

		logger.info("Response:")
		logger.info(json.dumps(response, indent=4, sort_keys=True))

		validate_message(request, response)

		return response

	except ValueError as error:
		logger.error(error)
		raise

def handleDiscovery(request):
	endpoints = []
	for appliance in SAMPLE_APPLIANCES:
		endpoints.append(appliance)

	response = {
		"event": {
			"header": {
				"namespace": "Alexa.Discovery",
				"name": "Discover.Response",
				"payloadVersion": "3",
				"messageId": get_uuid()
			},
			"payload": {
				"endpoints": endpoints
			}
		}
	}
	return response

def handleNonDiscovery(request):
	request_namespace = request["directive"]["header"]["namespace"]
	request_name = request["directive"]["header"]["name"]

	if request_namespace == "Alexa.Authorization":
		if request_name == "AcceptGrant":
			logger.info("====== AcceptGrant directive is called. Authorization code is :" + request["directive"]["payload"]["grant"]["code"]);
			response = {
				"event": {
					"header": {
						"namespace": "Alexa.Authorization",
						"name": "AcceptGrant.Response",
						"payloadVersion": "3",
						"messageId": get_uuid()
					},
					"payload": {}
				}
			}
			return response

		#TODO elif request_name == "GrantRevoked"

	elif request_namespace == "Alexa.PowerController":

		#Do action

		if request_name == "TurnOn":
			value = "ON"
			status_code, body = sendHTTPRequest(TURN_ON_URL, "POST")
		else:
			value = "OFF"
			status_code, body = sendHTTPRequest(TURN_OFF_URL, "POST")

		#Do action end

		if (status_code == 200 and body["result"].upper() == "OK"):
			response = {
				"context": {
					"properties": [
						{
							"namespace": "Alexa.PowerController",
							"name": "powerState",
							"value": value,
							"timeOfSample": get_utc_timestamp(),
							"uncertaintyInMilliseconds": 500
						}
					]
				},
				"event": {
					"header": {
						"namespace": "Alexa",
						"name": "Response",
						"payloadVersion": "3",
						"messageId": get_uuid(),
						"correlationToken": request["directive"]["header"]["correlationToken"]
					},
					"endpoint": {
						"scope": {
							"type": "BearerToken",
							"token": "access-token-from-Amazon"
						},
						"endpointId": request["directive"]["endpoint"]["endpointId"]
					},
					"payload": {}
				}
			}
			return response
		else:
			## TODO: error response
			pass

	elif request_namespace == "Alexa":
		if request_name == "ReportState":
			status_code, body = sendHTTPRequest(GET_STATUS_URL)
			if (status_code == 200):
				value = "ON" if body["onoff"] == 1 else "OFF"
				response = {
					"context": {
						"properties": [
							{
								"namespace": "Alexa.PowerController",
								"name": "powerState",
								"value": value,
								"timeOfSample": get_utc_timestamp(),
								"uncertaintyInMilliseconds": 500
							},
							{
								"namespace": "Alexa.EndpointHealth",
								"name": "connectivity",
								"value": {
									"value": "OK"
								},
								"timeOfSample": get_utc_timestamp(),
								"uncertaintyInMilliseconds": 200
							}
						]
					},
					"event": {
						"header": {
							"namespace": "Alexa",
							"name": "StateReport",
							"payloadVersion": "3",
							"messageId": get_uuid(),
							"correlationToken": request["directive"]["header"]["correlationToken"]
						},
						"endpoint": {
					 		"scope": {
								"type": "BearerToken",
						 		"token": "access-token-from-Amazon"
					 		},
					 		"endpointId": request["directive"]["endpoint"]["endpointId"]
						},
						"payload": {}
					}
				}
				return response

			else:
				## TODO: error response
				pass

def get_utc_timestamp(seconds=None):
	return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))

def get_uuid():
	return str(uuid.uuid4())

def sendHTTPRequest(url, method="GET"):
	req = urllib.request.Request(url, method=method)
	try:
		with urllib.request.urlopen(req) as res:
			return res.status, json.load(res)
	except urllib.error.HTTPError as err:
		logger.info("sendHTTPRequest HTTPError:(%d) %s" % (err.code, err.reason))
		return  err.code, {}
	except urllib.error.URLError as err:
		logger.info("sendHTTPRequest URL Error:(%d) %s" % (err.code, err.reason))
		return  err.code, {}
	return

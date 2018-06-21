# -*- coding: utf-8 -*-


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

SAMPLE_APPLIANCES = [
				{
					"capabilities": [
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
						},
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
						}
					],
					"description": "スマートデバイスカンパニーのスマートプラグ",
					"displayCategories": [
						"SWITCH"
					],
					"endpointId": "111-11111-11111-1001",
					"friendlyName": "スイッチ",
					"manufacturerName": "スマートデバイスカンパニー"
				}
			]

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

	if request_namespace == "Alexa.PowerController":

		#Do action

		if request_name == "TurnOn":
			value = "ON"
			status_code, body = sendHTTPRequest("https:// ノードをONにするURLを設定","POST")
		else:
			value = "OFF"
			status_code, body = sendHTTPRequest("https:// ノードをOFFにするURLを設定","POST")

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
			status_code, body = sendHTTPRequest("https:// ノードの状態を取得するURLを設定")
			if (status_code == 200):
				value = "ON" if body["onoff"] == 1 else "OFF"
				response = {
					"context": {
						"properties": [
							{
								"namespace": "Alexa.EndpointHealth",
								"name": "connectivity",
								"value": {
									"value": "OK"
								},
								"timeOfSample": get_utc_timestamp(),
								"uncertaintyInMilliseconds": 200
							},
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

	elif request_namespace == "Alexa.Authorization":
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

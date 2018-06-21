# -*- coding: utf-8 -*-

WIO_SERVER_URL = "https://us.wio.seeed.io"

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
	access_token = request["directive"]["payload"]["scope"]["token"]

	endpoints = []

	status_code, nodes = sendHTTPRequest("{}/v1/nodes/list?access_token={}".format(WIO_SERVER_URL, access_token))
	for node in nodes["nodes"]:
		status_code, node_config = sendHTTPRequest("{}/v1/node/config?access_token={}".format(WIO_SERVER_URL, node["node_key"]))
		for node_connection in node_config["config"]["connections"]:
			print("{} {} {} {}".format(node["name"], node["node_key"], node_connection["port"], node_connection["sku"]))
			if node_connection["port"] == "D0" and node_connection["sku"] == "3a9d9a84-8c59-11e5-8994-feff819cdc9f":
				endpoints.append({
					"endpointId": node["node_key"],
					"friendlyName": "{} - {}".format(node["name"], node_connection["port"]),
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
				})

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

		node_token = request["directive"]["endpoint"]["endpointId"]

		#Do action

		if request_name == "TurnOn":
			value = "ON"
			status_code, body = sendHTTPRequest("{}/v1/node/GenericDOutD0/onoff/1?access_token={}".format(WIO_SERVER_URL, node_token), "POST")
		else:
			value = "OFF"
			status_code, body = sendHTTPRequest("{}/v1/node/GenericDOutD0/onoff/0?access_token={}".format(WIO_SERVER_URL, node_token), "POST")

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

			node_token = request["directive"]["endpoint"]["endpointId"]

			status_code, body = sendHTTPRequest("{}/v1/node/GenericDOutD0/onoff_status?access_token={}".format(WIO_SERVER_URL, node_token))
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

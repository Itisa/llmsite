import os
from openai import OpenAI
from volcenginesdkarkruntime import Ark
from django.core.cache import cache

from django.conf import settings

import time
import json
import requests
from django.utils import timezone
from mainsite.models_api import get_model_by_name, create_communication_content
import logging
logger = logging.getLogger(__name__)

class UserCommunicationContent:
	def __init__(self, cid):
		self.cid = cid
		self.last_index = 0
		self.reasoning_content = ""
		self.content = ""
		self.finished = False
		self.status = "queueing" # queueing / reasoning / content / done / failed
		self.have_get_info = False
		self.query_type = "" # reasoning / content
	
	def query_new_content(self):
		response_data = {

		}

		def Fail_RSP():
			response_data["cmd"] = "fail"
			yield json.dumps(response_data) + "\n"
			self.finished = True

		if not self.have_get_info:
			try:
				rsp = requests.get(f"http://127.0.0.1:8888/status?task_id={self.cid}")
				rsp_data = rsp.json()
				if rsp_data.get("status") == "error":
					logger.error(f"Task {self.cid} failed during processing. reason: {rsp_data.get('reason')}")
					Fail_RSP()
					return
				response_data["cmd"] = "info"
				response_data["model_name"] = rsp_data.get("model_name")
				response_data["model_type"] = rsp_data.get("model_type")
				if rsp_data.get("model_type") == "RS":
					self.query_type = "reasoning"
				else:
					self.query_type = "content"
					
				yield json.dumps(response_data) + "\n"
				
			except Exception as e:
				logger.error(f"Failed to query task status for comm {self.cid}: {e}")
				Fail_RSP()
				return 
			
			if rsp.status_code != 200:
				logger.error(f"Failed to query task status for comm {self.cid}: {rsp.status_code}")
				Fail_RSP()
				return 
			self.have_get_info = True

		try:
			rsp = requests.get(f"http://127.0.0.1:8888/content?task_id={self.cid}&last_index={self.last_index}&query_type={self.query_type}")
		except Exception as e:
			logger.error(f"Failed to query task status for comm {self.cid}: {e}")
			Fail_RSP()
			return 
		
		if rsp.status_code != 200:
			logger.error(f"Failed to query task status for comm {self.cid}: {rsp.status_code}")
			Fail_RSP()		
			return 
		
		rsp_data = rsp.json()
		print(rsp_data)
		self.status = rsp_data["status"]
		if rsp_data["status"] == "queueing":
			response_data["cmd"] = "queueing"
			yield json.dumps(response_data) + "\n"
			return 
		elif rsp_data["status"] == "failed":
			logger.error(f"Task {self.cid} failed during processing.")
			Fail_RSP()
			return
		
		elif self.query_type == "reasoning":
			new_content = rsp_data["reasoning_content"]
			self.reasoning_content += new_content
			self.last_index = len(self.reasoning_content)

			if rsp_data["status"] == "content":
				self.query_type = "content"
				self.last_index = 0
			elif rsp_data["status"] == "done":
				self.query_type = "content"
				self.last_index = 0
				
			response_data["cmd"] = "content"
			response_data["role"] = "reasoning"
			response_data["message"] = new_content
			yield json.dumps(response_data) + "\n"
		
		elif self.query_type == "content":
			new_content = rsp_data["content"]
			self.content += new_content
			self.last_index = len(self.content)
			if rsp_data["status"] == "done":
				self.finished = True
			
			response_data["cmd"] = "content"
			response_data["role"] = "content"
			response_data["message"] = new_content
			yield json.dumps(response_data) + "\n"
		else:
			logger.error(f"Unknown query type {self.query_type} for comm {self.cid}")
			self.finished = True
		return 

	def get_content(self):
		while True:
			yield from self.query_new_content()
			time.sleep(1)
			if self.finished:
				break
		return 	
		
def request_talk(cid, messages, model_name,params={}):
	post_data = {}
	post_data["task_id"] = str(cid)
	post_data["messages"] = messages
	post_data["model_name"] = model_name
	post_data["params"] = params
	rsp = requests.post(f"http://127.0.0.1:8888/submit",data=json.dumps(post_data))
	if rsp.status_code != 200:
		logger.error(f"Failed to submit task for comm {cid}: {rsp.status_code}")
		return "Error"
	elif rsp.json().get("status") == "fail":
		logger.warning(f"Failed to submit task for comm {cid}: {rsp.json()}")
		return "Queue Full"
	else:
		return "OK"

def update_comm_params(comm, params):
	comm.temperature = params["temperature"]
	comm.top_p = params["top_p"]
	comm.max_tokens = params["max_tokens"]
	comm.frequency_penalty = params["frequency_penalty"]
	comm.presence_penalty = params["presence_penalty"]

def yield_content(cid):
	UserComm = UserCommunicationContent(cid)
	yield from UserComm.get_content()

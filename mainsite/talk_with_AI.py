import os
from openai import OpenAI
from volcenginesdkarkruntime import Ark
from django.core.cache import cache

from django.conf import settings

import time
import json

from django.utils import timezone
from mainsite.models_api import get_model_by_name, create_communication_content

def update_comm_params(comm, params):
	comm.temperature = params["temperature"]
	comm.top_p = params["top_p"]
	comm.max_tokens = params["max_tokens"]
	comm.frequency_penalty = params["frequency_penalty"]
	comm.presence_penalty = params["presence_penalty"]

def talk_with_AI(comm,messages,model_name,params):
	model = get_model_by_name(model_name)
	if settings.TALK_TEST:
		time.sleep(3)
		content = ""
		reasoning_content = ""

		msglen = 4
		for i in range(msglen):  # 假设你生成10个JSON对象

			usercontent = messages[-1]["content"]
			data = {
				"id": i,
				"role": "assistant",
				"message": f"Message {i} **你好\n你好{usercontent}**\n\n",
				"cid": comm.pk,
				"title": comm.title,
			}

			if i == 0:
				data["message"] = json.dumps(params) + "\n"

			if i < msglen/2 and model.get_model_type_display() == "reasoning":
				data["role"] = "reasoning"
			yield json.dumps(data) + "\n"  # 每个JSON对象以换行符分隔
			if data["role"] == "assistant":
				content += data["message"]
			elif data["role"] == "reasoning":
				reasoning_content += data["message"]

			time.sleep(0.5)  # 模拟延迟
	else:
		
		if model.get_model_origin_display() == "deepseek":
			client = OpenAI(
				api_key = model.api_key,
				base_url = model.base_url,
			)
			
			response = client.chat.completions.create(
				model = model.model,
				messages = messages,
				stream = True,
				temperature = params["temperature"],
				top_p = params["top_p"],
				max_tokens = params["max_tokens"],
				frequency_penalty = params["frequency_penalty"],
				presence_penalty = params["presence_penalty"],
			)
			content_id = 0
			reasoning_content = ""
			content = ""
			data = {
				"cid": comm.pk,
				"title": comm.title,
			}
			for chunk in response:
				data["id"] = content_id
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					data["role"] = "reasoning"
					data["message"] = new_content
					yield json.dumps(data) + "\n"
					reasoning_content += new_content
				else:
					new_content = chunk.choices[0].delta.content
					data["role"] = "assistant"
					data["message"] = new_content
					yield json.dumps(data) + "\n"
					content += new_content
				content_id += 1
		
		elif model.get_model_origin_display() == "doubao":
			client = Ark(
				api_key = model.api_key
			)
			response = client.chat.completions.create(
				model = model.model,
				messages = messages,
				stream=True,
				temperature = params["temperature"],
				top_p = params["top_p"],
				max_tokens = params["max_tokens"],
				frequency_penalty = params["frequency_penalty"],
				presence_penalty = params["presence_penalty"],
			)

			data = {
				"cid": comm.pk,
				"title": comm.title,
				"role": "assistant"
			}
			content = ""
			content_id = 0
			for chunk in response:
				if not chunk.choices:
					continue
				new_content = chunk.choices[0].delta.content
				data["id"] = content_id
				data["message"] = new_content
				yield json.dumps(data) + "\n"
				content += new_content
				content_id += 1
		elif model.get_model_origin_display() == "openai":
			client = OpenAI(
				api_key = model.api_key,
				base_url = model.base_url,
			)
			
			response = client.chat.completions.create(
				model = model.model,
				messages = messages,
				stream = True,
				temperature = params["temperature"],
				top_p = params["top_p"],
				max_tokens = params["max_tokens"],
				frequency_penalty = params["frequency_penalty"],
				presence_penalty = params["presence_penalty"],
			)
			content_id = 0
			reasoning_content = ""
			content = ""
			data = {
				"cid": comm.pk,
				"title": comm.title,
			}
			for chunk in response:
				if hasattr(chunk.choices[0],'finish_reason') and chunk.choices[0].finish_reason != None:
					break
				data["id"] = content_id
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					data["role"] = "reasoning"
					data["message"] = new_content
					yield json.dumps(data) + "\n"
					reasoning_content += new_content
				else:
					new_content = chunk.choices[0].delta.content
					data["role"] = "assistant"
					data["message"] = new_content
					yield json.dumps(data) + "\n"
					content += new_content
				content_id += 1
			
	if model.get_model_type_display() == "reasoning":
		create_communication_content(comm,"reasoning",reasoning_content,model.model_origin)
	create_communication_content(comm,"assistant",content,model.model_origin)
	
	update_comm_params(comm,params)
	comm.save() # 触发comm时间的auto_now

def talk_limit_exceeded(comm, model_name, params):
	model = get_model_by_name(model_name)
	content = f"Your talk limit exceed today, please contact the administrator."
	data = {
		"id": 0,
		"role": "assistant",
		"message": content,
		"cid": comm.pk,
		"title": comm.title,
	}
	yield json.dumps(data) + "\n"
	create_communication_content(comm,"assistant",content,model.model_origin)
	
	update_comm_params(comm,params)
	comm.save()
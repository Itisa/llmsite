import os
from openai import OpenAI
from volcenginesdkarkruntime import Ark
from django.core.cache import cache

from django.conf import settings

import time
import json
import requests
from django.utils import timezone
from mainsite.models_api import write_failed_communication_to_database
import logging
import threading

from mainsite.models_api import *

logger = logging.getLogger(__name__)

def yield_content(cid):
	# rsp = {
	# 	"cmd" : "", # info / content / queueing / fail
	# 	"role":"",    # assistant / reasoning
	# 	"message":"", # content
	# }
	reasoning_index = 0
	content_index = 0
	dic = cache.get(cid)
	if dic is None:
		yield json.dumps({"cmd":"fail"}) + '\n'
		return 
	yield json.dumps({"cmd":"info","model_type":dic["model_type"]}) + '\n'

	def new_reasoning():
		nonlocal reasoning_index
		new_reasoning_content = dic["reasoning_content"][reasoning_index:]
		reasoning_index += len(new_reasoning_content)
		return json.dumps({"cmd":"content","role":"reasoning","message":new_reasoning_content}) + '\n'

	def new_content():
		nonlocal content_index
		new_content = dic["content"][content_index:]
		content_index += len(new_content)
		return json.dumps({"cmd":"content","role":"assistant","message":new_content}) + '\n'
	
	while True:
		dic = cache.get(cid)
		if dic is None:
			yield json.dumps({"cmd":"fail"}) + '\n'
			return 
		if dic["status"] == "reasoning":
			yield new_reasoning()
		elif dic["status"] == "content":
			if reasoning_index != len(dic["reasoning_content"]):
				yield new_reasoning()
			yield new_content()
		elif dic["status"] == "done":
			if reasoning_index != len(dic["reasoning_content"]):
				yield new_reasoning()
			if content_index != len(dic["content"]):
				yield new_content()
			break
		time.sleep(0.1)

def talk_with_AI(cid,model_name,messages,params):
	model = get_model_by_name(model_name)
	model_type = model.model_type
	comm = get_communication_by_cid(cid)
	dic = {}
	dic["model_type"] = model_type
	def update(**kwargs):
		dic["reasoning_content"] = reasoning_content
		dic["content"] = content
		dic["status"] = status
		cache.set(cid,dic,timeout=300)
		return 
	
	def end_cache():
		dic["status"] = "done"
		cache.set(cid,dic,timeout=10)
		return
	
	reasoning_content = ""
	content = ""
	status = "pending"
	update()
	if settings.TALK_TEST:
		t = 0
		output_text = f"杀杀杀杀杀水水水水水**水水**水水水水水水水水水水水水呃呃呃呃呃呃呃呃呃呃呃呃呃杀杀杀杀杀杀杀杀杀杀杀杀杀杀杀杀为非哦我房间王妃哦减肥我就根荣个人你给i哦就我改日哦哦i合同i耳机ioeg节日批改网irgju他忽然感觉 我怕热结果i而改为ig破i忘记她忽然就egoism 我i就提交人哦额外i就给i就公婆加热i偶就如果i欧俄日记给热键i偶尔结果哦i额日哦 鹅绒估计我就和他iu后i我{cid}"
		for chunk in output_text:
			t += 1
			if model_type == "RS" and t < 50:
				reasoning_content += chunk
				status = "reasoning"
				update(reasoning_content=reasoning_content,status="reasoning")
			else:
				content += chunk
				status = "content"
				update(content=content, status="content")
			time.sleep(0.07)
	else:
		if model.model_origin == "DS":
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
			
			for chunk in response:
			
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					reasoning_content += new_content
					status = "reasoning"
					update(reasoning_content=reasoning_content,status="reasoning")
				else:
					new_content = chunk.choices[0].delta.content
					content += new_content
					status = "content"
					update(content=content,status="content")
		
		elif model.model_origin == "DB":
			client = Ark(
				api_key = model.api_key,
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
			for chunk in response:
				if not chunk.choices:
					continue
				new_content = chunk.choices[0].delta.content
				content += new_content
				status = "content"
				update(content=content,status="content")
		
		elif model.model_origin == "OA":
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
			for chunk in response:
				if hasattr(chunk.choices[0],'finish_reason') and chunk.choices[0].finish_reason != None:
					break
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					reasoning_content += new_content
					status = "reasoning"
					update(reasoning_content=reasoning_content,status="reasoning")
				else:
					new_content = chunk.choices[0].delta.content
					content += new_content
					status = "content"
					update(content=content,status="content")
		
		elif model.model_origin == "KM":
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
			for chunk in response:
				delta = chunk.choices[0].delta
				if delta.content:
					new_content = delta.content
					content += new_content
					status = "content"
					update(content=content,status="content")
		elif model.model_origin == "QW":
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
			for chunk in response:
				if chunk.choices:
					delta = chunk.choices[0].delta
					if delta.content:
						new_content = delta.content
						content += new_content
						status = "content"
						update(content=content,status="content")
				elif chunk.usage: 
					# 需要在client.chat.completions.create()中加上stream_options={"include_usage": True}
					# 请求结束，打印Token用量。
					# print("\n--- 请求用量 ---")
					# print(f"输入 Tokens: {chunk.usage.prompt_tokens}")
					# print(f"输出 Tokens: {chunk.usage.completion_tokens}")
					# print(f"总计 Tokens: {chunk.usage.total_tokens}")
					pass

	if model_type == "RS":
		create_communication_content(comm,"reasoning",reasoning_content, model.model_origin)
	create_communication_content(comm,"assistant",content, model.model_origin)
	comm.status = "DN"
	comm.save()
	end_cache()

def new_talk(cid, messages, model_name, params):
	# print("收到new_talk================")
	# print(f"{cid=}")
	# print(f"{messages=}")
	# print(f"{model_name=}")
	# print(f"{params=}")
	# print("=============================")
	thread = threading.Thread(
		target=talk_with_AI,
		args=(cid, model_name, messages, params),
		name=f"talk_with_AI-{cid}-{int(time.time())}"
	)
	thread.daemon = True
	thread.start()
	return 'ok'

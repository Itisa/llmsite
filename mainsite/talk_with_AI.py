import os
from openai import OpenAI
from volcenginesdkarkruntime import Ark

talk_test = False
try:
	from .local_settings import talk_test
except:
	pass
import time
import json

from django.utils import timezone
from .models_api import get_model_by_name, create_communication_content

def talk_with_AI(comm,messages,model_name):
	model = get_model_by_name(model_name)
	if talk_test:
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
				"model": comm.model,
			}
			if i < msglen/2 and model.get_model_type_display() == "reasoning":
				data["role"] = "reasoning"
			yield json.dumps(data) + "\n"  # 每个JSON对象以换行符分隔
			if data["role"] == "assistant":
				content += data["message"]
			elif data["role"] == "reasoning":
				reasoning_content += data["message"]

			time.sleep(0.5)  # 模拟延迟
	else:
		
		if model.get_model_origin_display() == "deepseek" or model.get_model_origin_display() == "openai":
			client = OpenAI(
				api_key = model.api_key,
				base_url = model.base_url,
			)
			
			response = client.chat.completions.create(
				model = model.endpoint,
				messages = messages,
				stream = True,
			)
			content_id = 0
			reasoning_content = ""
			content = ""
			data = {
				"cid": comm.pk,
				"title": comm.title,
				"model": comm.model,
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
				model = model.endpoint,
				messages = messages,
				stream=True
			)

			data = {
				"cid": comm.pk,
				"title": comm.title,
				"model": comm.model,
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
			
	if model.get_model_type_display() == "reasoning":
		create_communication_content(comm,"reasoning",reasoning_content)
	create_communication_content(comm,"assistant",content)
	comm.save() # 触发comm时间的auto_now
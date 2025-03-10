import os
from openai import OpenAI
from .local_settings import *
import time
import json

from .models import User, Communication, Communication_Content
from django.utils import timezone
def talk_with_AI(comm,messages,model_name="deepseek_v3"):
	if talk_test:
		content = ""
		reasoning_content = ""
		gen_date = timezone.now()

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
			if i < msglen/2 and model_name == "deepseek_r1":
				data["role"] = "reasoning"
			yield json.dumps(data) + "\n"  # 每个JSON对象以换行符分隔
			if data["role"] == "assistant":
				content += data["message"]
			elif data["role"] == "reasoning":
				reasoning_content += data["message"]

			time.sleep(0.5)  # 模拟延迟
	else:
		if model_name in available_models_volcano: # 火山云
			client = OpenAI(
				api_key=volcano_api_key,
				base_url="https://ark.cn-beijing.volces.com/api/v3",
				timeout=1800,
			)

			gen_date = timezone.now()
			response = client.chat.completions.create(
				model=volcano_ENDPOINT_ID[model_name],
				messages=messages,
				stream=True,
			)
			content_id = 0
			reasoning_content = ""
			content = ""
			for chunk in response:
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					data = {
						"id": content_id,
						"message": new_content,
						"cid": comm.pk,
						"title": comm.title,
						"model": comm.model,
						"role": "reasoning",
					}
					yield json.dumps(data) + "\n"
					reasoning_content += new_content
				else:
					new_content = chunk.choices[0].delta.content
					data = {
						"id": content_id,
						"message": new_content,
						"cid": comm.pk,
						"title": comm.title,
						"model": comm.model,
						"role": "assistant",
					}
					yield json.dumps(data) + "\n"
					content += new_content
				content_id += 1
		
		elif model_name in available_models_deepseek: #deepseek官方api
			client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

			gen_date = timezone.now()
			response = client.chat.completions.create(
				model=deepseek_model_name[model_name],
				messages=messages,
				stream=True
			)
			content_id = 0
			reasoning_content = ""
			content = ""
			for chunk in response:
				if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
					new_content = chunk.choices[0].delta.reasoning_content
					data = {
						"id": content_id,
						"message": new_content,
						"cid": comm.pk,
						"title": comm.title,
						"model": comm.model,
						"role": "reasoning",
					}
					yield json.dumps(data) + "\n"
					reasoning_content += new_content
				else:
					new_content = chunk.choices[0].delta.content
					data = {
						"id": content_id,
						"message": new_content,
						"cid": comm.pk,
						"title": comm.title,
						"model": comm.model,
						"role": "assistant",
					}
					yield json.dumps(data) + "\n"
					content += chunk.choices[0].delta.content
	
	if model_name in ["deepseek_r1_火山云","deepseek_r1"]:
		comm.communication_content_set.create(gen_date=gen_date,role="reasoning",content=reasoning_content)

	comm.communication_content_set.create(gen_date=gen_date,role="assistant",content=content)
	comm.save()

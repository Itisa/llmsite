import os
from openai import OpenAI
from .secret_settings import volc_api_key,ENDPOINT_ID
import time
import json

from .models import User, Communication, Communication_Content
from django.utils import timezone
def talk_with_AI(comm,messages,model_name="deepseek_v3",base_url="https://ark.cn-beijing.volces.com/api/v3"):
	test = False
	if test:
		allcontent = ""
		reasoning_content = ""
		gen_date = timezone.now()
		for i in range(10):  # 假设你生成10个JSON对象
			usercontent = messages[-1]["content"]
			data = {
				"id": i,
				"role": "assistant",
				"message": f"Message {i} **你好你好{usercontent}**\n\n",
				"cid": comm.pk,
				"title": comm.title,
				"model": comm.model,
			}
			if i < 5 and model_name == "deepseek_r1":
				data["role"] = "reasoning"
			yield json.dumps(data) + "\n"  # 每个JSON对象以换行符分隔
			if data["role"] == "assistant":
				allcontent += data["message"]
			elif data["role"] == "reasoning":
				reasoning_content += data["message"]

			time.sleep(1)  # 模拟延迟
	else:
		client = OpenAI(
			api_key=volc_api_key,
			base_url=base_url,
			timeout=1800,
		)

		gen_date = timezone.now()
		response = client.chat.completions.create(
			model=ENDPOINT_ID[model_name],
			messages=messages,
			stream=True,
		)
		content_id = 0
		reasoning_content = ""
		allcontent = ""
		for chunk in response:
			if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
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
				allcontent += new_content
			content_id += 1
	
	# print(reasoning_content)
	# print(allcontent)
	if model_name == "deepseek_r1":
		comm.communication_content_set.create(gen_date=gen_date,role="reasoning",content=reasoning_content)

	comm.communication_content_set.create(gen_date=gen_date,role="assistant",content=allcontent)
	comm.save()

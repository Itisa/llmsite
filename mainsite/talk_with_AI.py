import os
from openai import OpenAI
from .secret_settings import volc_api_key,ENDPOINT_ID
import time
import json

from .models import User, Communication, Communication_Content
from django.utils import timezone
def talk_with_AI(comm,messages,model_name="deepseek_v3",base_url="https://ark.cn-beijing.volces.com/api/v3"):

	allcontent = ""
	gen_date = timezone.now()
	for i in range(10):  # 假设你生成10个JSON对象
		usercontent = messages[-1]["content"]
		data = {
			"id": i,
			"message": f"Message {i} **你好你好{usercontent}**\n\n",
			"cid": comm.pk,
			"title": comm.title,
			"model": comm.model,
		}
		yield json.dumps(data) + "\n"  # 每个JSON对象以换行符分隔
		allcontent += data["message"]

		time.sleep(1)  # 模拟延迟

	# client = OpenAI(
	# 	api_key=volc_api_key,
	# 	base_url=base_url,
	# 	timeout=1800,
	# )
	# gen_date = timezone.now()
	# response = client.chat.completions.create(
	# 	model=ENDPOINT_ID[model_name],
	# 	messages=messages,
	# 	stream=True,
	# )
	# allcontent = ""
	# print("\033[91mStart print rsp\033[0m")
	# content_id = 0
	# for chunk in response:
	# 	print("chunk:", chunk)
	# 	# if 'choices' in chunk:
	# 	if hasattr(chunk,"choices"):
	# 		print(1111)
	# 		print("choices:",chunk.choices)
	# 		print()
	# 		content = chunk.choices[0].delta.content
	# 		data = {
	# 			"id": content_id,
	# 			"message": content,
	# 		}
	# 		yield json.dumps(data) + "\n"
	# 		print(content, end='', flush=True)
	# 		allcontent += content
	# print("\033[91mEnd print rsp\033[0m")
	# print(allcontent)

	# end_time = time.time()
	# print(f"duration: {end_time - start_time}")
	# # 当触发深度推理时，打印思维链内容
	# if hasattr(response.choices[0].message, 'reasoning_content'):
	# 	print(response.choices[0].message.reasoning_content)
	# print("LINE 21")
	# print("LINE 22")
	# print(response.choices[0].message.content)
	# return response.choices[0].message.content

	comm.communication_content_set.create(gen_date=gen_date,role="assistant",content=allcontent)
	comm.save()

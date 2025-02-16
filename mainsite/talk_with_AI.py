import os
from openai import OpenAI
from api_keys import *
import time

def talk_with_AI(model_name,messages):
	return messages[-1]["content"].swapcase()
	# start_time = time.time()
	# client = OpenAI(
	# 	api_key=volc_api_key,
	# 	base_url="https://ark.cn-beijing.volces.com/api/v3",
	# 	timeout=1800,
	# 	)

	# # question = "我想使用alpinejs写一个与deepseek交互的前端网页，需要有用户登录与历史对话记录，请给出网页的层次结构与大致的代码"
	# question = "在Django的教程中有这么一段代码，question = models.ForeignKey(Question, on_delete=models.CASCADE)，请问这里的 on_delete=models.CASCADE 是什么意思，有什么用"
	# response = client.chat.completions.create(
	# 	model=ENDPOINT_ID["deepseek_v3"],
	# 	messages=[
	# 		{"role": "user", "content": question}
	# 	],
	# 	stream=False,
	# )

	# end_time = time.time()
	# print(f"duration: {end_time - start_time}")
	# # 当触发深度推理时，打印思维链内容
	# if hasattr(response.choices[0].message, 'reasoning_content'):
	# 	print(response.choices[0].message.reasoning_content)
	# print("LINE 21")
	# print("LINE 22")
	# print(response.choices[0].message.content)

import os
from openai import OpenAI
from api_keys import *
import time

def talk_with_AI(model_name,messages):
	return messages[-1]["content"].swapcase()
	start_time = time.time()
	client = OpenAI(
		api_key=volc_api_key,
		base_url="https://ark.cn-beijing.volces.com/api/v3",
		timeout=1800,
		)

	
	question = "你好！"
	response = client.chat.completions.create(
		model=ENDPOINT_ID["deepseek_v3"],
		messages=[
			{"role": "user", "content": question}
		],
		stream=False,
	)

	end_time = time.time()
	print(f"duration: {end_time - start_time}")
	# 当触发深度推理时，打印思维链内容
	if hasattr(response.choices[0].message, 'reasoning_content'):
		print(response.choices[0].message.reasoning_content)
	print("LINE 21")
	print("LINE 22")
	print(response.choices[0].message.content)

import os
from openai import OpenAI
from .secret_settings import volc_api_key,ENDPOINT_ID
import time

def talk_with_AI(messages,model_name="deepseek_v3",base_url="https://ark.cn-beijing.volces.com/api/v3"):
	return messages[-1]["content"].swapcase();
	start_time = time.time()
	client = OpenAI(
		api_key=volc_api_key,
		base_url=base_url,
		timeout=1800,
	)
	
	response = client.chat.completions.create(
		model=ENDPOINT_ID[model_name],
		messages=messages,
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
	return response.choices[0].message.content

from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from mainsite.models import Api_config
import json
class Command(BaseCommand):
	help = '从mainsite/api_config.json里读取api配置文件'

	def handle(self, *args, **kwargs):
		# 在这里编写你的脚本逻辑
		file_path = Path(settings.BASE_DIR) / 'mainsite' / 'api_config.json'
		data = json.loads(file_path.read_text(encoding='utf-8'))
		for api in data:
			try:
				name = api["name"]
				api_key = api["api_key"]
				endpoint = api["endpoint"]
				base_url = api.get("base_url","")
				model_type = api.get("model_type","chat")
				model_origin = api.get("model_origin","openai")

				name_qst = Api_config.objects.filter(name=name)
				if len(name_qst) == 0:
					aa = Api_config(
						name=name,
						api_key=api_key,
						endpoint=endpoint,
						base_url=base_url,
						model_type=model_type,
						model_origin=model_origin
					)
					aa.save()
					self.stdout.write(f"new api {api}")
			except KeyError as e:
				self.stdout.write(f"ERROR: Key not found: {e}")
		# 示例：调用其他函数
		self.my_custom_function()

	def my_custom_function(self):
		# 这里是你的自定义逻辑
		self.stdout.write(self.style.SUCCESS('读取api配置到数据库成功！'))

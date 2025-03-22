from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from mainsite.models import Api_config
import json
class Command(BaseCommand):
	help = '将api配置文件写入mainsite/api_config.json'

	def handle(self, *args, **kwargs):
		file_path = Path(settings.BASE_DIR) / 'mainsite' / 'api_config.json'
		data = []
		for api in Api_config.objects.all():
			data.append({
				"name": api.name,
				"base_url": api.base_url,
				"api_key": api.api_key,
				"model": api.model,
				"model_type": api.model_type,
				"model_origin": api.model_origin
			})
		file_path.write_text(json.dumps(data,indent='\t',ensure_ascii=False), encoding='utf-8')
		self.stdout.write("保存api配置至文件成功")
from django.core.management.base import BaseCommand
from django.core.cache import cache
class Command(BaseCommand):
	help = '初始化'

	def handle(self, *args, **kwargs):
		from mainsite.models import GlobalSetting
		def get_setting(name):
			try:
				u = GlobalSetting.objects.get(key=name)
				return u
			except:
				return None
		def init_setting(key,value,comment=""):
			g = get_setting(key)
			if g is None:
				g = GlobalSetting(key=key,value=value,comment=comment)
				g.save()

			return g

		init_setting("can_register", "False", "设置为True以允许注册")
		
		init_setting("website_name", "网站名称", "网站名称")

		print("初始化成功！")

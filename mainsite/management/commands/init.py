from django.core.management.base import BaseCommand
from django.core.cache import cache
class Command(BaseCommand):
	help = '初始化一些经常改变的全局设置（写入数据库）'

	def handle(self, *args, **kwargs):
		from mainsite.models import GlobalSetting
		if GlobalSetting.objects.all().count() == 0:
			g = GlobalSetting()
			g.save()

		print("初始化成功！")

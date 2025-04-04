from django.core.management.base import BaseCommand
from django.core.cache import cache
class Command(BaseCommand):
	help = '删除缓存'

	def handle(self, *args, **kwargs):
		cache.delete("models")
		cache.delete("typed_models")
		self.stdout.write(self.style.SUCCESS('删除缓存成功！'))

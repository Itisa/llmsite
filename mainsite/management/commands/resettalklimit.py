from django.core.management.base import BaseCommand
from mainsite.models import User, GlobalSetting
from django.db.models import Case, When, Value
class Command(BaseCommand):
	help = '重置用户的询问次数上限'

	def handle(self, *args, **kwargs):
		limit = GlobalSetting.objects.all().first().user_talk_limit
		User.objects.all().update(
			user_talk_cnt_left = Case(
				When(user_type='AD', then=Value(-1)),
				default=Value(limit)
			)
		)
		self.stdout.write("重置成功")
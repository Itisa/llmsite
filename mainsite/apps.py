from django.apps import AppConfig


class MainsiteConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'mainsite'

	def ready(self):
		from mainsite.tasks import start_scheduler
		start_scheduler()
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from mainsite.models_api import reset_user_talk_limit
from django.db.models import Case, When, Value
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
	return 
	scheduler = BackgroundScheduler()
	scheduler.add_jobstore(DjangoJobStore(), "default")
	
	scheduler.add_job(
		reset_user_talk_limit,
		'cron',
		hour=0,
		id='reset_user_talk_limit',
		replace_existing=True
	)
	logger.info("starting scheduler...")
	scheduler.start()
	logger.info("scheduler started...")

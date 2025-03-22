from .models import User, Communication, Communication_Content, Mailbox, Api_config
import logging
import bcrypt
from django.utils import timezone
from django.core.cache import cache
import platform
logger = logging.getLogger(__name__)
def add_user(username,password,user_type="NM"):
	user_qst = User.objects.filter(username=username)
	if len(user_qst) != 0:
		return False
	hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
	new_user = User(username=username,user_password=hashed_password.decode(),user_type=user_type)
	new_user.save()
	return True

def add_tmp_user(username,password):
	user_qst = User.objects.filter(username=username)
	if len(user_qst) != 0:
		return False
	hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
	new_user = User(username=username,user_password=hashed_password.decode(),user_type="TM")
	new_user.save()
	return True

def delete_user(username):
	try:
		user = User.objects.get(username=username)
		user.delete()
		return True
	except:
		return False

def get_user_by_sessionid(sessionid):
	u = None
	try:
		u = User.objects.get(sessionid=sessionid)
	except User.DoesNotExist:
		pass
	return u

def get_user_by_username(username):
	u = None
	try:
		u = User.objects.get(username=username)
	except User.DoesNotExist:
		pass
	return u

def add_mailbox(user,title,content):
	mm = Mailbox(user=user,title=title,content=content)
	mm.save()

def create_communication(user,model_name,title):
	comm = user.communication_set.create(model=model_name,title=title)
	return comm

def get_communication_by_pk(pk):
	u = None
	try:
		u = Communication.objects.get(pk=pk)
	except Communication.DoesNotExist:
		logger.error(f"no Communication found pk={pk}")
		print("Communication.DoesNotExist")
		print("pk:",pk)
		print("type",type(pk))
		pass
	return u

def create_communication_content(communication,role,content):
	cc = communication.communication_content_set.create(role=role,content=content)
	return cc

def get_model_by_name(model_name):
	u = None
	try:
		u = Api_config.objects.get(name=model_name)
	except:
		pass
	return u

def if_user_valid(user):
	if user == None:
		return False
	if user.get_user_status_display() == "forbidden":
		return False
	if user.sessionid_expire < timezone.now():
		if user.get_user_type_display() == "temporary":
			if user.sessionid_expire != timezone.datetime.min:
				# user.delete() ########################################################
				pass
		return False
	return True

def get_models():
	if platform.system() == "Linux":
		cached_models = cache.get('models')
		if cached_models is None:
			models = []
			for model in Api_config.objects.all():
				models.append(model.name)
			cache.set('models',models)
			return models
		else:
			return cached_models
	else:
		models = []
		for model in Api_config.objects.all():
			models.append(model.name)
		return models

def get_typed_models():
	if platform.system() == "Linux":
		cached_typed_models = cache.get('typed_models')
		if cached_typed_models is None:
			typed_models = []
			for model in Api_config.objects.all():
				typed_models.append({"name":model.name,"type":model.get_model_type_display()})
			cache.set('typed_models',typed_models)
			return typed_models
		else:
			return cached_typed_models
	else:
		typed_models = []
		for model in Api_config.objects.all():
			typed_models.append({"name":model.name,"type":model.get_model_type_display()})
		return typed_models

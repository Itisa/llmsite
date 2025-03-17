from .models import User, Communication, Communication_Content, Mailbox, Api_config
import logging
import bcrypt
from django.utils import timezone
logger = logging.getLogger(__name__)
def add_user(username,password):
	user_qst = User.objects.filter(username=username)
	if len(user_qst) != 0:
		return False
	hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
	new_user = User(username=username,user_password=hashed_password.decode())
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
	if user.sessionid_expire < timezone.now():
		if user.get_user_type_display() == "temporary":
			if user.sessionid_expire != timezone.datetime.min:
				# user.delete() ########################################################
				pass
		return False
	return True

def get_models():
	models = []
	for model in Api_config.objects.all():
		models.append(model.name)
	return models
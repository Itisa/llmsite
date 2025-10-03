from .models import User, Communication, Communication_Content, Mailbox, Api_config, GlobalSetting, Ds2pdf_report
import logging
import bcrypt
import uuid
from django.utils import timezone
from django.core.cache import cache
from django.db.models import F, Case, When, Value

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

def create_communication(user,title,model_name):
	cid = uuid.uuid4().hex
	comm = user.communication_set.create(cid=cid,title=title,model=model_name)
	return comm

# def get_communication_by_pk(pk):
# 	u = None
# 	try:
# 		u = Communication.objects.get(pk=pk)
# 	except Communication.DoesNotExist:
# 		logger.error(f"no Communication found pk={pk}")
# 		print("Communication.DoesNotExist")
# 		print("pk:",pk)
# 		print("type",type(pk))
# 		pass
# 	return u

def get_communication_by_cid(cid):
	u = None
	try:
		u = Communication.objects.get(cid=cid)
	except Communication.DoesNotExist:
		logger.error(f"no Communication found cid={cid}")
		print("Communication.DoesNotExist")
		print("cid:",cid)
		print("type",type(cid))
		pass
	return u

def create_communication_content(communication,role,content,model='NN'):
	cc = Communication_Content(communication=communication,role=role,content=content,model=model)
	cc.save()
	return cc

def get_model_by_name(model_name):
	u = None
	try:
		u = Api_config.objects.get(name=model_name)
	except:
		pass
	return u

def if_user_valid(user):
	if user is None:
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
	cached_models = cache.get('models')
	if cached_models is None:
		models = []
		for model in Api_config.objects.filter(disabled=False).order_by("pk"):
			models.append(model.name)
		cache.set('models',models)
		return models
	else:
		return cached_models

def get_typed_models():
	cached_typed_models = cache.get('typed_models')
	if cached_typed_models is None:
		typed_models = []
		for model in Api_config.objects.filter(disabled=False).order_by("pk"):
			typed_models.append({"name":model.name,"type":model.get_model_type_display(), "origin":model.get_model_origin_display()})
		cache.set('typed_models',typed_models)
		return typed_models
	else:
		return cached_typed_models

def get_model_origin_by_name(name):
	cached_model_origin = cache.get(f'model_origin_{name}')
	if cached_model_origin is None:
		model = get_model_by_name(name)
		if model is None:
			ret = 'NN'
		else:
			ret = model.model_origin;
		cache.set(f'model_origin_{name}',ret)
		return ret
	else:
		return cached_model_origin

def get_setting():
	return GlobalSetting.objects.all().first()

def is_enable_register():
	s = get_setting()
	return s.enable_register

def get_website_name():
	s = get_setting()
	return s.website_name
	
def get_user_talk_limit():
	s = get_setting()
	return s.user_talk_limit

def user_try_talk(user):
	cnt = user.user_talk_cnt_left
	if cnt == 0:
		return False
	if cnt == -1:
		return True
	user.user_talk_cnt_left = F("user_talk_cnt_left") - 1
	user.save()
	return True

def reset_user_talk_limit():
	limit = get_user_talk_limit()
	User.objects.all().update(
		user_talk_limit = Case(
			When(user_type='AD', then=Value(-1)),
			default=Value(limit)
		)
	)

def update_comm_params(comm, params):
	comm.temperature = params["temperature"]
	comm.top_p = params["top_p"]
	comm.max_tokens = params["max_tokens"]
	comm.frequency_penalty = params["frequency_penalty"]
	comm.presence_penalty = params["presence_penalty"]
	comm.save()

def new_ds2pdf_report(content,description):
	report = Ds2pdf_report(content=content,description=description)
	report.save();
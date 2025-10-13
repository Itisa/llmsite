from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import json
import bcrypt
import random
import string
import datetime
import logging
import requests
logger = logging.getLogger(__name__)

from .models_api import *
from .talk_with_AI import request_talk, yield_content

def _redirect2loginResponse():
	response = HttpResponseRedirect(reverse("mainsite:login"))
	# response.delete_cookie('sessionid')
	# response.delete_cookie('username')
	return response

def _NoAuthResponse():
	response = HttpResponse('Unauthorized', status=401)
	# response.delete_cookie('sessionid')
	# response.delete_cookie('username')
	return response

class require_user:
	'''decorator'''
	def __init__(self,request_type):
		self.request_type = request_type

	def __call__(self,func):
		def wrapper(*args, **kwargs):
			request = args[0]
			if not if_user_valid(request.User):
				if request.method == "GET" and self.request_type == "page":
					return _redirect2loginResponse()
				else:
					return _NoAuthResponse()
			result = func(*args, **kwargs)
			return result
		return wrapper

def _generate_random_string(length):
	characters = string.ascii_letters + string.digits  # 字母和数字
	return ''.join(random.choices(characters, k=length))

def _get_params_from_dict(dic):
	params = {}
	params["temperature"] = dic.get("temperature",1)
	params["top_p"] = dic.get("top_p",1)
	params["max_tokens"] = dic.get("max_tokens",4096)
	params["frequency_penalty"] = dic.get("frequency_penalty",0)
	params["presence_penalty"] = dic.get("presence_penalty",0)
	def ensure_range(val,l,r,paramname=""):
		if l <= val and val <= r:
			return
		logger.warning(f"illegal param {val}, except [{l}, {r}]")
		raise Exception(f"illegal params: {paramname} except [{l}, {r}] got {val}")

	ensure_range(params["temperature"],0,2,"temperature")
	ensure_range(params["top_p"],0,1,"top_p")
	ensure_range(params["max_tokens"],1,8192,"max_tokens")
	ensure_range(params["frequency_penalty"],-2,2,"frequency_penalty")
	ensure_range(params["presence_penalty"],-2,2,"presence_penalty")
	return params

@require_http_methods(["GET"])
@require_user("page")
def site(request):
	data = {
		"website_name" : get_website_name(),
	}
	rsp = render(request,"mainsite/mainsite.html",data)
	return rsp

@require_http_methods(["GET","POST"])
def login(request):
	if request.method == "GET":
		if request.User:
			return HttpResponseRedirect(reverse("mainsite:site"))
		data = {
			"website_name" : get_website_name(),
		}
		return render(request,"mainsite/login.html",data)
	elif request.method == "POST":
		username = request.POST.get("username","")
		password = request.POST.get("password","")
		
		user = get_user_by_username(username)
		if user is None:
			return JsonResponse({"status": "fail","reason": "user not exist or incorrect password"}, status=200)

		if bcrypt.checkpw(password.encode(), user.user_password.encode()):
			if user.user_status == "FD":
				return JsonResponse( {"status": "fail","reason": "user forbidden"}, status=200)
			sessionid = _generate_random_string(20)
			user.sessionid = sessionid
			user.sessionid_expire = timezone.now() + datetime.timedelta(days=14)

			if user.user_type == "TM" and user.user_status == "NM": # 临时用户，第二次登陆就禁止了
				user.user_status = "FD"
				user.save()
				return JsonResponse( {"status": "fail","reason": "user forbidden"}, status=200)

			if user.user_status == "NL":
				user.user_status = "NM"
			user.save()
			request.session["id"] = sessionid
			rsp = JsonResponse({"status": "success"}, status=200)
			rsp.set_cookie("username",username,max_age=1209600)
			return rsp
		else:
			return JsonResponse({"status": "fail","reason": "user not exist or incorrect password"}, status=200)

@require_http_methods(["GET","POST"])
def register(request):
	if request.method == "GET":
		if is_enable_register():
			data = {
				"website_name" : get_website_name(),
			}
			return render(request,"mainsite/register.html")
		else:
			return HttpResponse("注册暂时不可用，请与管理员联系")
	elif request.method == "POST":
		if not is_enable_register():
			return JsonResponse( {"status": "fail","reason": "register unavailable",}, status=200)
		
		username = request.POST.get("username","")
		password = request.POST.get("password","")
		invitation_code = request.POST.get("invitation_code","")

		if add_user(username,password):
			return JsonResponse({"status": "success",}, status=200)
		else:
			return JsonResponse({"status": "fail","reason": "username exist"}, status=200)

@require_http_methods(["GET","POST"])
@require_user("data")
def change_password(request):
	if request.method == "GET":
		data = {
			"website_name" : get_website_name(),
		}
		return render(request,"mainsite/change_password.html",data)
	elif request.method == "POST":
		user = request.User

		logger.info(f"user {user} change_password")
		ori_password = request.POST.get("ori_password","")
		
		if not bcrypt.checkpw(ori_password.encode(), user.user_password.encode()):
			return JsonResponse({"status": "fail","reason": "ori_password error"}, status=200)

		if not "new_password" in request.POST.keys():
			return JsonResponse({"status": "fail","reason": "no new_password"}, status=200)

		new_password = request.POST.get("new_password")

		user.user_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
		user.save()
		return JsonResponse({"status": "success"}, status=200)

@require_http_methods(["GET"])
@require_user("page")
def logout(request):
	rsp = HttpResponseRedirect(reverse("mainsite:login"))
	rsp.delete_cookie("sessionid")
	rsp.delete_cookie("username")
	return rsp

@require_http_methods(["GET"])
@require_user("data")
def get_available_models(request):
	try:
		rsp = requests.get(settings.AI_SERVER_HOST+":"+str(settings.AI_SERVER_PORT)+"/health",timeout=1)	
		return JsonResponse({'status': 'ok', 'data': get_typed_models(), 'talk_test': rsp.json().get("talk_test",False)},status=200)
	except Exception as e:
		return JsonResponse({'status': 'AI server down', 'data': get_typed_models()},status=200)
		
@require_http_methods(["GET"])
@require_user("data")
def get_history(request):
	titles = []
	query = request.User.communication_set.all() # 不用排序，前端会排序
	for comm in query.iterator():
		titles.append({"title":comm.title,"model":comm.model,"date":comm.gen_date,"id":comm.cid,"starred":comm.starred})
	return JsonResponse({'status': 'ok', 'titles': titles},status=200)

@require_http_methods(["GET"])
@require_user("data")
def get_communication_content(request):
	cid = request.GET["cid"]
	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'error', 'reason': 'no communication'}, status=200)
	if comm.user.pk != request.User.pk:
		return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=200)
	messages = []
	qst = comm.communication_content_set.all().order_by('gen_date')
	for msg in qst:
		messages.append({"role":msg.role,"content":msg.content,"model":msg.get_model_display()})
	if comm.status == "QR":
		messages.append({"role":"querying","content":"","model":"none"})
	return JsonResponse({'status': 'ok', 'messages': messages},status=200)

@require_http_methods(["POST"])
@require_user("data")
def post_message(request):
	try:
		data = json.loads(request.body)
	except:
		data = {}
	if not user_try_talk(request.User):
		return JsonResponse({'status': 'error', 'reason': 'talk limit exceeded'}, status=200)
	
	model_name = data.get('model_name',"")
	if not model_name in get_models():
		return JsonResponse({'status': 'error', 'reason': 'model not supported'}, status=200)	
	message = data.get('message',"")
	system = data.get('system',"")
	cid = data.get('cid',"")

	try:
		params = _get_params_from_dict(data)
	except Exception as e:
		return JsonResponse({'status': 'error', 'reason': 'illegal params'}, status=200)

	# 获取对话
	if cid == "":
		comm = create_communication(request.User,message[:30],model_name)
	else:
		comm = get_communication_by_cid(cid)
		if comm is None:
			return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=200)

		if comm.user.pk != request.User.pk:
			return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=200)
	update_comm_params(comm, params)
	comm.model = model_name
	comm.system = system
	create_communication_content(comm, "user", message, get_model_origin_by_name(model_name))

	messages = []
	if system != "":
		messages.append({"role": "system", "content": system})
	for msg in comm.communication_content_set.all().order_by('pk'):
		if msg.role == "reasoning":
			continue
		messages.append({"role" : msg.role,"content":msg.content})
	messages.append({"role": "user", "content": message})

	rsp = request_talk(comm.cid, messages, model_name, params)
	if rsp == "fail":
		return JsonResponse({'status': 'error', 'reason': 'Internal Error'}, status=200)
	if rsp == "queue full":
		return JsonResponse({'status': 'error', 'reason': 'queue full'}, status=200)
	elif rsp == "ok":
		comm.status = "QR"
		comm.save()
		return JsonResponse({'status': 'ok', 'cid': comm.cid, "title": comm.title}, status=200)

@require_http_methods(["POST"])
@require_user("data")
def get_streaming_content(request):
	try:
		data = json.loads(request.body)
	except:
		data = {}

	cid = data.get('cid',"")
	if cid == "":
		return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=200)
	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=200)
	if comm.user.pk != request.User.pk:
		return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=200)

	return StreamingHttpResponse(yield_content(cid), content_type='text/event-stream')
	

@require_http_methods(["POST"])
@require_user("data")
def change_communication_title(request):
	data = json.loads(request.body)
	cid = data.get('cid',"")
	newtitle = data.get('newtitle',"")
	if len(newtitle) > 30:
		return JsonResponse({'status': 'fail', 'reason': "length of title exceed 30"}, status=200)

	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=200)
	
	if comm.user.pk == request.User.pk:
		comm.title = newtitle
		comm.save()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=200)

@require_http_methods(["POST"])
@require_user("data")
def delete_communication(request):
	data = json.loads(request.body)
	cid = data.get('cid',"")
	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=200)
	
	if comm.user.pk == request.User.pk:
		comm.delete()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=200)

@require_http_methods(["POST"])
@require_user("data")
def star_communication(request):
	data = json.loads(request.body)
	cid = data.get('cid',"")
	b = data.get('b',False)
	if type(b) != bool:
		return JsonResponse({'status': 'fail', 'reason': "params error: b is not a boolen"}, status=200)
	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=200)

	if comm.user.pk == request.User.pk:
		comm.starred = b
		comm.save()
		return JsonResponse({'status': 'ok',"data":b}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=200)

@require_user("page")
def site_mailbox(request):
	if request.method == "GET":
		return render(request,"mainsite/site_mailbox.html")
	
	elif request.method == "POST":
		try:
			data = json.loads(request.body)
			title = data.get('title')
			content = data.get('content')
			add_mailbox(request.User,title,content)
			return JsonResponse({'status': 'ok'}, status=200)
		except json.JSONDecodeError:
			return JsonResponse({'status': 'fail', 'reason': 'Invalid JSON'}, status=200)	
		except KeyError as e:
			return JsonResponse({'status': 'fail', 'reason': f'Missing key: {str(e)}'}, status=200)

@require_http_methods(["GET"])
@require_user("data")
def get_params(request): # 获取服务器存的对话参数
	cid = request.GET["cid"]
	comm = get_communication_by_cid(cid)
	if comm is None:
		return JsonResponse({'status': 'fail', 'reason': 'no communication'}, status=200)
	if (comm.user.pk != request.User.pk):
		return JsonResponse({'status': 'fail', 'reason': 'no permission'}, status=200)
	ret_data = {}
	ret_data["system"] = comm.system
	ret_data["temperature"] = comm.temperature
	ret_data["top_p"] = comm.top_p
	ret_data["max_tokens"] = comm.max_tokens
	ret_data["frequency_penalty"] = comm.frequency_penalty
	ret_data["presence_penalty"] = comm.presence_penalty
	return JsonResponse({'status': 'ok', 'data': json.dumps(ret_data)},status=200)

@require_http_methods(["GET"])
def ds2pdf(request):
	return render(request,"mainsite/ds2pdf.html")

@require_http_methods(["POST"])
def ds2pdf_report(request):
	data = json.loads(request.body)
	content = data.get('content','')
	description = data.get('description','')
	new_ds2pdf_report(content,description)
	return JsonResponse({'status': 'ok'},status=200)

#only localhost can access
@require_http_methods(["POST"])
@csrf_exempt
def update_communication_to_database(request):
	if not request.META.get('REMOTE_ADDR') in [settings.LOCAL_HOST, 'localhost', '127.0.0.1']:
		logger.warning(f"unauthorized access from {request.META.get('REMOTE_ADDR')}")
		return JsonResponse({'status': 'fail', 'reason': 'no permission'}, status=200)
	
	datas = json.loads(request.body)
	for data in datas:
		cid = data.get("cid","")
		role = data.get("role","")
		if "content" not in data.keys():
			return JsonResponse({'status': 'fail', 'reason': 'no content'}, status=200)
		content = data.get("content")
		model_name = data.get("model_name","")

		if cid == "" or model_name == "":
			return JsonResponse({'status': 'fail', 'reason': 'params error'}, status=200)
		
		comm = get_communication_by_cid(cid)

		if comm is None:
			return JsonResponse({'status': 'fail', 'reason': 'no communication'}, status=200)
		
		if comm.status != "QR":
			logger.warning(f"comm {comm.cid} status is not querying")

		create_communication_content(comm ,role, content, get_model_origin_by_name(model_name))
		if role == "assistant":
			comm.status = "DN"
			comm.save()

	return JsonResponse({'status': 'ok'},status=200)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
	if not request.META.get('REMOTE_ADDR') in [settings.LOCAL_HOST, 'localhost', '127.0.0.1']:
		logger.warning(f"unauthorized access from {request.META.get('REMOTE_ADDR')}")
		return HttpResponse(status=404)
	return JsonResponse({'status': 'ok'},status=200)

@require_http_methods(["POST"])
@require_user("data")
def user_copy_communication(request):
	try:
		data = json.loads(request.body)
	except:
		data = {}
	
	cid = data.get('cid',"")

	# 获取对话
	if cid == "":
		return JsonResponse({'status': 'error', 'reason': 'no cid'}, status=200)
	else:
		comm = get_communication_by_cid(cid)
		if comm is None:
			return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=200)

		if comm.user.pk != request.User.pk:
			return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=200)
		
		if comm.status != "DN":
			return JsonResponse({'status': 'error', 'reason': 'communication not done'}, status=200)
		
		new_comm = copy_communication(comm)
		return JsonResponse({'status': 'ok', "cid": new_comm.cid, "title": new_comm.title, "model": comm.model}, status=200)

@require_http_methods(["POST"])
@require_user("data")
def user_new_communication(request):
	try:
		data = json.loads(request.body)
	except:
		data = {}
	cid = data.get('cid',"")
	messages = data.get("messages",[])
	model_name = data.get('model_name',"")
	if not model_name in get_models():
		return JsonResponse({'status': 'error', 'reason': 'model not supported'}, status=200)	
	
	if not user_try_talk(request.User):
		return JsonResponse({'status': 'error', 'reason': 'talk limit exceeded'}, status=200)
	
	if cid == "":
		return JsonResponse({'status': 'error', 'reason': 'no cid'}, status=200)
	elif messages == []:
		return JsonResponse({'status': 'error', 'reason': 'no messages'}, status=200)
	else:
		comm = get_communication_by_cid(cid)
		if comm is None:
			return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=200)

		if comm.user.pk != request.User.pk:
			return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=200)
		
		if comm.status != "DN":
			return JsonResponse({'status': 'error', 'reason': 'communication not done'}, status=200)
		
		for i in range(len(messages)):
			if set(messages[i].keys()) != {"role", "content", "model"}:
				return JsonResponse({'status': 'error', 'reason': 'params error in messages'}, status=200)
			if not messages[i]["role"] in ["assistant","reasoning","user"]:
				return JsonResponse({'status': 'error', 'reason': 'params error in messages'}, status=200)
		system = data.get('system',"")
		cid = data.get('cid',"")
		try:
			params = _get_params_from_dict(data)
		except Exception as e:
			print(e)
			return JsonResponse({'status': 'error', 'reason': 'params error'}, status=200)
		
		upload_messages = []
		for msg in messages:
			if msg["role"] != "reasoning":
				upload_messages.append({"role": msg["role"],"content": msg["content"]})
		systemed_messages = []
		if system != "":
			systemed_messages.append({"role":"system","content":system})
		systemed_messages.extend(upload_messages)

		newtitle = (comm.title[:22] + "_another")
		new_comm = new_communication(request.User, messages, newtitle, system, params)

		update_comm_params(new_comm,params)
		new_comm.system = system
		
		rsp = request_talk(new_comm.cid, systemed_messages, model_name, params)
		if rsp == "fail":
			return JsonResponse({'status': 'error', 'reason': 'Internal Error'}, status=200)
		if rsp == "queue full":
			return JsonResponse({'status': 'error', 'reason': 'queue full'}, status=200)
		elif rsp == "ok":
			new_comm.status = "QR"
			new_comm.save()
			return JsonResponse({'status': 'ok', 'cid': new_comm.cid, "title": new_comm.title}, status=200)

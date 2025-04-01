from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone

import json
import bcrypt
import random
import string
import datetime
import logging
logger = logging.getLogger(__name__)

from .models_api import *
from .talk_with_AI import talk_with_AI

def redirect2loginResponse():
	response = HttpResponseRedirect(reverse("mainsite:login"))
	response.delete_cookie('sessionid')
	response.delete_cookie('username')
	return response

def NoAuthResponse():
	response = HttpResponse('Unauthorized', status=401)
	response.delete_cookie('sessionid')
	response.delete_cookie('username')
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
					return redirect2loginResponse()
				else:
					return NoAuthResponse()
			result = func(*args, **kwargs)
			return result
		return wrapper

def generate_random_string(length):
	characters = string.ascii_letters + string.digits  # 字母和数字
	return ''.join(random.choices(characters, k=length))

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
		return render(request,"mainsite/login.html")
	elif request.method == "POST":
		username = request.POST.get("username","")
		password = request.POST.get("password","")
		
		user = get_user_by_username(username)
		if user == None:
			return JsonResponse({"status": "fail","reason": "user not exist or incorrect password"}, status=400)

		if bcrypt.checkpw(password.encode(), user.user_password.encode()):
			if user.user_status == "FD":
				return JsonResponse( {"status": "fail","reason": "user forbidden"}, status=400)
			sessionid = generate_random_string(20)
			user.sessionid = sessionid
			user.sessionid_expire = timezone.now() + datetime.timedelta(days=14)

			if user.user_type == "TM" and user.user_status == "NM": # 临时用户，第二次登陆就禁止了
				user.user_status = "FD"
				user.save()
				return JsonResponse( {"status": "fail","reason": "user forbidden"}, status=400)

			if user.user_status == "NL":
				user.user_status = "NM"
			user.save()
			request.session["id"] = sessionid
			rsp = JsonResponse({"status": "success"}, status=200)
			rsp.set_cookie("username",username,max_age=1209600)
			return rsp
		else:
			return JsonResponse({"status": "fail","reason": "user not exist or incorrect password"}, status=400)

@require_http_methods(["GET","POST"])
def register(request):
	if request.method == "GET":
		if get_can_register():
			return render(request,"mainsite/register.html")
		else:
			return HttpResponse("注册暂时不可用，请与管理员联系") #
	elif request.method == "POST":
		if not get_can_register():
			return JsonResponse( {"status": "fail","reason": "register unavailable",}, status=403) #
		
		username = request.POST.get("username","")
		password = request.POST.get("password","")

		if add_user(username,password):
			return JsonResponse({"status": "success",}, status=200)
		else:
			return JsonResponse({"status": "fail","reason": "username exist"}, status=400)

@require_http_methods(["GET","POST"])
@require_user("data")
def change_password(request):
	if request.method == "GET":
		return render(request,"mainsite/change_password.html")
	elif request.method == "POST":
		# return JsonResponse( {"status": "fail","reason": "change_password unavailable",}, status=403)
		user = request.User

		logger.info(f"user {user} change_password")
		ori_password = request.POST.get("ori_password","")
		
		if not bcrypt.checkpw(ori_password.encode(), user.user_password.encode()):
			return JsonResponse({"status": "fail","reason": "ori_password error"}, status=400)

		if not "new_password" in request.POST.keys():
			return JsonResponse({"status": "fail","reason": "no new_password"}, status=400)

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
	return JsonResponse({'status': 'ok', 'data': get_typed_models()},status=200)

@require_http_methods(["GET"])
@require_user("data")
def get_history(request):
	titles = []
	# query = request.User.communication_set.all().order_by('gen_date')
	query = request.User.communication_set.all()
	for comm in query.iterator():
		titles.append({"title":comm.title,"model":comm.model,"date":comm.gen_date,"id":comm.pk})
	return JsonResponse({'status': 'ok', 'titles': titles},status=200)

@require_http_methods(["GET"])
@require_user("data")
def get_communication_content(request):
	cid = request.GET["cid"]
	comm = get_communication_by_pk(int(cid))
	if comm == None:
		return JsonResponse({'status': 'error', 'reason': 'no communication'}, status=400)
	if (comm.user.pk != request.User.pk):
		return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)
	messages = []
	qst = comm.communication_content_set.all().order_by('gen_date')
	for msg in qst:
		messages.append({"role":msg.role,"content":msg.content,"model":msg.get_model_display()})
	return JsonResponse({'status': 'ok', 'messages': messages},status=200)


@require_http_methods(["POST"])
@require_user("data")
def talk(request):
	try:
		data = json.loads(request.body)
	except:
		data = {}
	
	model_name = data.get('model_name',"")
	if not model_name in get_models():
		return JsonResponse({'status': 'error', 'reason': 'model not supported'}, status=400)	
	message = data.get('message',"")
	cid = data.get('cid',-2)

	if cid == -1:
		comm = create_communication(request.User,message[:30],model_name)
	else:
		comm = get_communication_by_pk(cid)
		if comm == None:
			return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=400)

		if (comm.user.pk != request.User.pk):
			return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)

	messages = []
	for msg in comm.communication_content_set.all():
		if msg.role == "reasoning":
			continue
		messages.append({"role":msg.role,"content":msg.content})

	messages.append({"role": "user", "content": message})
	create_communication_content(comm,"user",message,get_model_origin_by_name(model_name))
	return StreamingHttpResponse(talk_with_AI(comm,messages,model_name), content_type="application/json")

@require_http_methods(["POST"])
@require_user("data")
def change_communication_title(request):
	data = json.loads(request.body)
	cid = data.get('cid',-2)
	newtitle = data.get('newtitle',"")
	if len(newtitle) > 30:
		return JsonResponse({'status': 'fail', 'reason': "length of title exceed 30"}, status=400)

	comm = get_communication_by_pk(cid)
	if comm == None:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
	
	if comm.user.pk == request.User.pk:
		comm.title = newtitle
		comm.save()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)

@require_http_methods(["POST"])
@require_user("data")
def delete_communication(request):
	data = json.loads(request.body)
	cid = data.get('cid',-2)
	comm = get_communication_by_pk(cid)
	if comm == None:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
	
	if comm.user.pk == request.User.pk:
		comm.delete()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)

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
			return JsonResponse({'status': 'error', 'reason': 'Invalid JSON'}, status=400)	
		except KeyError as e:
			return JsonResponse({'status': 'error', 'reason': f'Missing key: {str(e)}'}, status=400)
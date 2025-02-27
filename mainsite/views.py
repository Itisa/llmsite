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

from .models import User, Communication, Communication_Content, Mailbox
from .talk_with_AI import talk_with_AI
from .local_settings import available_models

def redirect2loginResponse():
	response = HttpResponseRedirect(reverse("mainsite:login"))
	response.delete_cookie('sessionid')
	response.delete_cookie('username')
	return response

def require_user(views):
	def wrapper_function(*args, **kwargs):
		if (not hasattr(args[0],"User")) or args[0].User == None or args[0].User.sessionid_expire < timezone.now():
			return redirect2loginResponse()
		result = views(*args, **kwargs)
		return result
	return wrapper_function

def generate_random_string(length):
	characters = string.ascii_letters + string.digits  # 字母和数字
	return ''.join(random.choices(characters, k=length))

def add_user(username,password):
	if_have_user = User.objects.filter(username=username)

	if len(if_have_user) != 0:
		return False
	hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
	new_user = User(username=username,user_password=hashed_password.decode(),sessionid_expire=timezone.now())
	new_user.save()
	return True

def delete_user(username):
	if_have_user = User.objects.filter(username=username)

	if len(if_have_user) == 0:
		return False
	if_have_user[0].delete()
	return True

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

@require_http_methods(["GET"])
@require_user
def site(request):
	print("On request site")
	rsp = render(request,"mainsite/mainsite.html")
	return rsp

@require_http_methods(["GET","POST"])
def login(request):
	print("On request login")
	if request.method == "GET":
		if request.User:
			return HttpResponseRedirect(reverse("mainsite:site"))
		return render(request,"mainsite/login.html")
	elif request.method == "POST":
		ret_dict = {}
		ret_dict['result'] = 0

		username = request.POST.get("username","")
		password = request.POST.get("password","")
		
		user = get_user_by_username(username)
		if not user:
			return JsonResponse( {"status": "fail","reason": "user not exist",}, status=400)

		if bcrypt.checkpw(password.encode(), user.user_password.encode()):
			sessionid = generate_random_string(20)
			user.sessionid = sessionid
			user.sessionid_expire = timezone.now() + datetime.timedelta(days=14)
			user.save()
			request.session["id"] = sessionid
			rsp = JsonResponse({"status": "success"}, status=200)
			rsp.set_cookie("username",username,max_age=1209600)
			print(123456)
			return rsp
		else:
			response_data = {
				"status": "fail",
				"reason": "incorrect password",
			}
			return JsonResponse(response_data, status=403)

@require_http_methods(["GET","POST"])
def register(request):
	if request.method == "GET":
		return render(request,"mainsite/register.html")
	elif request.method == "POST":
		
		return JsonResponse( {"status": "fail","reason": "register unavailable",}, status=403)
		username = request.POST.get("username","")
		password = request.POST.get("password","")

		if add_user(username,password):
			return JsonResponse({"status": "success",}, status=200)
		else:
			return JsonResponse({"status": "fail","reason": "username exist"}, status=403)

@require_http_methods(["GET","POST"])
@require_user
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
		new_password = request.POST.get("new_password","")
		
		user.user_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
		user.save()
		return JsonResponse({"status": "success"}, status=200)

@require_http_methods(["GET"])
@require_user
def logout(request):
	rsp = HttpResponseRedirect(reverse("mainsite:login"))
	rsp.delete_cookie("sessionid")
	rsp.delete_cookie("username")
	return rsp

@require_http_methods(["GET"])
@require_user
def get_available_models(request):
	return JsonResponse({'status': 'ok', 'data': available_models},status=200)

@require_http_methods(["GET"])
@require_user
def get_history(request):
	titles = []
	for comm in request.User.communication_set.all():
		titles.append({"title":comm.title,"model":comm.model,"date":comm.gen_date,"id":comm.pk})
	return JsonResponse({'status': 'ok', 'titles': titles},status=200)

@require_http_methods(["GET"])
@require_user
def get_communication_content(request):
	cid = request.GET["cid"]
	comm = Communication.objects.get(pk=int(cid))
	if not comm:
		return JsonResponse({'status': 'error', 'reason': 'no communication'}, status=400)
	if (comm.user.pk != request.User.pk):
		return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)
	messages = []
	for msg in comm.communication_content_set.all():
		messages.append({"role":msg.role,"content":msg.content,"timestamp":msg.gen_date,"id":msg.pk})
	return JsonResponse({'status': 'ok', 'messages': messages},status=200)


@require_http_methods(["POST"])
@require_user
def talk(request):

	print("On talk post")
	try:
		data = json.loads(request.body)
	except:
		data = {}
	
	model_name = data.get('model_name',"")
	if not model_name in available_models:
		return JsonResponse({'status': 'error', 'reason': 'model not supported'}, status=400)	
	message = data.get('message',"")
	cid = data.get('cid',-2)

	if cid == -1:
		comm = request.User.communication_set.create(gen_date=timezone.now(),model=model_name)
		comm.title = message[:30]
	else:
		comm = Communication.objects.get(pk=int(cid))
		if not comm:
			return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=400)

		if (comm.user.pk != request.User.pk):
			return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)

	messages = []
	for msg in comm.communication_content_set.all():
		if msg.role == "reasoning":
			continue
		messages.append({"role":msg.role,"content":msg.content})

	messages.append({"role": "user", "content": message})
	# print(messages)
	comm.communication_content_set.create(gen_date=timezone.now(),role="user",content=message)
	return StreamingHttpResponse(talk_with_AI(comm,messages,model_name), content_type="application/json")

@require_http_methods(["POST"])
@require_user
def change_communication_title(request):
	data = json.loads(request.body)
	cid = data.get('cid')
	newtitle = data.get('newtitle')
	if len(newtitle) > 30:
		return JsonResponse({'status': 'fail', 'reason': "length of title exceed 30"}, status=400)

	comm = Communication.objects.get(pk=cid)
	if not comm:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
	
	if comm.user.pk == request.User.pk:
		comm.title = newtitle
		comm.save()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)

@require_http_methods(["POST"])
@require_user
def delete_communication(request):
	data = json.loads(request.body)
	cid = data.get('cid')
	comm = Communication.objects.get(pk=cid)
	if not comm:
		return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
	
	if comm.user.pk == request.User.pk:
		comm.delete()
		return JsonResponse({'status': 'ok'}, status=200)
	else:
		return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)

@require_user
def site_mailbox(request):
	if request.method == "GET":
		return render(request,"mainsite/site_mailbox.html")
	
	elif request.method == "POST":
		try:
			data = json.loads(request.body)
			title = data.get('title')
			content = data.get('content')
			mm = Mailbox(user=request.User,title=title,content=content,gen_date=timezone.now())
			mm.save()
			return JsonResponse({'status': 'ok'}, status=200)
		except json.JSONDecodeError:
			return JsonResponse({'status': 'error', 'reason': 'Invalid JSON'}, status=400)	
		except KeyError as e:
			return JsonResponse({'status': 'error', 'reason': f'Missing key: {str(e)}'}, status=400)
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone

import json
import bcrypt
import random
import string
import datetime

from .models import User, Communication, Communication_Content
from .talk_with_AI import talk_with_AI

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
	return User.objects.filter(sessionid=sessionid)[0]

def get_user_by_username(username):
	return User.objects.filter(username=username)[0]

def check_user_status(user):
	if user.sessionid_expire >= timezone.now():
		return True
	else:
		return False

def site(request):
	print("On request site")
	rsp = render(request,"mainsite/mainsite.html")
	return rsp
	
def login(request):
	print("On request login")
	try:
		username = request.POST["username"]
		password = request.POST["password"]
		print("username:",username)
		print("password:",password)

		user = get_user_by_username(username)

		if bcrypt.checkpw(password.encode(), user.user_password.encode()):
			sessionid = generate_random_string(20)
			user.sessionid = sessionid;
			user.sessionid_expire = timezone.now() + datetime.timedelta(days=14)
			user.save()
			request.session["id"] = sessionid;
			response_data = {
				"status": "success",
			}
			rsp = JsonResponse(response_data, status=200)
			rsp.set_cookie("username",username,max_age=1209600)
			return rsp
		else:
			response_data = {
				"status": "fail",
				"reason": "incorrect password",
			}
			return JsonResponse(response_data, status=403)

	except Exception as e:
		print("ERROR\n",e)
		response_data = {
			'status': 'error',
		}
		return JsonResponse(response_data, status=500)

def register(request):
	if request.method == "GET":
		return render(request,"mainsite/register.html")
	elif request.method == "POST":
		
		response_data = {
			"status": "fail",
			"reason": "register unavailable",
		}
		return JsonResponse(response_data, status=403)
		### register unavailable
		username = request.POST["username"]
		password = request.POST["password"]
		
		if add_user(username,password):
			response_data = {
				"status": "success",
				"sessionid": "xoihfiseorjgdio",
			}
			return JsonResponse(response_data, status=200)

		else:
			response_data = {
				"status": "fail",
				"reason": "username exist",
			}
			return JsonResponse(response_data, status=403)

		
def logout(request):
	rsp = HttpResponseRedirect(reverse("mainsite:site"))
	rsp.delete_cookie("sessionid")
	rsp.delete_cookie("username")
	return rsp

def talk(request):
	try:
		user = get_user_by_sessionid(request.session["id"])
		if not check_user_status(user):
			rsp = JsonResponse({'status': 'error', 'message': 'sessionid expires'}, status=400)
			rsp.delete_cookie("sessionid")
			rsp.delete_cookie("username")
			return rsp;
	except Exception as e:
		print(e)
		print("ERROR in talk user")
		# return logout(request)
		return JsonResponse({'status': 'error', 'message': 'no sessionid'}, status=400)

	if request.method == "GET":
		print("On talk get")

		for key, value in request.GET.items():
			if key == "communication_id":
				communication_id = int(value)

		if communication_id == -1:
			titles = []
			for comm in user.communication_set.all():
				titles.append({"title":comm.title,"model":comm.model,"date":comm.gen_date,"id":comm.pk})
			return JsonResponse({'status': 'ok', 'titles': titles},status=200)
		else:
			comm = Communication.objects.filter(pk=int(communication_id))[0]
			if (comm.user.pk != user.pk):
				return JsonResponse({'status': 'error', 'message': 'no permission'}, status=403)
			messages = []
			for msg in comm.communication_content_set.all():
				messages.append({"role":msg.role,"content":msg.content,"timestamp":msg.gen_date,"id":msg.pk})
			return JsonResponse({'status': 'ok', 'messages': messages},status=200)

	elif request.method == "POST":
		print("On talk post")
		try:
			data = json.loads(request.body)
			model_name = data.get('model_name')
			message = data.get('message')
			communication_id = data.get('communication_id')
			if communication_id == -1:
				comm = user.communication_set.create(gen_date=timezone.now(),model=model_name)
			else:
				comm = Communication.objects.filter(pk=int(communication_id))[0]
				if (comm.user.sessionid != request.session["id"]):
					return JsonResponse({'status': 'error', 'message': 'no permission'}, status=403)

			messages = [{"role": "user", "content": message}]
			comm.communication_content_set.create(gen_date=timezone.now(),role="user",content=message)
			rsp = talk_with_AI(model_name,messages)
			comm.communication_content_set.create(gen_date=timezone.now(),role="assistant",content=rsp)
			response_data = {
				'status': 'ok',
				'message': rsp,
				'communication_id': comm.pk,
			}
			return JsonResponse(response_data)
		
		except json.JSONDecodeError:
			# 处理JSON解析错误
			return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
		
		except KeyError as e:
			# 处理缺少必要字段的情况
			return JsonResponse({'status': 'error', 'message': f'Missing key: {str(e)}'}, status=400)
		
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': f'other: {str(e)}'}, status=400)

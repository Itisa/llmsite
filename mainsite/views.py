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

from .models import User, Communication, Communication_Content
from .talk_with_AI import talk_with_AI
from .secret_settings import available_models
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
	except:
		JsonResponse({"status": "fail","reason": "no username",}, status=400)
	try:
		password = request.POST["password"]
	except:
		JsonResponse({"status": "fail","reason": "no password",}, status=400)
	
	try:
		user = get_user_by_username(username)
	except:
		JsonResponse({"status": "fail","reason": "username not exist",}, status=400)
	try:
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
		
		return JsonResponse( {"status": "fail","reason": "register unavailable",}, status=403)
		try:		
			username = request.POST["username"]
		except:
			return JsonResponse({"status": "fail","reason": "no username"}, status=400)
		try:
			password = request.POST["password"]
		except:
			return JsonResponse({"status": "fail","reason": "no password"}, status=400)

		try:
			if add_user(username,password):
				return JsonResponse({"status": "success",}, status=200)
			else:
				return JsonResponse({"status": "fail","reason": "username exist"}, status=403)
		except Exception as e:
			print("Error occured in register")
			print(e)
			return JsonResponse({"status": "fail","reason": "error"}, status=500)
		
def logout(request):
	rsp = HttpResponseRedirect(reverse("mainsite:site"))
	rsp.delete_cookie("sessionid")
	rsp.delete_cookie("username")
	return rsp

def JSON_sessionid_expire_ret():
	rsp = JsonResponse({'status': 'error', 'reason': 'sessionid expires'}, status=400)
	rsp.delete_cookie("sessionid")
	rsp.delete_cookie("username")
	return rsp

def talk(request):
	try:
		user = get_user_by_sessionid(request.session["id"])
		if not check_user_status(user):
			return JSON_sessionid_expire_ret();
	except Exception as e:
		print(e)
		print("ERROR in user_get in talk user")
		return JSON_sessionid_expire_ret();

	if request.method == "GET":
		print("On talk get")
		try:
			cid = int(request.GET["cid"])
		except:
			return JsonResponse({'status': 'error', 'reason': "invalid cid"},status=400)
		
		if cid == -1:
			titles = []
			for comm in user.communication_set.all():
				titles.append({"title":comm.title,"model":comm.model,"date":comm.gen_date,"id":comm.pk})
			return JsonResponse({'status': 'ok', 'titles': titles},status=200)

		else:
			comm = Communication.objects.filter(pk=int(cid))
			if len(comm) == 0:
				return JsonResponse({'status': 'error', 'reason': 'no communication'}, status=400)
			comm = comm[0]
			if (comm.user.pk != user.pk):
				return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)
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
			cid = data.get('cid')
		except json.JSONDecodeError:
			# 处理JSON解析错误
			return JsonResponse({'status': 'error', 'reason': 'Invalid JSON'}, status=400)	
		except KeyError as e:
			# 处理缺少必要字段的情况
			return JsonResponse({'status': 'error', 'reason': f'Missing key: {str(e)}'}, status=400)

		try:
			if cid == -1:
				comm = user.communication_set.create(gen_date=timezone.now(),model=model_name)
				comm.title = str(comm.pk)
			else:
				comm = Communication.objects.filter(pk=int(cid))
				if len(comm) == 0:
					return JsonResponse({'status': 'error', 'reason': 'cid not exist'}, status=400)
				comm = comm[0]

				if (comm.user.sessionid != request.session["id"]):
					return JsonResponse({'status': 'error', 'reason': 'no permission'}, status=403)
				model_name = comm.model

			messages = []
			for msg in comm.communication_content_set.all():
				messages.append({"role":msg.role,"content":msg.content})
			messages.append({"role": "user", "content": message})
			# print(messages)
			comm.communication_content_set.create(gen_date=timezone.now(),role="user",content=message)
			return StreamingHttpResponse(talk_with_AI(comm,messages), content_type="application/json")
			
			# rsp = talk_with_AI(messages)
			# comm.communication_content_set.create(gen_date=timezone.now(),role="assistant",content=rsp)
			# response_data = {
			# 	'status': 'ok',
			# 	'message': rsp,
			# 	'cid': comm.pk,
			# 	'title': comm.title,
			# 	'model': comm.model,
			# }
			# comm.save()
			# return JsonResponse(response_data)

		except Exception as e:
			return JsonResponse({'status': 'error', 'reason': f'other: {str(e)}'}, status=400)

@require_http_methods(["GET","POST"])  # 限制只接受GET,POST请求
def other_functions(request):
	print("On other_functions post")
	try:
		user = get_user_by_sessionid(request.session["id"])
		if not check_user_status(user):
			return JSON_sessionid_expire_ret();
	except Exception as e:
		print(e)
		print("ERROR in user_get in other_functions")
		return JSON_sessionid_expire_ret();

	if request.method == "GET":
		try:
			cmd = request.GET["cmd"]
		except:
			return JsonResponse({'status': 'fail', 'reason': "no command"}, status=400)
		
		if cmd == "load models":
			return JsonResponse({'status': 'ok', 'data': available_models}, status=200)
		else:
			return JsonResponse({'status': 'fail', 'reason': "command not found"}, status=400)
	
	elif request.method == "POST":
		try:
			data = json.loads(request.body)
			cmd = data.get('cmd')
			print("cmd:",cmd)
			if cmd == "change communication title":
				cid = data.get('cid')
				newtitle = data.get('newtitle')
				comm = Communication.objects.filter(pk=cid)
				if len(comm) == 0:
					return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
				
				if comm[0].user.pk == user.pk:
					comm[0].title = newtitle
					comm[0].save()
					return JsonResponse({'status': 'ok'}, status=200)
				else:
					return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)
			elif cmd == "delete communication":
				cid = data.get('cid')
				comm = Communication.objects.filter(pk=cid)
				if len(comm) == 0:
					return JsonResponse({'status': 'fail', 'reason': "communication not found"}, status=400)
				
				if comm[0].user.pk == user.pk:
					comm[0].delete();
					return JsonResponse({'status': 'ok'}, status=200)
				else:
					return JsonResponse({'status': 'fail', 'reason': "no permission"}, status=400)
			elif cmd == "":
				pass
				return JsonResponse({'status': 'fail', 'reason': "cmd not found"}, status=400)
			else:
				return JsonResponse({'status': 'fail', 'reason': "cmd not found"}, status=400)
		except json.JSONDecodeError:
			return JsonResponse({'status': 'error', 'reason': 'Invalid JSON'}, status=400)	
		except KeyError as e:
			return JsonResponse({'status': 'error', 'reason': f'Missing key: {str(e)}'}, status=400)

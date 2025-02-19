from django.contrib import admin
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
# Register your models here.

from .models import User, Communication, Communication_Content
from .views import generate_random_string,add_user

import bcrypt
def new_user(username, password, param3):
	# 在这里执行你的自定义逻辑
	print("new_user:",username,password,param3)
	if password == "":
		password = generate_random_string(10)
	if add_user(username,password):
		result = f"successfully new user 用户名={username}, 密码={password}, param3={param3}"
	else:
		result = f"fail new user 用户名={username}, 密码={password}, param3={param3}"
	return result
class MyCustomForm(forms.Form):
	username = forms.CharField(label="用户名", required=True)
	password = forms.CharField(label="密码", required=False)
	param3 = forms.ChoiceField(
		label="这个现在没用",
		choices=[
			('option1', 'Option 1'),
			('option2', 'Option 2'),
			('option3', 'Option 3'),
		],
		required=True,
	)
	# param3 = forms.IntegerField(label="maxCommunications", initial=20, required=True)

def reset_pwd2username(modeladmin, request, queryset):
	for user in queryset:
		# 在这里执行你的自定义逻辑
		user.user_password = bcrypt.hashpw(user.username.encode(), bcrypt.gensalt()).decode()
		user.save()
	modeladmin.message_user(request, "重置密码成功")

reset_pwd2username.short_description = "重置密码为用户名"

class UserAdmin(admin.ModelAdmin):
	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('new_user/', self.admin_site.admin_view(self.custom_action_view), name='new_user'),
		]
		return custom_urls + urls

	def custom_action_view(self, request):
		if request.method == 'POST':
			form = MyCustomForm(request.POST)
			if form.is_valid():
				username = form.cleaned_data['username']
				password = form.cleaned_data['password']
				param3 = form.cleaned_data['param3']
				result = new_user(username, password, param3)
				self.message_user(request, result)
				return HttpResponseRedirect(request.path)
		else:
			form = MyCustomForm()

		return render(request, 'admin/new_user.html', {
			'form': form,
			'opts': self.model._meta,
		})
	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['new_user_url'] = 'new_user/'
		return super().changelist_view(request, extra_context=extra_context)
	list_display = ["username"]
	list_per_page = 50
	actions = [reset_pwd2username]  # 注册自定义操作

admin.site.register(User,UserAdmin)

class CommunicationAdmin(admin.ModelAdmin):
	list_display = ["title","user", "gen_date", "model"]
	list_per_page = 50
admin.site.register(Communication,CommunicationAdmin)

class Communication_ContentAdmin(admin.ModelAdmin):
	list_display = ["communication","__str__","get_communication_user"]
	list_per_page = 50
	def get_communication_user(self, obj):
		return obj.communication.user
	get_communication_user.short_description = 'User'

admin.site.register(Communication_Content,Communication_ContentAdmin)

from django.contrib import admin
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.contrib import messages

from .models import User, Communication, Communication_Content, Mailbox, Api_config, GlobalSetting, Ds2pdf_report
from .views import _generate_random_string
from .models_api import get_user_by_username, add_user

import bcrypt

def copy_api_config(modeladmin, request, queryset):
	newaa = []
	for model in queryset:
		new_name = model.name + "_copy"
		name_qst = Api_config.objects.filter(name=new_name)
		if len(name_qst) == 0:
			aa = Api_config(
				name=new_name,
				api_key=model.api_key,
				model=model.model,
				base_url=model.base_url,
				model_type=model.model_type,
				model_origin=model.model_origin
			)
			newaa.append(aa)
		else:
			modeladmin.message_user(request, f"复制失败，已经存在{new_name}，请修改后再复制")
			return 
	for model in newaa:
		model.save();
	modeladmin.message_user(request, "复制成功")
copy_api_config.short_description = "复制api配置"

class Api_configAdmin(admin.ModelAdmin):
	list_display = ["name","disabled"]
	actions = [copy_api_config]
admin.site.register(Api_config,Api_configAdmin)

def new_user(username, password, user_type):
	if password == "":
		password = _generate_random_string(10)
	if add_user(username,password,user_type):
		result = (messages.SUCCESS,f"successfully new user 用户名={username}, 密码={password}, 用户类型={user_type}")
	else:
		result = (messages.ERROR,f"用户名已存在 用户名={username}")
	return result

class AddUserForm(forms.Form):
	username = forms.CharField(label="用户名", required=True)
	password = forms.CharField(label="密码", required=False)
	user_type = forms.ChoiceField(
		label="用户类型",
		choices=[
			('NM', 'normal'),
			('AD', 'admin'),
			('TM', 'temporary'),
		],
		required=True,
	)

	# param3 = forms.IntegerField(label="maxCommunications", initial=20, required=True)
class ChangeUserPwdForm(forms.Form):
	username = forms.CharField(label="用户名", required=True)
	password = forms.CharField(label="密码", required=False)

def reset_pwd2username(modeladmin, request, queryset):
	for user in queryset:
		user.user_password = bcrypt.hashpw(user.username.encode(), bcrypt.gensalt()).decode()
		user.save()
	modeladmin.message_user(request, "重置密码成功")
reset_pwd2username.short_description = "重置密码为用户名"

def change_password(username, password):
	if password == "":
		password = _generate_random_string(10)
	user = get_user_by_username(username)
	if user is None:
		return (messages.ERROR, f"用户不存在 用户名={username}, 密码={password}")

	user.user_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
	user.save()
	return (messages.SUCCESS, f"成功修改密码 用户名={username}, 密码={password}")

class UserAdmin(admin.ModelAdmin):
	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('new_user/', self.admin_site.admin_view(self.add_user_view), name='new_user'),
			path('change_user_pwd/', self.admin_site.admin_view(self.change_user_pwd_view), name='change_user_pwd'),
		]
		return custom_urls + urls

	def add_user_view(self, request):
		if request.method == 'POST':
			form = AddUserForm(request.POST)
			if form.is_valid():
				username = form.cleaned_data['username']
				password = form.cleaned_data['password']
				user_type = form.cleaned_data['user_type']
				status, result = new_user(username, password, user_type)
				self.message_user(request, result, status)
				return HttpResponseRedirect(request.path)
		else:
			form = AddUserForm()

		return render(request, 'admin/new_user.html', {
			'form': form,
			'opts': self.model._meta,
		})

	def change_user_pwd_view(self, request):
		if request.method == 'POST':
			form = ChangeUserPwdForm(request.POST)
			if form.is_valid():
				username = form.cleaned_data['username']
				password = form.cleaned_data['password']
				status, result = change_password(username, password)
				self.message_user(request, result, status)
				return HttpResponseRedirect(request.path)
		else:
			form = ChangeUserPwdForm()

		return render(request, 'admin/change_user_pwd.html', {
			'form': form,
			'opts': self.model._meta,
		})

	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['new_user_url'] = 'new_user/'
		extra_context['change_user_pwd_url'] = 'change_user_pwd/'
		return super().changelist_view(request, extra_context=extra_context)
	change_list_template = "admin/user_change_list.html"

	def has_add_permission(self,request): # 禁止默认的添加操作
		return False

	list_display = ["username","user_type","user_status","user_level", "user_talk_cnt_left"]
	list_filter = ["user_type","user_status"]
	list_per_page = 50
	actions = [reset_pwd2username]  # 注册自定义操作
admin.site.register(User,UserAdmin)

class CommunicationAdmin(admin.ModelAdmin):
	list_display = ["title","user", "gen_date", "model"]
	list_filter = ["user"]

	list_per_page = 50
admin.site.register(Communication,CommunicationAdmin)

class Communication_ContentAdmin(admin.ModelAdmin):
	list_display = ["communication","__str__","get_communication_user"]
	list_per_page = 50
	
	def get_form(self, request, obj=None, **kwargs):
		# 获取默认的表单类
		form = super().get_form(request, obj, **kwargs)
		# 为特定字段设置 Textarea 小部件
		form.base_fields['content'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 40})
		return form

	def get_communication_user(self, obj):
		return obj.communication.user
	get_communication_user.short_description = 'User'
admin.site.register(Communication_Content,Communication_ContentAdmin)

class MailboxAdmin(admin.ModelAdmin):
	list_display = ["user","title","get_mailbox_content20","gen_date"]
	list_per_page = 50
	def get_mailbox_content20(self, obj):
		return obj.content[:20]
	get_mailbox_content20.short_description = 'content'
	
	def get_form(self, request, obj=None, **kwargs):
		form = super().get_form(request, obj, **kwargs)
		form.base_fields['content'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 40})
		return form
admin.site.register(Mailbox,MailboxAdmin)

class GlobalSettingAdmin(admin.ModelAdmin):
	list_display = ["website_name","enable_register","user_talk_limit"]
admin.site.register(GlobalSetting,GlobalSettingAdmin)

class Ds2pdf_reportAdmin(admin.ModelAdmin):
	list_display = ["__str__","fixed"]
admin.site.register(Ds2pdf_report,Ds2pdf_reportAdmin)
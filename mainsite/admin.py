from django.contrib import admin
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
# Register your models here.

from .models import User, Communication, Communication_Content
from .views import generate_random_string
def new_user(username, password, param3):
	# 在这里执行你的自定义逻辑
	print("new_user:",username,password,param3)
	if password == "":
		password = generate_random_string(10)
	result = f"successfully new user 用户名={username}, 密码={password}, param3={param3}"
	return result
class MyCustomForm(forms.Form):
	username = forms.CharField(label="用户名", required=True)
	password = forms.CharField(label="密码", required=False)
	param3 = forms.ChoiceField(
		label="Parameter 3",
		choices=[
			('option1', 'Option 1'),
			('option2', 'Option 2'),
			('option3', 'Option 3'),
		],
		required=True,
	)
	# param3 = forms.IntegerField(label="maxCommunications", initial=20, required=True)

def function1(modeladmin, request, queryset):
	print(modeladmin)
	print()
	print(request)
	print()
	print(queryset)
	# for obj in queryset:
	#     # 在这里执行你的自定义逻辑
	#     obj.some_field = "Updated Value"
	#     obj.save()
	modeladmin.message_user(request, "Custom function executed successfully.")

function1.short_description = "Execute custom function"

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
	actions = [function1]  # 注册自定义操作

admin.site.register(User,UserAdmin)

class CommunicationAdmin(admin.ModelAdmin):
	list_display = ["title","user", "gen_date", "model"]
admin.site.register(Communication,CommunicationAdmin)

class Communication_ContentAdmin(admin.ModelAdmin):
	pass
admin.site.register(Communication_Content,Communication_ContentAdmin)
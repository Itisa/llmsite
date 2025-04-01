from django.db import models
from django.core.cache import cache
# Create your models here.
from django.utils import timezone


class User(models.Model):
	USER_TYPE_CHOICES = [
		("AD","admin"),
		("NM","normal"),
		("TM","temporary"),
	]
	USER_STATUS_CHOICES = [
		("NM","normal"),
		("FD","forbidden"),
		("NL","nologin"),
	]
	# userid = models.IntegerField(default=-1)
	username = models.CharField(max_length=20,unique=True)
	user_password = models.CharField(max_length=60)
	sessionid = models.CharField(max_length=20,blank=True)
	sessionid_expire = models.DateTimeField("sessionid expire", auto_now_add=True)
	user_level = models.IntegerField(default=-1)
	user_type = models.CharField(max_length=3, choices=USER_TYPE_CHOICES, default="NM")
	user_status = models.CharField(max_length=3, choices=USER_STATUS_CHOICES, default="NL")
	def __str__(self):
		return self.username

class Communication(models.Model):
	MODEL_ORIGIN_CHOICES = [
		("DS","deepseek"),
		("DB","doubao"),
		("OA","openai"),
	]
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now=True)
	model = models.CharField(max_length=100,default='none') #用户最后使用的model
	title = models.CharField(max_length=100)
	def __str__(self):
		return self.title

class Communication_Content(models.Model):
	MODEL_CHOICES = [
		("DS","deepseek"),
		("DB","doubao"),
		("OA","openai"),
		("NN","none"),
	]
	communication = models.ForeignKey(Communication, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now_add=True)
	role = models.CharField(max_length=10)
	content = models.CharField(max_length=4000)
	model = models.CharField(max_length=3, choices=MODEL_CHOICES,default="NN")
	def __str__(self):
		return self.content[:20]

class Mailbox(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now_add=True)
	title = models.CharField(max_length=200,blank=True)
	content = models.CharField(max_length=4000)
	def __str__(self):
		return self.title

class Api_config(models.Model):
	MODEL_TYPE_CHOICES = [
		("RS","reasoning"),
		("CH","chat"),
		("PC","pic2chat"),
	]
	MODEL_ORIGIN_CHOICES = [
		("DS","deepseek"),
		("DB","doubao"),
		("OA","openai"),
	]
	name = models.CharField(max_length=40,unique=True)
	base_url = models.CharField(max_length=100,blank=True)
	api_key = models.CharField(max_length=100)
	model = models.CharField(max_length=100)
	level = models.IntegerField(default=-1)
	model_type = models.CharField(max_length=3, choices=MODEL_TYPE_CHOICES)
	model_origin = models.CharField(max_length=3, choices=MODEL_ORIGIN_CHOICES)
	disabled = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class GlobalSetting(models.Model):
	key = models.CharField(max_length=50,unique=True)
	value = models.CharField(max_length=100)
	comment = models.CharField(max_length=100)
	def __str__(self):
		return self.key

	def save(self, **kwargs):
		super().save(**kwargs)
		cache.set(self.key, self.value, None)
from django.db import models

# Create your models here.
import datetime
from django.utils import timezone

class User(models.Model):
	# userid = models.IntegerField(default=-1)
	username = models.CharField(max_length=20)
	user_password = models.CharField(max_length=60)
	sessionid = models.CharField(max_length=20)
	sessionid_expire = models.DateTimeField("sessionid expire", auto_now_add=True)
	user_level = models.IntegerField(default=-1)
	def __str__(self):
		return self.username

class Communication(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now=True)
	model = models.CharField(max_length=20)
	title = models.CharField(max_length=100)
	def __str__(self):
		return self.title

class Communication_Content(models.Model):
	communication = models.ForeignKey(Communication, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now_add=True)
	role = models.CharField(max_length=10)
	content = models.CharField(max_length=4000)
	def __str__(self):
		return self.content[:20]

class Mailbox(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published", auto_now_add=True)
	title = models.CharField(max_length=200)
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
	name = models.CharField(max_length=40)
	base_url = models.CharField(max_length=100)
	api_key = models.CharField(max_length=100)
	endpoint = models.CharField(max_length=100)
	level = models.IntegerField(default=-1)
	model_type = models.CharField(max_length=3, choices=MODEL_TYPE_CHOICES)
	model_origin = models.CharField(max_length=3, choices=MODEL_TYPE_CHOICES)
	def __str__(self):
		return self.name
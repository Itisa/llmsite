from django.db import models

# Create your models here.
import datetime
from django.utils import timezone

class User(models.Model):
	# userid = models.IntegerField(default=-1)
	username = models.CharField(max_length=20)
	user_password = models.CharField(max_length=60)
	sessionid = models.CharField(max_length=20)
	sessionid_expire = models.DateTimeField("sessionid expire")
	def __str__(self):
		return self.username

class Communication(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published")
	model = models.CharField(max_length=20)
	title = models.CharField(max_length=100)
	def __str__(self):
		return self.title

class Communication_Content(models.Model):
	communication = models.ForeignKey(Communication, on_delete=models.CASCADE)
	gen_date = models.DateTimeField("date published")
	role = models.CharField(max_length=10)
	content = models.CharField(max_length=4000)
	def __str__(self):
		return self.communication.title

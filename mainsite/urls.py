from django.urls import path

from . import views

app_name = "mainsite"
urlpatterns = [
	path("", views.site, name="site"),
	path("register", views.register, name="register"),
	path("login", views.login, name="login"),
	path("logout", views.logout, name="logout"),
	path("talk", views.talk, name="talk"),
	path("other_functions", views.other_functions, name="other_functions"),
]
from django.urls import path

from . import views

app_name = "mainsite"
urlpatterns = [
	path("", views.site, name="site"),
	path("register", views.register, name="register"),
	path("login", views.login, name="login"),
	path("logout", views.logout, name="logout"),
	path("talk", views.talk, name="talk"),
	path("change_password", views.change_password, name="change_password"),
	path("other_functions", views.other_functions, name="other_functions"),
	path("site_mailbox", views.site_mailbox, name="site_mailbox"),
]
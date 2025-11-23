from django.urls import path

from . import views

app_name = "mainsite"
urlpatterns = [
	path("", views.site, name="site"),
	path("c/<str:cid>/", views.site, name="site&cid"),
	path("register", views.register, name="register"),
	path("login", views.login, name="login"),
	path("logout", views.logout, name="logout"),
	path("change_password", views.change_password, name="change_password"),
	path("get_available_models", views.get_available_models, name="get_available_models"),
	path("get_history", views.get_history, name="get_history"),
	path("get_communication_content", views.get_communication_content, name="get_communication_content"),
	path("post_message", views.post_message, name="post_message"),
	path("get_streaming_content", views.get_streaming_content, name="get_streaming_content"),
	path("change_communication_title", views.change_communication_title, name="change_communication_title"),
	path("delete_communication", views.delete_communication, name="delete_communication"),
	path("star_communication", views.star_communication, name="star_communication"),
	path("site_mailbox", views.site_mailbox, name="site_mailbox"),
	path("get_params", views.get_params, name="get_params"),
	path("ds2pdf", views.ds2pdf, name="ds2pdf"),
	path("ds2pdf_report", views.ds2pdf_report, name="ds2pdf_report"),
	path("update_communication_to_database", views.update_communication_to_database, name="update_communication_to_database"),
	path("user_copy_communication", views.user_copy_communication, name="user_copy_communication"),
	path("user_new_communication", views.user_new_communication, name="user_new_communication"),
]
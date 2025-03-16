from mainsite.models import User
from django.utils import timezone
class UserAuthMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# 在视图处理请求之前执行的代码
		# print("Before view")
		sessionid = request.session.get("id")
		u = None
		if sessionid:
			try:
				u = User.objects.get(sessionid=sessionid)
				request.User_expire = (u.sessionid_expire < timezone.now())
			except User.DoesNotExist:
				pass
		request.User = u

		response = self.get_response(request)
		
		# 在视图处理请求之后执行的代码
		# print("After view")
		
		return response
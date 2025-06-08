import socket
import json
import time

def process_data(data):
	# 这里可以对字典进行一些处理，示例：将所有的值转为大写
	return {k: v.upper() for k, v in data.items()}

def start_server():
	# 创建并绑定服务器 socket
	port = 65315
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind(('localhost', port))  # 绑定到与 Django 通信的端口
	server_socket.listen()

	print(f"Server is listening on port {port}...")

	while True:
		# 接受来自客户端的连接
		conn, addr = server_socket.accept()
		with conn:
			print(f"Connected by {addr}")
			
			data = conn.recv(1024)
			print(data)
			if data:
				received_dict = json.loads(data.decode('utf-8'))
				print("Received data:", received_dict)
				for i in range(4):
					rsp = f"Message {i} **你好\n你好{received_dict["data"]}**\n\n"
					conn.sendall(rsp.encode('utf-8'))
					time.sleep(0.5)

			conn.close()
				
if __name__ == '__main__':
	start_server()

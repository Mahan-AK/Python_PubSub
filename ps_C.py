import socket

 
# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
# client.connect((target, port))
client.connect(('127.0.0.1', 1233))
name = input()	
client.send(str.encode(name))
password = input()
client.send(str.encode(password))

# Receive response 
response = client.recv(2048)
response = response.decode()

print(response)
client.close()
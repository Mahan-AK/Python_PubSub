import socket
import hashlib
from optparse import OptionParser


SERVER = "127.0.0.1"
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((SERVER, PORT))

print('Waiting for a Connection..')
server.listen(5)
HashTable = {}

connection, _ = server.accept()

name = connection.recv(2048)
password = connection.recv(2048)
password = password.decode()
name = name.decode()
password=hashlib.sha256(str.encode(password)).hexdigest() # Password hash using SHA256
# REGISTERATION PHASE   
# If new user,  regiter in Hashtable Dictionary  
if name not in HashTable:
    HashTable[name]=password
    connection.send(str.encode('Registeration Successful')) 
    print('Registered : ',name)
    print("{:<8} {:<20}".format('USER','PASSWORD'))
    for k, v in HashTable.items():
        label, num = k,v
        print("{:<8} {:<20}".format(label, num))
    print("-------------------------------------------")
    
else:
# If already existing user, check if the entered password is correct
    if(HashTable[name] == password):
        connection.send(str.encode('Connection Successful')) # Response Code for Connected Client 
        print('Connected : ',name)
    else:
        connection.send(str.encode('Login Failed')) # Response code for login failed
        print('Connection denied : ',name)

connection.close()
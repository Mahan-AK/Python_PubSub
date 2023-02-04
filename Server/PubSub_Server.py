import socket
import threading
from Server_Classes import NetHandler, ServerAuth


class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.conn = clientsocket
        print("New connection added: ", clientAddress)

    def run(self):
        net = NetHandler(clientsock)
        auth = ServerAuth(net)

        while True:
            try:
                Mtype, request = net.recv()
            except Exception as e:
                print(e)
                net.close()
                break

            if Mtype == 0:
                auth.resAuthentication(request)
            elif Mtype == 1:
                auth.resRegisteration(request)
            elif Mtype == 2:
                auth.resRole(request)
            elif Mtype == 3:
                auth.resPublish(request)
            elif Mtype == 4:
                auth.resSubSync(request)
            elif Mtype == 5:
                auth.resInfo(request)
            elif Mtype == 6:
                auth.resEOC(request)
                break
            
        print("Client at ", clientAddress, " disconnected...")


SERVER = "127.0.0.1"
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((SERVER, PORT))
print("Server started")
print("Waiting for client request..")

clients = []

try:
    while True:
        server.listen()
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.daemon = True
        newthread.start()
        clients.append(newthread)
except KeyboardInterrupt:
    print("\nTermination signal received, Ending all running processes...")
    for c in clients:
        c.conn.close()
import socket
import threading


class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.conn = clientsocket
        print("New connection added: ", clientAddress)

    def run(self):
        HEADERSIZE = 10

        while True:
            buff = self.conn.recv(HEADERSIZE)
            if not buff: break
            buff = int(buff.decode())
            data = self.conn.recv(buff)
            header = "{:<{}}".format(len(data), HEADERSIZE)
            self.conn.send(header.encode())
            self.conn.send(data)
        print("Client at ", clientAddress, " disconnected...")
        self.conn.close()


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
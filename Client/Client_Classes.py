import time
import json
import pickle


class Message:
    def __init__(self, data):
        self.id = int(time.time()*10000000)
        self.data = data


class NetHandler:
    def __init__(self, connection):
        self.connection = connection
        self.headersize = 10
        
    def send(self, Mtype, payload):
        payload = pickle.dumps(payload)
        header = f"{Mtype:<{1}}{len(payload):<{self.headersize-1}}".encode()

        self.connection.send(header)
        self.connection.send(payload)

    def recv(self):
        header = self.connection.recv(self.headersize).decode()
        Mtype, Psize = int(header[0]), int(header[1:])

        payload = pickle.loads(self.connection.recv(Psize))
        
        return Mtype, payload

    def close(self):
        self.connection.close()


class ClientAuth:
    def __init__(self, net, token=None):
        self.netHandler = net
        self.token = token

    def reqAuthentication(self, user, passwd):
        request = {
            "User": user,
            "Pass": passwd
        }

        self.netHandler.send(Mtype=0, payload=request)
        _, err = self.netHandler.recv()

        token = None
        if not err:
            _, token = self.netHandler.recv()
            self.token = token

            with open(".cache", 'wb') as f:
                pickle.dump((self.netHandler.connection.getpeername()[0], self.token), f)

        return err, self.reqInfo()

    def reqRegisteration(self, user, passwd):
        if not self.token: return 1

        request = {
            "token": self.token,
            "regUser": user,
            "regPass": passwd
        }

        self.netHandler.send(Mtype=1, payload=request)
        _, err = self.netHandler.recv()

        return err

    def reqRole(self, ServiceName, RoleType):
        if not self.token: return 1

        request = {
            "token": self.token,
            "ServiceName": ServiceName,
            "RoleType": RoleType
        }

        self.netHandler.send(Mtype=2, payload=request)
        _, err = self.netHandler.recv()

        return err

    def reqPublish(self, topic, message):
        if not self.token: return 1

        request = {
            "token": self.token,
            "Topic": topic,
            "Message": message
        }

        self.netHandler.send(Mtype=3, payload=request)
        _, err = self.netHandler.recv()

        return err

    def reqSubSync(self, topic):
        if not self.token: return 1, None

        with open("SyncHistory", 'r+') as sync_file:
            sync = json.load(sync_file)
            if topic not in sync: sync[topic] = 0

            request = {
                "token": self.token,
                "Topic": topic,
                "lastSync": sync[topic]
            }

            self.netHandler.send(Mtype=4, payload=request)
            _, err = self.netHandler.recv()

            messages = None
            if not err:
                _, messages = self.netHandler.recv()

            if not err and len(messages):
                sync[topic] = int(messages[-1][0])
                sync_file.seek(0)
                json.dump(sync, sync_file)

        return err, messages

    def reqInfo(self):
        if not self.token: return 1, None

        request = {
            "token": self.token
        }

        self.netHandler.send(Mtype=5, payload=request)
        _, err = self.netHandler.recv()

        if not err:
            _, info = self.netHandler.recv()

        return err, info

    def reqEOC(self):
        if not self.token: return 1

        request = {
            "token": self.token
        }

        self.netHandler.send(Mtype=6, payload=request)
        _, err = self.netHandler.recv()

        self.netHandler.close()

        return err
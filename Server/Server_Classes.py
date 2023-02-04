import time
import os
import json
import pickle
import base64
import hmac
import hashlib


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
        

class ServerAuth:
    def __init__(self, net):
        self.netHandler = net
        self.sessions = {}
        self.userDBPath = "DB/Users"
        self.topicDBPath = "DB/Topics"

    def __mkJWTToken(self, data):
        Header = {
            "alg": "HS256",
            "typ": "JWT"
        }

        Header64 = base64.urlsafe_b64encode(json.dumps(Header).replace(' ', '').encode()).decode()
        Payload64 = base64.urlsafe_b64encode(json.dumps(data).replace(' ', '').encode()).decode()

        secret = "pubsub"
        message = Header64+'.'+Payload64
        Signature = hmac.new(secret.encode(), msg=message.encode(), digestmod=hashlib.sha256).hexdigest()

        token = Header64+'.'+Payload64+'.'+Signature

        return token

    def __getTokenData(self, token):
        return json.loads(base64.urlsafe_b64decode(token.split('.')[1]))

    def resAuthentication(self, request):
        user = request["User"]
        hashed_pass = hashlib.sha256(request["Pass"].encode()).hexdigest()

        with open(self.userDBPath, 'r') as user_db:
            userTable = json.load(user_db)

        if user not in userTable:
            self.netHandler.send(Mtype=0, payload=1)
        elif userTable[user]["Pass"] != hashed_pass:
            self.netHandler.send(Mtype=0, payload=2)
        else:
            self.netHandler.send(Mtype=0, payload=0)

            data = {
                "User": user ##### MORE INFO + SESSION HANDLING
            }

            token = self.__mkJWTToken(data=data)
            self.netHandler.send(Mtype=0, payload=token)
            self.sessions.update({user: token})

    def resRegisteration(self, request):
        user = request["regUser"]
        hashed_pass = hashlib.sha256(request["regPass"].encode()).hexdigest()

        with open(self.userDBPath, 'r+') as user_db:
            userTable = json.load(user_db)

            orgUser = self.__getTokenData(request["token"])["User"]

            err = 0
            if userTable[orgUser]["Role"] != "Admin":
                err = 2
            elif user in userTable:
                err = 3
            else:
                userTable[user] = {"Pass": hashed_pass, "Role": "User", "Pub": [], "Sub": []}
                user_db.seek(0)
                json.dump(userTable, user_db)

        self.netHandler.send(Mtype=1, payload=err)

    def resRole(self, request):
        orgUser = self.__getTokenData(request["token"])["User"]

        with open(self.userDBPath, 'r+') as user_db:
            userTable = json.load(user_db)

            err = 0
            if request["ServiceName"] in userTable[orgUser][request["RoleType"]]:
                err = 2
            else:
                userTable[orgUser][request["RoleType"]].append(request["ServiceName"])
                user_db.seek(0)
                json.dump(userTable, user_db)

                Topic(request["ServiceName"]).addPublisherSubscriber(orgUser, request["RoleType"] == "Pub")

        self.netHandler.send(Mtype=2, payload=err)

    def resPublish(self, request):
        orgUser = self.__getTokenData(request["token"])["User"]

        topic = Topic(request["Topic"])

        err = 0
        if orgUser not in topic.getPublishers():
            err = 2
        else:
            topic.publish(message=request["Message"], publisher=orgUser)

        self.netHandler.send(Mtype=3, payload=err)

    def resSubSync(self, request):
        orgUser = self.__getTokenData(request["token"])["User"]

        topic = Topic(request["Topic"])

        err = 0
        if orgUser not in topic.getSubscribers():
            err = 2
        
        self.netHandler.send(Mtype=4, payload=err)

        if not err:
            self.netHandler.send(Mtype=4, payload=topic.syncSubMessages(request["lastSync"]))

    def resInfo(self, request):
        orgUser = self.__getTokenData(request["token"])["User"]

        err = 0
        with open(self.userDBPath, 'r+') as user_db:
            userTable = json.load(user_db)

            res = {
                "User": orgUser,
                "Pubs": userTable[orgUser]["Pub"],
                "Subs": userTable[orgUser]["Sub"],
                "Topics": os.listdir(self.topicDBPath)
            }
            
        self.netHandler.send(Mtype=5, payload=err)

        if not err:
            self.netHandler.send(Mtype=5, payload=res)

    def resEOC(self, request):
        # orgUser = self.__getTokenData(request["token"])["User"]
        # del self.sessions[orgUser]

        self.netHandler.send(Mtype=6, payload=0)
        self.netHandler.close()


class Topic:
    def __init__(self, name):
        self.name = name
        self.topicDBPath = "DB/Topics"

        if not os.path.exists(f"{self.topicDBPath}/{self.name}"):
            with open(f"{self.topicDBPath}/{self.name}", 'w') as f:
                json.dump({
                    "Publishers": [],
                    "Subscribers": [],
                    "Messages": {}
                }, f)

    def publish(self, message, publisher):
        with open(f"{self.topicDBPath}/{self.name}", 'r+') as f:
            topic = json.load(f)
            topic["Messages"][message.id] = {"publisher": publisher, "data": message.data}
            f.seek(0)
            json.dump(topic, f)

    def syncSubMessages(self, history):
        with open(f"{self.topicDBPath}/{self.name}", 'r') as f:
            topic = json.load(f)

            messages = []
            for id in topic["Messages"]:
                if int(id) > history:
                    messages.append((id, topic["Messages"][id]))

        return messages
            
    def addPublisherSubscriber(self, user, isPub):
        with open(f"{self.topicDBPath}/{self.name}", 'r+') as f:
            topic = json.load(f)
            
            if isPub: topic["Publishers"].append(user)
            else: topic["Subscribers"].append(user)

            f.seek(0)
            json.dump(topic, f)

    def getPublishers(self):
        with open(f"{self.topicDBPath}/{self.name}", 'r') as f:
            topic = json.load(f)
            
        return topic["Publishers"]
        
    def getSubscribers(self):
        with open(f"{self.topicDBPath}/{self.name}", 'r') as f:
            topic = json.load(f)
            
        return topic["Subscribers"]
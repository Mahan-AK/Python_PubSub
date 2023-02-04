import os
import time
import pickle
import socket
from Client_Classes import NetHandler, ClientAuth, Message
from optparse import OptionParser


usage = """python %prog [OPERATION] [ARGUMENTS]

Operations: auth -> authenticate to a pubsub server
            %prog auth [HOST]

            register -> register a new user (only applicable for root user)
            %prog register

            addrole -> become a publisher or a subscriber to a topic
            %prog addrole [ROLE] [TOPIC]

            publish -> publish a message to a topic that you are a publisher to
            %prog publish [TOPIC] [MESSAGE]

            publish_stream -> publish a stream of data from std_in to a topic that you are a publisher to
            %prog publish_stream [TOPIC]

            syncsub -> get new and unseen data from a topic that you have subscribed
            %prog syncsub [TOPIC]

            info -> get user info
            %prog info         

            syncsub_stream -> get data stream from a topic that you have subscribed
            %prog syncsub_stream [TOPIC]
"""

parser = OptionParser(usage=usage)
opts, args = parser.parse_args()

if not len(args):
    print("You must specify an operation.")
    parser.print_usage()
    exit()

SERVER, token = None, None
if args[0] == "auth":
    SERVER = args[1]
elif os.path.exists(".cache"):
    with open(".cache", 'rb') as f:
        SERVER, token = pickle.load(f)
else:
    print("You need to authenticate first!")
    exit()

PORT = 8080

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((SERVER, PORT))
    print(f"Connected to {SERVER} at {PORT}")
    net = NetHandler(client)
    auth = ClientAuth(net, token)

    if args[0] == "auth":
        user = input("Username: ")
        passwd = input("Password: ")

        err, info = auth.reqAuthentication(user, passwd)

        if not err:
            info = info[1]

            print(f"\nYour are logged in as: {info['User']}")
            print(f"You are publisher for these topics: {info['Pubs']}")
            print(f"You are subscribed to these topics: {info['Subs']}")
            print(f"Here's a list of all topics: {info['Topics']}")

        print(f"Error Code: {err}", end='')
        if err == 1:
            print("User not found!")
        elif err == 2:
            print("User Pass combination is Incorrect!")

    elif args[0] == "register":
        user = input("Username: ")
        passwd = input("Password: ")

        err = auth.reqRegisteration(user, passwd)

        print(f"Error Code: {err}", end='')
        if err == 1:
            print("You need to be logged in!")
        elif err == 2:
            print("You must be an Admin to be able to create accounts!")
        elif err == 3:
            print("Account already exists!")

    elif args[0] == "addrole":
        err = auth.reqRole(args[2], args[1])

        print(f"Error Code: {err}", end='')
        if err == 1:
            print("You need to be logged in!")
        elif err == 2:
            print("User already has the requested role!")

    elif args[0] == "publish":
        err = auth.reqPublish(args[1], Message(args[2]))

        print(f"Error Code: {err}", end='')
        if err == 1:
            print("You need to be logged in!")
        elif err == 2:
            print("User is not a publisher for the requested topic!")

    elif args[0] == "publish_stream":
        while True:
            try:
                line = input()
                err = auth.reqPublish(args[1], Message(line))
                if err:
                    print("Something bad happened!")
                    break
            except KeyboardInterrupt:
                break

    elif args[0] == "syncsub":
        err, messages = auth.reqSubSync(args[1])
        
        if not err:
            print(messages)
        elif err == 1:
            print("You need to be logged in!")
        elif err == 2:
            print("User is not a subscriber for the requested topic!")

    elif args[0] == "syncsub_stream":
        while True:
            try:
                err, messages = auth.reqSubSync(args[1])
                if err == 2:
                    print("User is not a subscriber for the requested topic!")
                    break

                for m in messages:
                    print(m)

                time.sleep(0.5)
            except KeyboardInterrupt:
                break

    elif args[0] == "info":
        _, info = auth.reqInfo()
        print(info)
        
    else:
        print("Invalid operation!")

    auth.reqEOC()
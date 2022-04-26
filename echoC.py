import socket


SERVER = "127.0.0.1"
PORT = 8080
HEADERSIZE = 10

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((SERVER, PORT))
    print(f"Connected to {SERVER} at {PORT}")

    while True:
        try:
            data = input(">> ")
        except KeyboardInterrupt:
            print("\nTermination signal received.. Exitting..")
            break
        if not data: data = ' '
        header = "{:<{}}".format(len(data), HEADERSIZE)
        try:
            client.send(header.encode())
            client.send(data.encode())
        except IOError:
            print("\nConnection dropped/Server shut down.")
            break
        buff = int(client.recv(HEADERSIZE).decode())
        print(client.recv(buff).decode())
        print()

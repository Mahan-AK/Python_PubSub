import socket
import ssl

hostname = 'localhost'
context = ssl.create_default_context()

with socket.create_connection((hostname, 8443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())
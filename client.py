import socket

HOST = "127.0.0.1"
PORT = 5050

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

name = input("Enter your name: ")
client.send(name.encode())

while True:
    message = client.recv(1024).decode()

    if not message:
        break

    print()
    print(message)

    if message == "GO!":
        input("Press Enter as fast as you can!")
        client.send("PRESSED".encode())

client.close()
# test_server.py
import socket
import json
import time

def start_test_server(host='0.0.0.0', port=9000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Test server listening on {host}:{port}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    try:
                        message = json.loads(data.decode('utf-8'))
                        print(f"Received: {message}")
                        # Echo back the message once per millisecond
                        while True:
                            conn.send(data)
                            time.sleep(0.1)
                        print(f"Sent: {message}")
                    except json.JSONDecodeError:
                        print("Received invalid JSON")


if __name__ == '__main__':
    start_test_server()

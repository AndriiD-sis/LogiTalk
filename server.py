import socket
import threading

HOST = '0.0.0.0'
PORT = 8080

clients = []
clients_lock = threading.Lock()

def broadcast(data, exclude=None):
    with clients_lock:
        for c in clients[:]:
            if c is exclude:
                continue
            try:
                c.sendall(data)
            except:
                try:
                    clients.remove(c)
                    c.close()
                except:
                    pass

def handle_client(sock, addr):
    print(f'[+] New conection: {addr}')

    try:
       while True:
           data = sock.recv(4096)
           if not data:
               break
           broadcast(data, exclude=sock)
    except Exception as e:
        print(f'[!] Client {addr} error{e}')
    finally:
        with clients_lock:
            if sock in clients:
                clients.remove(sock)
        sock.close()
        print(f'[-] Disconected: {addr}')

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f'Server running on {HOST}:{PORT}')
    try:
        while True:
            client_sock, addr = s. accept()
            with clients_lock:
                clients.append(client_sock)
            t = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('Server shutting down...')
    finally:
        s.close()
        with clients_lock:
            for c in clients:
                try:
                    c.close()
                except:
                    pass

if __name__ == '__main__':
    main()
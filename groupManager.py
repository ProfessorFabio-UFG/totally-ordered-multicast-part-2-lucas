from socket import *
import pickle
from constMP import GROUPMNGR_TCP_PORT, PEER_TCP_PORT

port = GROUPMNGR_TCP_PORT
membership = []  # lista de (ip, port, lamport_clock)

def serverLoop():
    serverSock = socket(AF_INET, SOCK_STREAM)
    serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSock.bind(('0.0.0.0', GROUPMNGR_TCP_PORT))
    serverSock.listen(6)
    print(f'Group Manager listening on port {GROUPMNGR_TCP_PORT}...')

    while True:
        conn, addr = serverSock.accept()
        msgPack = conn.recv(2048)
        req = pickle.loads(msgPack)

        if req["op"] == "register":
            ipaddr = req["ipaddr"]
            peer_port = req["port"]
            lamport_clock = req.get("lamport_clock", 0)
            exists = any(m[0] == ipaddr and m[1] == peer_port for m in membership)
            if not exists:
                membership.append((ipaddr, peer_port, lamport_clock))
                print('Registered peer:', req)
            else:
                print('Peer already registered:', req)

        elif req["op"] == "list":
            peer_list = []
            seen = set()
            for m in membership:
                ip, port, _ = m
                if port >= PEER_TCP_PORT and ip not in seen:
                    peer_list.append((ip, port))
                    seen.add(ip)
            print('List of peers sent:', peer_list)
            conn.send(pickle.dumps(peer_list))

        else:
            print('Unknown operation:', req["op"])

        conn.close()

if __name__ == "__main__":
    serverLoop()

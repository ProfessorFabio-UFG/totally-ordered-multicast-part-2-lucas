from socket import *
import threading
import pickle
import time
import sys
from constMP import *

if len(sys.argv) != 2:
    print("Uso: python peerCommunicator.py <peer_id>")
    sys.exit(1)

peer_id = int(sys.argv[1])
PEER_UDP_PORT_INST = PEER_UDP_PORT + peer_id
PEER_TCP_PORT_INST = PEER_TCP_PORT + peer_id

lamportClock = 0
myself = peer_id
log = []

# Endereços dos pares (será preenchido após consulta ao group manager)
peer_addresses = []

sendSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket.bind(('0.0.0.0', PEER_UDP_PORT_INST))

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSock.bind(('0.0.0.0', PEER_TCP_PORT_INST))
serverSock.listen(5)

# Diálogo por peer
DIALOGUES = {
    0: [
        "Olá, está na escuta?",
        "Precisamos verificar os suprimentos.",
        "Ótimo, iniciando procedimento."
    ],
    1: [
        "Sim, estou ouvindo.",
        "Verificado, tudo certo.",
        "Confirmado. Boa sorte."
    ]
}

NUM_MESSAGES = len(DIALOGUES[myself])

def sendMessage(msg, dest_ip, dest_port):
    global lamportClock
    lamportClock += 1
    msg_data = (lamportClock, myself, msg)
    sendSocket.sendto(pickle.dumps(msg_data), (dest_ip, dest_port))
    print(f"[{lamportClock}] Enviado para peer: {msg}")
    log.append((lamportClock, f"Sent: {msg}"))

def receiveMessages(expected_msgs):
    global lamportClock
    received = 0
    while received < expected_msgs:
        data, addr = recvSocket.recvfrom(2048)
        recv_clock, sender_id, msg = pickle.loads(data)
        lamportClock = max(lamportClock, recv_clock) + 1
        print(f"[{lamportClock}] Recebido de peer {sender_id}: {msg}")
        log.append((lamportClock, f"Received: {msg}"))
        received += 1

def waitToStart():
    conn, addr = serverSock.accept()
    data = conn.recv(1024)
    num_msgs = pickle.loads(data)
    conn.send(pickle.dumps(f"Peer {myself} pronto"))
    conn.close()
    return num_msgs

def getPeers():
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    req = {"op": "list"}
    clientSock.send(pickle.dumps(req))
    msg = clientSock.recv(2048)
    clientSock.close()
    return pickle.loads(msg)

def registerWithGroupManager():
    global lamportClock
    ip = gethostbyname(gethostname())
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    req = {"op": "register", "ipaddr": ip, "port": PEER_TCP_PORT_INST, "lamport_clock": lamportClock}
    clientSock.send(pickle.dumps(req))
    lamportClock += 1
    clientSock.close()

def sendLogs():
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((SERVER_ADDR, SERVER_PORT))
    clientSock.send(pickle.dumps(log))
    clientSock.close()
    print("Log enviado ao servidor de comparação.")

def main():
    registerWithGroupManager()
    num_msgs = waitToStart()
    peer_list = getPeers()

    # Espera encontrar o outro peer
    other_peers = [p for p in peer_list if p[1] != PEER_TCP_PORT_INST]
    if not other_peers:
        print("Esperando outro peer entrar no grupo...")
        while not other_peers:
            time.sleep(2)
            other_peers = [p for p in getPeers() if p[1] != PEER_TCP_PORT_INST]

    other_ip, _ = other_peers[0]

    print(f"Conversando com peer em {other_ip}")

    # Peer 0 começa, peer 1 escuta primeiro
    if myself == 0:
        for i in range(NUM_MESSAGES):
            sendMessage(DIALOGUES[myself][i], other_ip, PEER_UDP_PORT + 1)
            time.sleep(1)
            receiveMessages(1)
    else:
        for i in range(NUM_MESSAGES):
            receiveMessages(1)
            time.sleep(1)
            sendMessage(DIALOGUES[myself][i], other_ip, PEER_UDP_PORT)

    sendLogs()

if __name__ == "__main__":
    main()

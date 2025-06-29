from socket import *
import threading
import random
import time
import pickle
from requests import get
from constMP import *
import sys

if len(sys.argv) != 2:
    print("Uso: python peer.py <peer_id>")
    sys.exit(1)

peer_id = int(sys.argv[1])

PEER_UDP_PORT_INST = PEER_UDP_PORT + peer_id
PEER_TCP_PORT_INST = PEER_TCP_PORT + peer_id

lamportClock = 0
myself = None
NUM_MESSAGES = 0  # valor padrão

sendSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket.bind(('0.0.0.0', PEER_UDP_PORT_INST))

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSock.bind(('0.0.0.0', PEER_TCP_PORT_INST))
serverSock.listen(5)

# Mensagens temáticas por peer
ROLE_MESSAGES = {
    0: "Iniciando análise de área.",
    1: "Equipes médicas prontas.",
    2: "Checando suprimentos.",
    3: "Planejando rota de evacuação.",
    4: "Confirmando comunicação com base.",
    5: "Drones enviados para reconhecimento."
}

def get_public_ip():
    try:
        ip = get('https://api.ipify.org').text
        return ip
    except:
        return '127.0.0.1'

def registerWithGroupManager():
    global lamportClock
    clientSock = socket(AF_INET, SOCK_STREAM)
    print('Connecting to group manager:', (GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    ipAddr = get_public_ip()
    req = {"op": "register", "ipaddr": ipAddr, "port": PEER_TCP_PORT_INST, "lamport_clock": lamportClock}
    msg = pickle.dumps(req)
    lamportClock += 1
    print('Registering with group manager:', req)
    clientSock.send(msg)
    clientSock.close()

def sendMessage(msg, addrToSend):
    global lamportClock
    lamportClock += 1
    msg = (lamportClock, msg)
    msgPack = pickle.dumps(msg)
    sendSocket.sendto(msgPack, (addrToSend, PEER_UDP_PORT_INST))
    print(f"Sent message with timestamp {lamportClock}: {msg[1]}")

def receiveMessage():
    global lamportClock
    msgPack = recvSocket.recvfrom(1024)
    receivedLamportClock, msg = pickle.loads(msgPack[0])
    lamportClock = max(lamportClock, receivedLamportClock) + 1
    print(f"Received message with timestamp {lamportClock}: {msg}")

def waitToStart():
    global myself
    conn, addr = serverSock.accept()
    msgPack = conn.recv(1024)
    msg = pickle.loads(msgPack)
    myself = msg[0]
    nMsgs = msg[1]
    conn.send(pickle.dumps('Peer process ' + str(myself) + ' started.'))
    conn.close()
    return (myself, nMsgs)

def sendLogs():
    global lamportClock, NUM_MESSAGES
    log = []
    for i in range(NUM_MESSAGES):
        lamportClock += 1
        msg = f"[{i+1}/{NUM_MESSAGES}] {ROLE_MESSAGES.get(myself, 'Mensagem padrão')} (peer {myself})"
        log.append((lamportClock, msg))
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((SERVER_ADDR, SERVER_PORT))
    clientSock.send(pickle.dumps(log))
    clientSock.close()
    print(f"Sent log of {len(log)} messages to comparison server.")

def main():
    global NUM_MESSAGES
    registerWithGroupManager()
    myself, nMsgs = waitToStart()
    NUM_MESSAGES = nMsgs
    print(f"Peer {myself} starting with {NUM_MESSAGES} messages.")

    for i in range(NUM_MESSAGES):
        msg_content = f"[{i+1}/{NUM_MESSAGES}] {ROLE_MESSAGES.get(myself, 'Mensagem padrão')} (peer {myself})"
        sendMessage(msg_content, "127.0.0.1")
        time.sleep(random.uniform(0.5, 1.0))

    sendLogs()

if __name__ == "__main__":
    main()

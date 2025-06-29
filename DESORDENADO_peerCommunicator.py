from socket import *
import threading
import random
import time
import pickle
import sys
from constMP import *
from requests import get

if len(sys.argv) != 2:
    print("Uso: python peerCommunicator.py <peer_id>")
    sys.exit(1)

peer_id = int(sys.argv[1])
PEER_UDP_PORT_INST = PEER_UDP_PORT + peer_id
PEER_TCP_PORT_INST = PEER_TCP_PORT + peer_id
myself = peer_id
log = []
NUM_MESSAGES = 0

sendSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket.bind(('0.0.0.0', PEER_UDP_PORT_INST))

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSock.bind(('0.0.0.0', PEER_TCP_PORT_INST))
serverSock.listen(5)

NAMES = {0: "VERMELHO", 1: "AZUL"}

PERSON_MESSAGES = {
    0: [
        "Olá, você está na escuta?",
        "Como está o andamento da missão?",
        "Recebi um relatório da situação.",
        "Temos confirmação de posição.",
        "Tudo conforme o esperado?",
        "Já deu algum problema?",
        "Está tudo tranquilo por aí?",
        "Temos tudo sob controle.",
        "Precisamos revisar o plano?",
        "Confirmado, seguimos em frente.",
        "Prepare-se para a próxima etapa.",
        "Boa sorte aí!",
        "Mantenha a segurança.",
        "Retornaremos em breve.",
        "Missão quase concluída."
    ],
    1: [
        "Na escuta, pode falar.",
        "O andamento está dentro do previsto.",
        "Recebida, aguardando detalhes.",
        "Posição confirmada aqui.",
        "Tudo certo, sem problemas.",
        "Nada a relatar até agora.",
        "Sim, aqui está tranquilo.",
        "Perfeito, estamos preparados.",
        "Revisão do plano não necessária.",
        "Entendido, sigo adiante.",
        "Tudo pronto para próxima etapa.",
        "Obrigado, seguimos com atenção.",
        "Segurança reforçada.",
        "Permanecemos em alerta.",
        "Missão finalizada, voltando."
    ]
}

def get_public_ip():
    try:
        return get('https://api.ipify.org').text.strip()
    except:
        return '127.0.0.1'

def registerWithGroupManager():
    ip = get_public_ip()
    print(f"[INFO] Registrando com IP: {ip}")
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    req = {"op": "register", "ipaddr": ip, "port": PEER_TCP_PORT_INST}
    clientSock.send(pickle.dumps(req))
    clientSock.close()

def sendMessageThread(dest_ip, dest_port):
    for i in range(NUM_MESSAGES):
        time.sleep(random.uniform(0.5, 1.5))
        msg = PERSON_MESSAGES[myself][i]
        sendSocket.sendto(pickle.dumps((myself, msg)), (dest_ip, dest_port))
        print(f"{NAMES[myself]}: {msg}")
        log.append(f"{NAMES[myself]}: {msg}")

def receiveMessageThread():
    for _ in range(NUM_MESSAGES):
        data, addr = recvSocket.recvfrom(2048)
        sender_id, msg = pickle.loads(data)
        print(f"{NAMES[sender_id]}: {msg}")
        log.append(f"{NAMES[sender_id]}: {msg}")

def waitToStart():
    conn, addr = serverSock.accept()
    data = conn.recv(1024)
    peer_number, num_msgs = pickle.loads(data)
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

def sendLogs():
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((SERVER_ADDR, SERVER_PORT))
    clientSock.send(pickle.dumps(log))
    clientSock.close()
    print("Log enviado ao servidor de comparação.")

def main():
    global NUM_MESSAGES
    registerWithGroupManager()
    NUM_MESSAGES = waitToStart()

    peer_list = getPeers()
    other_peers = [p for p in peer_list if p[1] != PEER_TCP_PORT_INST]

    while not other_peers:
        print("Esperando outro peer no grupo...")
        time.sleep(2)
        peer_list = getPeers()
        other_peers = [p for p in peer_list if p[1] != PEER_TCP_PORT_INST]

    other_ip, _ = other_peers[0]
    other_peer_id = 0 if myself == 1 else 1
    print(f"\nConversa entre {NAMES[myself]} e {NAMES[other_peer_id]} iniciada!\n")

    # Iniciar threads paralelas
    sender = threading.Thread(target=sendMessageThread, args=(other_ip, PEER_UDP_PORT + other_peer_id))
    receiver = threading.Thread(target=receiveMessageThread)

    sender.start()
    receiver.start()

    sender.join()
    receiver.join()

    sendLogs()

if __name__ == "__main__":
    main()

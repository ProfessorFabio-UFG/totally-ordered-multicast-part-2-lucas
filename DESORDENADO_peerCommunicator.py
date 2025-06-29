
from socket import *
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
myself = peer_id
log = []

sendSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket.bind(('0.0.0.0', PEER_UDP_PORT_INST))

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSock.bind(('0.0.0.0', PEER_TCP_PORT_INST))
serverSock.listen(5)

NAMES = {0: "Pessoa 1", 1: "Pessoa 2"}

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

def sendMessage(msg, dest_ip, dest_port):
    msg_data = (myself, msg)
    sendSocket.sendto(pickle.dumps(msg_data), (dest_ip, dest_port))
    print(f"{NAMES[myself]}: {msg}")
    log.append(f"{NAMES[myself]}: {msg}")

def receiveMessage():
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

def registerWithGroupManager():
    ip = get_public_ip()
    print(f"[INFO] Registrando com IP: {ip}")
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    req = {"op": "register", "ipaddr": ip, "port": PEER_TCP_PORT_INST}
    clientSock.send(pickle.dumps(req))
    clientSock.close()

def sendLogs():
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((SERVER_ADDR, SERVER_PORT))
    clientSock.send(pickle.dumps(log))
    clientSock.close()
    print("Log enviado ao servidor de comparação.")

def get_public_ip():
    from requests import get
    try:
        return get('https://api.ipify.org').text.strip()
    except:
        return '127.0.0.1'

def main():
    registerWithGroupManager()
    num_msgs = waitToStart()
    peer_list = getPeers()

    other_peers = [p for p in peer_list if p[1] != PEER_TCP_PORT_INST]
    while not other_peers:
        print("Esperando outro peer no grupo...")
        time.sleep(2)
        peer_list = getPeers()
        other_peers = [p for p in peer_list if p[1] != PEER_TCP_PORT_INST]

    other_ip, _ = other_peers[0]
    print(f"\n Conversa iniciada entre {NAMES[0]} e {NAMES[1]}\n")

    for i in range(num_msgs):
        if myself == 0:
            sendMessage(PERSON_MESSAGES[0][i], other_ip, PEER_UDP_PORT + 1)
            time.sleep(0.5)
            receiveMessage()
        else:
            receiveMessage()
            time.sleep(0.5)
            sendMessage(PERSON_MESSAGES[1][i], other_ip, PEER_UDP_PORT)

    sendLogs()

if __name__ == "__main__":
    main()

from socket import *
import pickle
from constMP import *

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSock.bind(('0.0.0.0', SERVER_PORT))
serverSock.listen(6)

def mainLoop():
    print(f'Comparison Server listening on port {SERVER_PORT}')
    while True:
        nMsgs = int(input('Enter number of messages for each peer to send (0 to exit): '))
        if nMsgs == 0:
            break

        clientSock = socket(AF_INET, SOCK_STREAM)
        clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
        req = {"op": "list"}
        clientSock.send(pickle.dumps(req))
        msg = clientSock.recv(2048)
        clientSock.close()
        peerList = pickle.loads(msg)
        print('Peers:', peerList)

        startPeers(peerList, nMsgs)
        print('Waiting for message logs from peers...')
        receiveLogs(len(peerList))

    serverSock.close()

def startPeers(peerList, nMsgs):
    for peerNumber, peer in enumerate(peerList):
        try:
            clientSock = socket(AF_INET, SOCK_STREAM)
            clientSock.connect((peer[0], peer[1]))
            msg = (peerNumber, nMsgs)
            clientSock.send(pickle.dumps(msg))
            response = pickle.loads(clientSock.recv(512))
            print(f'Peer {peerNumber} started: {response}')
            clientSock.close()
        except Exception as e:
            print(f'Error starting peer {peerNumber} ({peer[0]}): {e}')

def receiveLogs(numPeers):
    numReceived = 0
    while numReceived < numPeers:
        conn, addr = serverSock.accept()
        msgPack = conn.recv(32768)
        conn.close()
        log_data = pickle.loads(msgPack)
        print(f"\n--- Log do peer {numReceived} ---")
        for line in log_data:
            print(line)
        numReceived += 1
    print('\nTodos os logs recebidos.\n')

if __name__ == "__main__":
    mainLoop()

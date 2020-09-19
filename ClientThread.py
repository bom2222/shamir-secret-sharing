import threading
from Codes import *


class ClientThread(threading.Thread):
    def __init__(self, connection, cmd):
        threading.Thread.__init__(self)
        self.connection = connection
        self.cmd = cmd
        self.secretPart = None


    def run(self):
        try:
            if self.cmd == "s":
                self.send_to_clients()
            elif self.cmd == "g":
                self.recv_secret_from_clients()
        except:
            print "Lost connection..."


    def send_to_clients(self):
        lenSending = len(self.secret)
        protocolTx = str(SEND_SECRET) + SEPERATOR
        msg = protocolTx + self.secret
        self.connection.sendall(msg)
        print "Secret Shared..."


    def recv_secret_from_clients(self):
        self.connection.send(str(GET_SECRET))
        data = self.connection.recv(SOCKET_SIZE)
        self.secretPart = data
        print "Secret Recieved..."


    def has_secret_part(self):
        return not self.secretPart == None

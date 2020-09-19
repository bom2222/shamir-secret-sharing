import socket
from thread import *
import sys
from Codes import *
import time
import ClientThread
import ShamirScheme


host = ''
port = 0
secret = ""
num_shares = -1
threads = []
threadInputCmds = "X"
threshold = -1
numClientsOnline = 0

def init():
    global host, port, serverAddress

    # print socket.geta
    if len(sys.argv) == 1:
        host = "localhost"
        port = 5252
    elif not len(sys.argv) == 3:
        print "Arguments are: [host] [port], leave as blank for localhost"
        sys.exit()
    elif len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])


def get_arguments(allArgs=True):
    global secret, num_shares, threshold

    print "Leave all Blank for default values"
    print "Enter a Secret (String): ",
    secret = get_user_input()
    if secret == "":
        secret = "thisisasharedsecretvaluethatwillbesharedwithNusersandaTthreshold"

    if allArgs:
        print "Enter Max Number of Clients: ",
        num_shares = -1

        while num_shares < 0:
            num_shares = get_user_input()

            try:
                if num_shares == "":
                    num_shares = "2"
                elif int(num_shares) <= 1:
                    num_shares = -1
                    print "Number of Clients must be greater than 1: ",

                num_shares = int(num_shares)
            except:
                num_shares = -1
                print "Number of Clients must be a number: ",
        # end while

        print "Enter a Threshold Size (Integer, <= # Clients, > 1): ",

        threshold = -1
        while threshold < 0:
            threshold = get_user_input()

            try:
                if threshold == "":
                    threshold = "2"

                threshold = int(threshold)

                if threshold <= 1:
                    threshold = -1
                    print "Threshold must be greater than 1: ",
                elif threshold > num_shares:
                    threshold = -1
                    print "Threshold must be smaller or equal to the number of Clients, {0}: ".format(num_shares),
            except:
                threshold = -1
                print "Threshold must be a number: ",

        threshold = int(threshold)
    print (secret, num_shares, threshold)


def bind_server_socket(sock):
    successful = False
    print "Host: {0} Port: {1}".format(host, port)
    serverAddress = (host, port)

    while not successful:
        try:
            sock.bind(serverAddress)
            successful = True
        except socket.error as msg:
            print "Bind failed. Error Code: {0} Message: {1}".format(msg[0], msg[1])
            time.sleep(2)


def serv():
    global recievedSecrets

    shamirScheme = ShamirScheme.ShamirScheme()
    splitSecrets = shamirScheme.split_secret(secret, num_shares, threshold)

    keepRunning = True
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_server_socket(serverSocket)
    serverSocket.listen(num_shares)

    start_new_thread(connection_thread, (serverSocket,))
    wait_for_all_clients()

    try:
        while keepRunning:
            while True:
                print "Enter Command ([s,g,e], h for help): ",
                threadInputCmds = get_user_input()

                if threadInputCmds == SEND_MSG:
                    ''' Send shares to clients '''
                    share = iter(splitSecrets)

                    for t in threads:
                        msg = build_message(share.next())
                        t.cmd = threadInputCmds
                        t.secret = msg
                        t.run()
                elif threadInputCmds == GET_MSG:
                    ''' Sends the tx secret command to each client, and they send their part
                    back to the server, the server waits for the threshold number of clients
                    to respond, and then will recombine the secret and print it out'''
                    for t in threads:
                        t.cmd = threadInputCmds
                        t.run()
                    receivedMsg = wait_for_threshold_responses()
                    receivedSecret = []
                    for msg in receivedMsg:
                        t = recover_message(msg)

                        if not t == None:
                            receivedSecret.append(t)

                    combinedSecret = shamirScheme.recover_secret(receivedSecret)
                    print "The Recovered Secret is: {0}".format(combinedSecret)
                elif threadInputCmds == HELP:
                    print "s - Split and Send Secret\ng - Get and Recombine Secret\ne - Exit"
                elif threadInputCmds == EXIT:
                    keepRunning = False
                    break
                else:
                    print "Unknown Command"
        # end while
    except socket.error as msg:
        print "Bind failed. Error Code: {0} Message: {1}".format(msg[0], msg[1])
        serverSocket.close()
        sys.exit()
    except:
        print "Error: {0}".format(error)
    finally:
        print "Closing Server"
        serverSocket.close()
        close_clients()
        sys.exit()
    # end try
# end serv


# this accepts a connection and adds it to the thread pool, as long as the connection amount isn't
# greater than the num_shares
def connection_thread(serverSocket):
    global numClientsOnline, threshold

    while True:
        connection, clientAddress = serverSocket.accept()
        numClientsOnline = numClientsOnline + 1
        print "Client connected, Accepted From: {0}, minimum number left to connect: {1}".format(clientAddress, num_shares - numClientsOnline)
        clientThread = ClientThread.ClientThread(connection, "X")
        threads.append(clientThread)


def get_user_input():
    return raw_input()


def close_clients():
    for t in threads:
        try:
            t.connection.send(str(STOP_RECEIVING))
            time.sleep(1)
            t.connection.close()
        except IOError, e:
            pass

def wait_for_all_clients():
    print "Waiting for {0} Clients".format(num_shares)
    global numClientsOnline, num_shares

    while numClientsOnline < num_shares:
        time.sleep(1)
    print "All Clients Connected"


def wait_for_threshold_responses():
    recievedSecrets = []
    timeout = 20

    for t in threads:
        i = 0

        while not t.has_secret_part():
            print "Waiting... {0}".format(i)
            i = i + 1
            time.sleep(1)

            if i == threshold:
                # wait a lot less if we have enough secrets
                timeout = 5

            if i > timeout:
                print "Timed out waiting for responses"
                break
        # end while

        if t.has_secret_part():
            recievedSecrets.append(t.secretPart)
            t.secretPart = ""

    return recievedSecrets
# end waitForThresholdResponses


def build_message(indexMsgTuple):
    index = indexMsgTuple[0]
    share = indexMsgTuple[1]
    msg = index + ";;" + share

    return msg


def recover_message(msgReceived):
    if msgReceived == "":
        return None

    tokens = msgReceived.split(";;")
    index = tokens[0]
    share = tokens[1]

    return (index, share)


init()
get_arguments()
serv()

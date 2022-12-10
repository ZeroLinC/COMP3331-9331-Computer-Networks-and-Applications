"""
    Python 3
    Usage: python3 client.py server_IP server_port client_udp_server_port
    coding: utf-8
    
    Author: Hongyu Chen z5097965
"""
from socket import *
from threading import Thread
import time
import sys
import os



def TCP_process(clientSocket, UDPserverPort):
    
    # set loginState to False to initiate it
    loginState = False
    
    # ask for username for the first time
    username = input("> Username: ").strip()
    
    #start login process
    while not loginState:
        # ask for password for the first time
        password = input("> Password: ").strip()
        
        # send the credential to server
        message = "CREDENTIAL$$"+username+" "+password
        clientSocket.send(message.encode())
        
        # reveive response from server,
        # this will tell that credential is credential is right or not
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        dataType, receivedMessage = receivedMessage.split("$$")
        
        # the first is just for very special case
        if receivedMessage == "":
            print("> [recv] Message from server is empty!")
        # this means credential is right
        elif receivedMessage == "welcome":
            print("> Welcome!")
            message = "UDPserverPortNUM$$"+str(UDPserverPort)
            clientSocket.send(message.encode())
            loginState = True
        # this will tell user password is wrong
        # and ask for it agian
        elif receivedMessage == "Invalid password":
            print("> Invalid Password. Please try again")
        # this will tell user username is wrong
        # and ask for it again
        elif receivedMessage == "Invalid username":
            print("> Invalid Username. Please try again")
            username = input("> Username: ").strip()
        # this will tell user, he/she/it/they is blocked
        # and send the UDP port to server
        # for asking shut down this client's UDP
        # and jump to end to close TCP
        elif receivedMessage == 'blocked':
            print("> Invalid Password. Your account has been blocked. Please try again later")
            message = "UDPserverPortNUM$$"+str(UDPserverPort)
            clientSocket.send(message.encode())
            break
        # this will tell user, he/she/it/they is already blocked
        # and send the UDP port to server
        # for asking shut down this client's UDP
        # and jump to end to close TCP
        elif receivedMessage == "In blocked duration":
            print("> Your account is blocked due to multiple authentication failures. Please try again later")
            message = "UDPserverPortNUM$$"+str(UDPserverPort)
            clientSocket.send(message.encode())
            break
            
    # after log in
    while loginState:
        # ask for a COMMAND and give REMINDER
        message = input("> Enter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF)\n> (Reminder: you may wait for few time until the server finishes other's processing):\n").strip()
        
        # for a correct command, the first is commandtype, them follows argument(s)
        # for each command, the client side will firstly check
        # its format
        command_list = message.split(" ")
        command = command_list[0]
        
        # send OUT command to server
        # and wait the response from server
        # then excute
        if command == 'OUT':
            if len(command_list) != 1:
                print("> OUT command requires no argument.")
            else:
                clientSocket.send(message.encode())
                data = clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "go":
                    print(f"> Bye, {username}!")
                    loginState = False
        
        # send EDG with arguments to server
        # and wait response to start
        elif command == "EDG":
            if len(command_list) != 3:
                print("> EDG command requires fileID and dataAmount as arguments.")
            elif (not command_list[1].isdigit()) or (not command_list[2].isdigit()):
                print("> The fileID or dataAmount are not integers, you need to specify the parameter as integers.")
            elif command_list[2] == "0":
                print("> The data size should be great than 0.")
            else:
                file_ID = command_list[1]
                data_size = command_list[2]
                clientSocket.send(message.encode())
                data = clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "start":
                    # create file name
                    sample_name = username+"-"+file_ID+".txt"
                    # create the data based on data size
                    new = ""
                    for i in range(int(data_size)):
                        new = new + str(i + 1) + "\n"
                    new = new[:-1]
                    f = open(sample_name, "w")
                    f.write(new)
                    f.close()
                    # tell server the process finishes
                    message = "EDG$$Done"
                    clientSocket.send(message.encode())
        
        # send UED with arguments to server
        # and wait response to start
        elif command == "UED":
            if len(command_list) != 2:
                print("> only one fileID is needed to upload the data.")
            elif not command_list[1].isdigit():
                print("> The fileID is not integer, you need to specify the parameter as integer.")
            else:
                filename = username+"-"+command_list[1]+".txt"
                if not os.path.exists(filename):
                    print("> the file to be uploaded does not exist.")
                else:
                    clientSocket.send(message.encode())
                    data = clientSocket.recv(1024)
                    message = data.decode()
                    dataType, message = message.split("$$")
                    if message == "receive command":
                        # read file in a size of buffer size 1024
                        f = open(filename, 'rb')
                        data = f.read(1024)
                        send_num = 1
                        while data:
                            clientSocket.send(data)
                            print(f">>> sending {send_num}...")
                            send_num += 1
                            data = f.read(1024)
                            time.sleep(0.005)
                        f.close()
                        # send a 0 value to stop receiver loop
                        clientSocket.send("".encode())
                        data = clientSocket.recv(1024)
                        message = data.decode()
                        dataType, message = message.split("$$")
                        # server give the feedback if it receive the data
                        if message == "Done":
                            print(f"> Data file with ID of {command_list[1]} has been uploaded to server")
        
        # send SCS with arguments to server
        # and wait result from server
        elif command == "SCS":
            operation_list = ["AVERAGE", "MAX", "MIN", "SUM"]
            if len(command_list) != 3:
                print("> number of arguments is wrong, correct arguments are 2.")
            elif not command_list[1].isdigit():
                print("> fileID is missing or fileID should be an integer.")
            elif command_list[2] not in operation_list:
                print("> Wrong operation code, should be SUM, MAX, MIN or AVERAGE")
            else:
                fileID = command_list[1]
                operation = command_list[2]
                clientSocket.send(message.encode())
                data = clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "no such file":
                    print(f"> the file with fileID {fileID} does not exist at server side\nPlease check fileID or upload that file")
                else:
                    print(f"> Computation ({operation}) result on the file (ID: {fileID}) returned from the server is: {message}")
        
        # send DTE with argument to server
        # and wait response from server
        elif command == "DTE":
            if len(command_list) != 2:
                print("> only one fileID is needed, correct arguments are 1.")
            elif not command_list[1].isdigit():
                print("> fileID should be an integer.")
            else:
                fileID = command_list[1]
                clientSocket.send(message.encode())
                data = clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "no such file":
                    print(f"> the file with fileID {fileID} does not exist at server side\nPlease check fileID")
                elif message == "Done":
                    print(f"> file with fileID {fileID} has been successfully removed from central server")
        
        # send AED to server
        # and wait response from server
        elif command == "AED":
            if len(command_list) != 1:
                print("> AED command requires no argument.")
            else:
                clientSocket.send(message.encode())
                data = clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "no other active device":
                    print("> no other active edge devices")
                else:
                    print(f"> Other active edge device:\n{message}")
        
        # send UVF with arguments to server
        # and wait response from server
        elif command == "UVF":
            aud_username = command_list[1]
            if len(command_list) != 3:
                print("> Missing Audience edge device name or file name to be uploaded")
            else:
                filename = command_list[2]
                if not os.path.exists(filename):
                    print(f"> No such {filename} file in current directory, please check")
                else:
                    clientSocket.send(message.encode())
                    data = clientSocket.recv(1024)
                    message = data.decode()
                    dataType, message = message.split("$$")
                    if message == "Invalid audience":
                        print("> No such audience edge device, please check with command AED")
                    elif message == "not active":
                        print("> such audience edge device is not currently active")
                    else:
                        # receive the destination UDP IP and Port number
                        aud_IP, aud_UDPserverPort = message.strip().split(";")
                        # set client UDP here, and send this username and file name
                        # to destination side
                        UDPclientSocket = socket(AF_INET, SOCK_DGRAM)
                        message = "UVF"+"$$"+username+";"+filename
                        UDPclientSocket.sendto(message.encode(),(aud_IP, int(aud_UDPserverPort)))
                        # wait a few ms to avoid errors
                        time.sleep(0.005)
                        # read file and send data
                        f = open(filename, "rb")
                        data = f.read(1024)
                        packet_num = 1
                        while data:
                            if UDPclientSocket.sendto(data,(aud_IP, int(aud_UDPserverPort))):
                                print(f">>> sending {packet_num}...")
                                data = f.read(1024)
                                packet_num += 1
                                time.sleep(0.005)
                        f.close()
                        UDPclientSocket.sendto("".encode(),(aud_IP, int(aud_UDPserverPort)))
                        UDPclientSocket.close()
                        print(f"> {filename} has been uploaded to {aud_username}")
                        # tell server sending process is done
                        message = "UVF$$Done"
                        clientSocket.send(message.encode())
        
        # for all other inputs that does not have
        # a correct command
        else:
            print("> Error. Invalid command!")
    
    # close the socket
    clientSocket.close()

# set a keep listening UDP 
def UDP_process(UDPserverSocket, UDPserverAddress):
    while True:
        UDPdata, tuple_ip_port = UDPserverSocket.recvfrom(1024)
        UDPmessage = UDPdata.decode()
        # command to close UDP, will be use when
        # TCP close
        if UDPmessage == "OUT":
            break
        else:
            command, new_filename = UDPmessage.split("$$")
            # doing UVF (peer to peer), this is the audience side
            if command == "UVF":
                sender_name, old_filename = new_filename.split(";")
                new_filename = sender_name+"_"+old_filename
                # open a new file, and receive packets, then write the data
                f = open(new_filename, "wb")
                UDPdata, tuple_ip_port = UDPserverSocket.recvfrom(1024)
                receive_num = 1
                while UDPdata:
                    print(f">>> receiving {receive_num}...")
                    receive_num += 1
                    f.write(UDPdata)
                    UDPdata, tuple_ip_port = UDPserverSocket.recvfrom(1024)
                f.close
                # open the file in read mode
                # to make file correct
                f = open(new_filename, "r")
                f.close()
                print(f"> Received {old_filename} from {sender_name}")
                # the same with TCP input, while this is end of UDP
                print("> Enter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):\n> (Reminder: you may wait for few time until the server finishes other's processing):")
                # wait for 1s, to avoid unexpected error
                time.sleep(1)
    
    # close UDP
    UDPserverSocket.close()  
    
def main():
    #Server would be running on the same host as Client
    if len(sys.argv) != 4:
        print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
        exit(0)
    serverHost = sys.argv[1]
    serverPort = int(sys.argv[2])
    UDPserverPort = int(sys.argv[3])
    serverAddress = (serverHost, serverPort)
    UDPserverAddress = (serverHost, UDPserverPort)

    # define a TCP socket for the client side, it would be used to communicate with the server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    # define a UDP socket as server(audience) side, it would receive data from other peer
    UDPserverSocket = socket(AF_INET, SOCK_DGRAM)

    # build connection with the server and send message to it
    clientSocket.connect(serverAddress)
    # build connection with a specifi UDP address
    UDPserverSocket.bind(UDPserverAddress)
    
    # create TCP thread
    TCP_p = Thread(target=TCP_process, args=(clientSocket, UDPserverPort,))
    TCP_p.start()
    
    # create UDP thread
    UDP_p = Thread(target=UDP_process, args=(UDPserverSocket, UDPserverAddress))
    UDP_p.start()
    
if __name__ == '__main__':
    main()

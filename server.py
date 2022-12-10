"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 server.py server_port number_of_consecutive_failed_attempts
    coding: utf-8
    
    Author: Hongyu Chen z5097965
"""
from socket import *
from threading import Thread
import sys, select
import datetime
import time
import os

# acquire server host and port from command line parameter
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 server.py SERVER_PORT num_times_to_block======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])

# check number_of_consecutive_failed_attempts should be an integer
if not sys.argv[2].isdigit():
    print("\n===== Error usage, number_of_consecutive_failed_attempts should be an integer======\n")
    exit(0)
blocked_time = int(sys.argv[2])

# check number_of_consecutive_failed_attempts should be 1 to 5
if blocked_time < 1 or blocked_time > 5:
    print("\n===== Error usage, num_times_to_block should be an integer between 1 and 5, including 1 and 5======\n")
    exit(0)
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

# to add user which is blocked
blocked_user = []

# to store the time that a user will be blocked till
end_block_time = {}

# to check if other client is in processing
in_use = False

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.loginState = False
        print("===== New connection created for: ", clientAddress)
        
        
    def run(self):
        global blocked_user
        global end_block_time
        global in_use
        # initiate message to avoid unexpected error
        message = "ERROR$$"
        # num ber of attempts to log in
        trying = 0
        
        # log in process
        while not self.loginState:
            # receive credentials from client
            data = self.clientSocket.recv(1024)
            
            # record receive time
            current_time = datetime.datetime.now()
            message = data.decode()
            dataType, usernameAndpassword = message.split("$$")
            username, password = usernameAndpassword.split(" ")
            
            # first check if username is still blocked
            if username in blocked_user:
                # if still blocked
                # give response
                # then wait client to send its UDP port number
                # send a close message to its UDP to close it
                # then close connection with client
                if current_time <= end_block_time[username]:
                    message = "ERROR$$In blocked duration"
                    self.clientSocket.send(message.encode())
                    data = self.clientSocket.recv(1024)
                    message = data.decode()
                    dataType, message = message.split("$$")
                    UDPport = int(message)
                    command = "OUT"
                    UDPclientSocket = socket(AF_INET, SOCK_DGRAM)
                    client_IP = list(self.clientAddress)[0]
                    UDPserverAddress = (client_IP, UDPport)
                    UDPclientSocket.sendto(command.encode(), UDPserverAddress)
                    UDPclientSocket.close()
                    break
                # if not blocked now
                # remove username from blocked list
                if current_time > end_block_time[username]:
                    blocked_user.remove(username)
            print(f'> Receive: username is {username} password is {password}')
            # check whether credential is right
            # give response in 3 different conditions:
            # invalid username, invalid password and both right
            # each time, the password is wrong, will increase trying by 1
            with open("credentials.txt") as file:
                message = "ERROR$$Invalid username"
                for line in file:
                    u,p = line.strip().split(" ")
                    if username == u and password == p:
                        message = "SUCCESS$$welcome"
                        self.loginState = True
                        self.login_time = current_time
                        self.username = username
                    elif username == u and password != p:
                        message = "ERROR$$Invalid password"
                        trying += 1
            # when trying reaches 3, the username will be blocked
            if trying == 3:
                message = "ERROR$$blocked"
                self.clientSocket.send(message.encode())
                # add blocke duration to the time receive this credential
                # and save it with its username to a dictionary
                blocked_duration = 10
                blocked_time = current_time + datetime.timedelta(seconds=blocked_duration)
                blocked_user.append(username)
                end_block_time[username] = blocked_time
                # close the client's UDP
                # then disconnect with client side
                data = self.clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                UDPport = int(message)
                command = "OUT"
                UDPclientSocket = socket(AF_INET, SOCK_DGRAM)
                client_IP = list(self.clientAddress)[0]
                UDPserverAddress = (client_IP, UDPport)
                UDPclientSocket.sendto(command.encode(), UDPserverAddress)
                UDPclientSocket.close()
                break
            # message here, is the message before 'if trying == 3'
            self.clientSocket.send(message.encode())
            
            # if credential is right, server gave response before
            # and receive UDP port number from client side
            # then upload informations
            if message == "SUCCESS$$welcome":
                data = self.clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                self.UDPport = int(message)
                self.login_process()
            
        # when log in    
        while self.loginState:
            data = self.clientSocket.recv(1024)
            # after receive a command, first check whether server
            # is processing with other client
            while in_use:
                time.sleep(1)
            
            message = data.decode()
            command_list = message.split(" ")
            command = command_list[0]
            
            # with any command, first set in_use to True and set in_use to False at end
            
            # with OUT command
            # send message to client to close its UDP and TCP
            # print who exit
            if command == "OUT":
                in_use = True
                message = "OUT$$go"
                self.clientSocket.send(message.encode())
                self.logout_process()
                UDPclientSocket = socket(AF_INET, SOCK_DGRAM)
                client_IP = list(self.clientAddress)[0]
                UDPserverAddress = (client_IP, self.UDPport)
                UDPclientSocket.sendto(command.encode(), UDPserverAddress)
                UDPclientSocket.close()
                print(f"> {username} exited the edge network")
                self.loginState = False
                in_use = False
            
            # with EDG command
            # client tell server it is about to generate a file with a size
            # server print this process
            elif command == "EDG":
                in_use = True
                file_ID = command_list[1]
                data_size = command_list[2]
                print(f"> The edge device is generating {data_size} data samples...")
                message = "EDG$$start"
                self.clientSocket.send(message.encode())
                data = self.clientSocket.recv(1024)
                message = data.decode()
                dataType, message = message.split("$$")
                if message == "Done":
                    sample_name = username+"-"+file_ID+".txt"
                    print(f"> Data generation done, {data_size} data samples have been generatedand stored in the file {sample_name}")
                in_use = False
            
            # with UED command
            # receive data from receiver and write in file
            elif command == "UED":
                in_use = True
                file_ID = command_list[1]
                print(f"> Edge device {username} issued UED command")
                message = "UED$$receive command"
                self.clientSocket.send(message.encode())
                # receive data from client via packets
                data = self.clientSocket.recv(1024)
                receive_num = 1
                sample_name = username+"-"+file_ID+".txt"
                f = open(sample_name, "wb")
                try:
                    while data:
                        print(f">>> receiving {receive_num}...")
                        receive_num += 1
                        f.write(data)
                        # set timeout to avoid unexpected error
                        self.clientSocket.settimeout(1)
                        data = self.clientSocket.recv(1024)
                except timeout:
                    f.close()
                    # set timeout to NONE
                    self.clientSocket.settimeout(None)
                f = open(sample_name, "r")
                # record received data size
                d = f.readlines()
                f.close()
                data_size = len(d)
                # record the end of received time
                current_time = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
                print(f"> A data file is received from edge device {username}")
                # update upload log file
                log_f = open("upload_log.txt", "a")
                log_info = username+"; "+current_time+"; "+file_ID+"; "+str(data_size)+"\n"
                log_f.write(log_info)
                log_f.close
                print(f"> Return message:\nThe file with ID of {file_ID} has been received, upload-log.txt file has been updated")
                message = "UED$$Done"
                self.clientSocket.send(message.encode())
                in_use = False
            
            # with SCS command
            # client ask server to computate with one uploaded file by the client
            # with operation SUM, MAX, MIN, AVERAGE
            elif command == "SCS":
                in_use = True
                fileID = command_list[1]
                operation = command_list[2]
                print(f"> Edge device {username} requested a computation operation on the file with ID of {fileID}")
                filename = username+"-"+fileID+".txt"
                if not os.path.exists(filename):
                    print(f"> The requested {filename} to be computated does not exist\nReture message: NO such file")
                    message = "SCS$$no such file"
                    self.clientSocket.send(message.encode())
                else:
                    # excute operation
                    with open(filename,"r") as f:
                        d = f.readlines()
                        if operation == "SUM":
                            res = sum([int(x) for x in d])
                        if operation == "MAX":
                            res = max([int(x) for x in d])
                        if operation == "MIN":
                            res = min([int(x) for x in d])
                        if operation == "AVERAGE":
                            res = sum([int(x) for x in d])/len(d)
                    print(f"> Return message:\n{operation} computation has been made on edge device {username} data file (ID: {fileID}), the result is {res}")
                    # send the result to client side
                    message = "SCS$$"+str(res)
                    self.clientSocket.send(message.encode())
                in_use = False
            
            # with DTE command
            # server delete the file with fileID uploaded and given by client
            # then update deletion log file
            elif command == "DTE":
                in_use = True
                fileID = command_list[1]
                print(f"> Edge device {username} issued DTE command, the fileID is {fileID}")
                filename = username+"-"+fileID+".txt"
                if not os.path.exists(filename):
                    print(f"> The requested {filename} to be deleted does not exist\nReture message: NO such file")
                    message = "DTE$$no such file"
                    self.clientSocket.send(message.encode())
                else:
                    f = open(filename, "r")
                    d = f.readlines()
                    f.close()
                    data_size = len(d)
                    os.remove(filename)
                    if not os.path.exists(filename):
                        # record time of deletion
                        current_time = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
                        log_f = open("deletion_log.txt", "a")
                        log_info = username+"; "+current_time+"; "+fileID+"; "+str(data_size)+"\n"
                        log_f.write(log_info)
                        log_f.close
                        print(f"> Return message:\nThe file with ID of {fileID} from edge device {username} has been deleted, deletion log file has been updated")
                        message = "DTE$$Done"
                        self.clientSocket.send(message.encode())
                in_use = False
            
            # with AED command
            # server tell client all active edge device
            # except for client itself
            elif command == "AED":
                in_use = True
                print(f"> The edge device {username} issued AED command")
                message = ""
                # check if there is other active edge device
                with open("edge-device-log.txt", "r") as f:
                    d = f.readlines()
                    for line in d:
                        data_list = line.strip("\n").split("; ")
                        if username == data_list[2]:
                            continue
                        else:
                            other_logintime = data_list[1]
                            other_username = data_list[2]
                            other_IP = data_list[3]
                            other_UDPserverPort = data_list[4]
                            new = other_username+";"+other_IP+";"+other_UDPserverPort+";active since "+other_logintime+"\n"
                            message = message + new
                if message == "":
                    print("> No other active edge device\nReturn message: no other active device")
                    message = "AED$$no other active device"
                    self.clientSocket.send(message.encode())
                else:
                    message = message[:-1]
                    show = "> Return other active edge device list:\n"+message
                    message = "AED$$"+message[:-1]
                    print(show)
                    self.clientSocket.send(message.encode())
                in_use = False
            
            # with UVF command
            # server will tell client
            # the destination device exists or not
            # and whether it is active
            elif command == "UVF":
                in_use = True
                aud_username = command_list[1]
                filename = command_list[2]
                valid_username = False
                with open("credentials.txt") as file:
                    for line in file:
                        u,p = line.strip().split(" ")
                        if aud_username == u and username != u:
                            valid_username = True
                if not valid_username:
                    message = "UVF$$Invalid audience"
                    self.clientSocket.send(message.encode())
                else:
                    message = "UVF$$not active"
                    with open("edge-device-log.txt", "r") as f:
                        d = f.readlines()
                        for line in d:
                            data_list = line.strip("\n").split("; ")
                            if aud_username == data_list[2]:
                                message = "UVF$$"+data_list[3]+";"+data_list[4]
                    self.clientSocket.send(message.encode())
                    data = self.clientSocket.recv(1024)
                    message = data.decode()
                    dataType, message = message.split("$$")
                in_use = False
    
    # log-in process
    # append log-in information to log file
    # give correct log-in ID 
    def login_process(self):
        current_time = self.login_time.strftime("%d %B %Y %H:%M:%S")
        f = open("edge-device-log.txt", "a")
        f.close()
        with open("edge-device-log.txt", "r") as f:
            d = f.readlines()
            if d == []:
                index = 1
            else:
                index = int(d[-1].strip("\n").split("; ")[0]) + 1
        IP = list(self.clientAddress)[0]
        new = str(index)+"; "+current_time+"; "+self.username+"; "+IP+"; "+str(self.UDPport)+"\n"
        f = open("edge-device-log.txt", "a")
        f.write(f"{new}")
        f.close()
    
    # log-out process
    # delete log-out device and correct other log-in ID
    def logout_process(self):
        with open("edge-device-log.txt", "r+") as f:
            d = f.readlines()
            number = int(d[-1].strip("\n").split("; ")[0])
            f.seek(0)
            for i in d:
                list_i = i.strip("\n").split("; ")
                if self.username in list_i:
                    number = int(list_i[0])
                if self.username not in list_i:
                    new = i
                    if int(list_i[0]) > number:
                        list_i[0] = str(int(list_i[0]) - 1)
                        new = "; ".join(list_i)
                        new = new + "\n"
                    f.write(new)
            f.truncate()                
    
    
        
        
        
        

print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()

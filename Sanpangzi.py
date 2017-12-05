# -- coding:UTF-8 --
#!/usr/bin/python
import sys
import getopt
import socket
import threading
import subprocess
import hashlib
import time
import os
'''
该工具有如下功能：
1、建立交互shell
2、上传文件
3、远程执行命令
'''
def usage():
    print "Sanpangzi Net Tool"
    print
    print "服务端使用："
    print "sangpangzi.py -t 192.168.0.1 -p 5555 -l"
    print "客户端使用："
    print "1、建立交互shell：sanpangzi.py -t 192.168.0.1 -p 5555 -c"
    print "2、上传文件：sanpangzi.py -t 192.168.0.1 -p 5555 -u C:\\test.exe -d /www/"
    print "3、远程执行命令：sanpangzi.py -t 192.168.0.1 -p 5555 -l -e \"cat /etc/passwd\""
    sys.exit(0)

def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

def valid_port(port):
    print port
    if port.isdigit() and int(port) <= 65535 and int(port) > 0:
        return True
    else:
        return False

'''参数列表'''
listen = False
port = 0
execute = ""
command = False
upload = False
upload_file = ""
upload_position = ""
target = ""
exe_cmd = ""

'''检查参数'''
def check_args():
    global listen
    global port
    global execute
    global command
    global upload_file
    global upload_position
    global target
    global exe_cmd
    if not len(sys.argv[1:]):
        usage()
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:d:",["help","listen","execute","target","port","command","upload","destination"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execte"):
            execute = True
            exe_cmd = a
        elif o in ("-c","--commandshell"):
            command = True
        elif o in ("-u","--upload"):
            upload_file = a
            #print upload_file
        elif upload_file and o in("-d","--destination"):
            upload_position = a
            #print upload_position
        elif o in ("-t","--target"):
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False,"Unhandled Option"

'''客户端建立shell'''
def client_get_shell():
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    global target
    global port
    try:
        client.connect((target,int(port)))
        # 发送建立shell的命令码
        shell_command = hashlib.md5()
        shell_command.update("0001sanpangzi")
        #print shell_command.hexdigest()
        client.send(shell_command.hexdigest())
        while True:
            recv_len = 1
            response = ""
            buffer = raw_input("<BHP:#>")
            # exit命令则退出shell
            if buffer == "exit":
                print "Good bye!!"
                client.close()
                break
            buffer += "\n"
            client.send(buffer)
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data
                if recv_len < 4096:
                    break
            print response
    except Exception as error:
        print "Shell has disconnected!!"
        print error
        client.close()

'''服务端获得交互shell'''
def server_get_shell(client_socket):
    while True:
        cmd_buffer = ""
        while "\n" not in cmd_buffer:
            cmd_buffer += client_socket.recv(1024)
            response = run_command(cmd_buffer)
            client_socket.send(response)

'''客户端上传文件'''
def client_upload_file(filename,destination):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    global target
    global port
    try:
        client.connect((target,int(port)))
        # 发送上传文件的命令码及文件名称
        upload_command = hashlib.md5()
        upload_command.update("0010sanpangzi")
        client.send(upload_command.hexdigest())
        time.sleep(1)
        # 发送文件名称
        client.send(filename)
        # 发送文件存放位置
        client.send(destination)
        time.sleep(1)
        # 发送文件大小
        try:
            file_size = str(os.path.getsize(filename))
            #print file_size
        except Exception as error:
            print "Could not open file!!"
            client.close()
            sys.exit()
        if file_size == "0":
            print "File is empty, please try again"
            client.close()
            sys.exit()
        else:
            client.send(file_size)
            # 传送文件
            with open(filename,"rb") as f:
                for data in f:
                    client.send(data)
            response = client.recv(1024)
            print response
            client.close()
    except Exception as error:
        print "Upload failed!!"
        print error
        client.close()

'''服务端接收文件上传'''
def server_upload_file(client_socket):
    # 接受文件名
    filename = client_socket.recv(1024)
    # 这里由于windows使用\,linux使用/，因此需要做区分
    final_filename = ""
    # windows
    if "\\" in filename:
        final_filename = filename.split("\\")[-1]
    # linux
    if "/" in filename:
        final_filename = filename.split("/")[-1]
    print final_filename
    # 接受文件存放位置
    file_destination = client_socket.recv(1024)
    # 接受文件大小
    file_size = client_socket.recv(1024)
    print file_size
    # 上传成功与失败的标志位，True表示上传成功，False表示上传失败
    is_succeed = True
    # 验证文件位置是否存在
    if not os.path.exists(file_destination) and file_size > 0:
        client_socket.send("File upload failed:File destination is not exist!")
        is_succeed = False
    else:
        file_buffer = ""
        file_count = 0
        while True:
            data = client_socket.recv(1024)
            file_count += len(data)
            file_buffer += data
            try:
                with open(file_destination+final_filename,"ab") as f:
                    f.write(file_buffer)
            except IOError as error:
                client_socket.send("File upload failed:Permission denied!")
                is_succeed = False
                break
            if str(file_count) == str(file_size):
                print "over"
                break
    if is_succeed:
        print "succeed!!"
        client_socket.send("File upload succeed!")
    else:
        print "failed!!"
'''客户端远程命令执行'''
def client_command_execute(cmd):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    global target
    global port
    try:
        client.connect((target,int(port)))
        # 发送远程执行命令的命令码，及需要执行的命令
        execute_command = hashlib.md5()
        execute_command.update("0011sanpangzi")
        client.send(execute_command.hexdigest())
        client.send(cmd)
        # 接收回显的总长度
        back_size = client.recv(1024)
        back_count = 0
        while True:
            data = client.recv(1024)
            back_count += len(data)
            print data
            if str(back_count) == str(back_size):
                break
    except Exception as e:
        print e
        sys.exit()
    client.close()
    sys.exit()

'''服务端接受远程命令执行'''
def server_command_execute(client_socket):
    command = client_socket.recv(1024)
    #print command
    output = run_command(command)
    # 发送回显的总长度
    client_socket.send(str(len(output)))
    client_socket.send(output)
    
'''服务端，监听端口的函数，负责执行命令，并将执行结果回显给客户端'''
def server_loop():
    global target
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        server.bind((target,port))
    except Exception as e:
        print e
        sys.exit()
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        print addr
        client_thread = threading.Thread(target=server_handler,args=(client_socket,))
        client_thread.start()

'''服务端调用执行命令的函数'''
def run_command(command):
    command = command.rstrip()
    print command
    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)
    except:
        output = "Failed to execute command."
    return output


'''服务端函数,具有远程执行命令，远程上传文件，建立shell连接等功能'''
def server_handler(client_socket):
    command_code = client_socket.recv(1024)[:32]
    # 交互shell命令码
    valid_code_shell = hashlib.md5()
    valid_code_shell.update("0001sanpangzi")
    # 远程上传文件命令码
    valid_code_upload = hashlib.md5()
    valid_code_upload.update("0010sanpangzi")
    # 远程执行命令
    valid_code_execute = hashlib.md5()
    valid_code_execute.update("0011sanpangzi")
    #print command_code
    #print valid_code_upload.hexdigest()
    if command_code == valid_code_shell.hexdigest():
        server_get_shell(client_socket)
    if command_code == valid_code_upload.hexdigest():
        server_upload_file(client_socket)
    if command_code == valid_code_execute.hexdigest():
        server_command_execute(client_socket)
    else:
        print command_code
        print valid_code_execute.hexdigest()
        print valid_code_shell.hexdigest()
        print valid_code_upload.hexdigest()
        print "error code!!"
        
if __name__ == '__main__':
    check_args()
    # 客户端建立shell连接
    if not listen and len(target) and port > 0 and command:
        client_get_shell()
    # 客户端远程上传文件
    if not listen and len(target) and port > 0 and upload_file and upload_position:
        client_upload_file(upload_file,upload_position)
    # 客户端远程执行命令
    if not listen and len(target) and port > 0 and execute and exe_cmd:
        client_command_execute(exe_cmd) 
    # 作为服务端工具使用
    if listen:
        server_loop()
        
    
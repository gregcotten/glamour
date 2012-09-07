import paramiko

host = "gregcotten.com"                    #hard-coded
port = 22
transport = paramiko.Transport((host, port))

transport.connect(username = "gregcott", password = "fakepass")

ftp = paramiko.SFTPClient.from_transport(transport)
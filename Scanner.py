import threading

from config import host, port, timeout_accept, timeout_read

import math
import socket

import multiprocessing

class Scanner:
    def __init__(self):
        self.lidars = []

        self.s = None
        #self.connection = multiprocessing.Process(target=self.connect)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(timeout_accept)
        self.s.bind((host, port))
        self.s.listen(5)
        pass

    def check(self):
        self.lidars.clear()
        (clientsock, (ip, port)) = self.s.accept()
        # self.lidars.append(clientsock)

    def scan(self):
        self.lidars.clear()
        (clientsock, (ip, port)) = self.s.accept()
        self.lidars.append(clientsock)

        new_thread = ClientThread(ip, port, clientsock, self.lidars)
        new_thread.start()

class LidarServer:
    def __init__(self):
        self.points = []
        self.status = "ready"
        self.msgS = "rd" # every command contain 2 char - TYPE + may contain 6 char of data
                                                                # (probably increase to 8 char)
        self.only_reading = False

        self.x_max = 128
        self.y_max = 64
        self.x_val = 0
        self.y_val = 0

    def write_file(self):
        f = open('data.obj', 'w+')
        for i in self.points:
            f.write('v ' + i.toStringXYZ() + '\n')
        for i in range(0, self.y_max - 1):
            for j in range(self.x_max - 1):
                f.write(
                    f'f {i * self.x_max + 1 + j} {i * self.x_max + 2 + j} {(i + 1) * self.x_max + 2 + j} {(i + 1) * self.x_max + 1 + j}\n')
        f.close()

    def is_only_reading(self):
        return self.only_reading

    def request(self):
        return self.msgS

    def response(self, msg):
        if self.status == "ready":
            if msg == "ok":
                print('ghj')
                self.status = "scan"
                self.msgS = "st" + str(self.x_max).rjust(3, '0') + str(self.y_max).rjust(3,
                                                                                         '0')  # only 2 digit in number
            return

        elif self.status == "scan":
            self.only_reading = True
            if msg == "dn":
                self.status = "exit"
                self.msgS = "ex"
                self.only_reading = False

                print("scanning is done\n")
                self.write_file()
                # self.show()
                # for i in self.points:
                #     print(i.toStringXYZ())
                return

            r = int(msg)
            point = Point(r, self.x_max, self.y_max, self.x_val, self.y_val)
            self.points.append(point)

            self.x_val += 1
            if self.x_val == self.x_max:
                print("new line" + '\n')
                self.y_val += 1
                self.x_val = 0

            if self.y_val == self.y_max:
                print("exit" + '\n')
                self.x_val = 0
                self.y_val = 0

        elif self.status == "exit":
            # self.write_file()
            print("scanning is done\n")


class ClientThread(threading.Thread):
    msg: str

    def __init__(self, ip, port, socket, l):
        threading.Thread.__init__(self)

        self.ip = ip
        self.port = port
        self.socket = socket
        self.msg_size = 5625  # start value
        self.msg = ""
        self.clients = l

        self.msg_head_size = 5

        self.lidar_server = LidarServer()

        print("[+] New thread started for " + ip + ":" + str(port))

    def update_msg(self, msg):
        self.msg = msg.encode()
        self.msg_size = len(msg)

    def recv_timeout(self, msg_size):
        self.socket.settimeout(timeout_read)
        data = self.socket.recv(msg_size)
        return data

    def read(self, msg_size):
        data = ""
        buf_size = 0
        while buf_size < msg_size:
            buf = self.recv_timeout(msg_size - buf_size)
            if buf == b'':
                raise ConnectionError
            data += buf
            buf_size += len(buf)
        return data.decode()

    def run(self):
        try:
            while True:
                self.msg = self.lidar_server.request()

                for c in self.clients:
                    if int(c.fileno()) == int(self.socket.fileno()):
                        c.send(str(len(self.msg)).rjust(5, '0').encode())
                        c.send(self.msg.encode())
                    continue

                self.msg_size = int(self.read(self.msg_head_size))
                print("length msg:", self.msg_size)
                self.msg = self.read(self.msg_size)
                print("msg(s): ", self.msg)

                self.lidar_server.response(self.msg)

                # self.msg = input("enter msg: ")
        except Exception as ex:
            print(ex)
            self.socket.close()
            self.clients.remove(self.socket)
            print("connection closed")



class Point:
    def __init__(self, r, x_max, y_max, x_val, y_val):
        self.x: float
        self.y: float
        self.z: float

        self.x = r * math.sin(math.radians(180 - (180 / y_max) * y_val)) * math.cos(math.radians((360 / x_max) * x_val))
        self.y = r * math.sin(math.radians(180 - (180 / y_max) * y_val)) * math.sin(math.radians((360 / x_max) * x_val))
        self.z = r * math.cos(math.radians(180 - (180 / y_max) * y_val))

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_z(self):
        return self.z

    def toStringXYZ(self):
        return f'{self.x} {self.y} {self.z}'



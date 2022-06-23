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
        self.lidars.append(clientsock)

        new_thread = ClientThread(ip, port, clientsock, self.lidars, mode="test")
        new_thread.start()

    def scan(self):
        self.lidars.clear()
        (clientsock, (ip, port)) = self.s.accept()
        self.lidars.append(clientsock)

        new_thread = ClientThread(ip, port, clientsock, self.lidars, mode="scan")
        new_thread.start()

class LidarServer:
    def __init__(self, mode="scan"):
        self.recieve = True

        self.points = []
        self.status = "ready" # start value

        self.msgS = "" # every command contain 2 char - TYPE + may contain 6 char of data
                                                                 # (probably increase to 8 char)
        if mode == "scan": self.msgS = "rd"
        if mode == "test": self.msgS = "ex"

        self.x_max = 128*2
        self.y_max = 64*2
        self.x_iter = 0
        self.y_iter = 0

    def is_recieve(self):
        return self.recieve

    def write_raw_file(self):
        f = open('data_raw.txt', 'w+')
        for i in self.points:
            f.write(i)
        f.close()

    def write_file(self):
        f = open('data.obj', 'w+')
        for i in self.points:
            f.write('v ' + i.toStringXYZ() + '\n')
        for i in range(0, self.y_max - 1):
            for j in range(self.x_max - 1):
                f.write(
                    f'f {i * self.x_max + 1 + j} {i * self.x_max + 2 + j} {(i + 1) * self.x_max + 2 + j} {(i + 1) * self.x_max + 1 + j}\n')
        f.close()

    def request(self):
        return self.msgS

    def response(self, msg):
        if self.status == "ready":
            if msg[0:2] == "ok":
                print('device is ready')
                self.status = "scan"
                self.msgS = "sc" + str(self.x_max).rjust(4, '0') + str(self.y_max).rjust(4, '0')
                                                                        # only 2 digit in number
            return

        elif self.status == "scan":
            if msg[0:2] == "dn":
                self.recieve = True
                self.status = "exit"
                self.msgS = "ex"

                print("scanning is done\n")
                self.write_raw_file()
                self.write_file()

                raise ConnectionError # exit due to finish

                # self.show()
                # for i in self.points:
                #     print(i.toStringXYZ())
                return

            if msg[0:2] == "pt":
                self.recieve = False
                # self.msgS = "pg"
                r = int(msg[2:])
                point = Point(r, self.x_max, self.y_max, self.x_iter, self.y_iter)
                self.points.append(point)

                self.x_iter += 1
                if self.x_iter == self.x_max:
                    print("new line" + '\n')
                    self.y_iter += 1
                    self.x_iter = 0

                if self.y_iter == self.y_max:
                    print("exit" + '\n')
                    self.x_iter = 0
                    self.y_iter = 0


        elif self.status == "exit":
            # self.write_file()
            print("scanning is done\n")


class ClientThread(threading.Thread):
    # msg: str

    def __init__(self, ip, port, socket, l, mode="scan"):
        threading.Thread.__init__(self)

        self.socket = socket
        self.clients = l

        self.recieve_mode = True

        self.msg_head_size = 5

        self.lidar_server = LidarServer(mode=mode)
        print("[+] New thread started for " + ip + ":" + str(port))

    def send(self, msg):
        self.socket.send(msg.encode())

    def do_send(self, message_send: str):
        print(f"to module len msg_size: {len(message_send)}")
        self.send(str(len(message_send)).rjust(self.msg_head_size, '0'))  # ?
        print(f"to module msg_size: {message_send}")
        self.send(str(message_send))

    def recv_timeout(self, msg_size) -> bytes:
        self.socket.settimeout(timeout_read)
        data = self.socket.recv(msg_size)
        return data

    def read(self, msg_size):
        data = b''
        buf_size = 0
        while buf_size < msg_size:
            buf = self.recv_timeout(msg_size - buf_size)
            if buf == b'':
                raise ConnectionError
            data += buf
            buf_size += len(buf)
        return data.decode()

    def do_read(self) -> str:
        msg_size = self.read(self.msg_head_size)
        print(f"from module msg_size: {msg_size}")
        msg = self.read(int(msg_size))
        print(f"from module msg: {msg}")
        return msg

    def close(self):
        self.socket.close()

    def run(self):
        try:
            while True:
                msg = self.lidar_server.request()
                # for c in self.clients:
                #     if int(c.fileno()) == int(self.socket.fileno()):
                #         c.send(str(len(self.msg)).rjust(5, '0').encode())
                #         c.send(self.msg.encode())
                #     continue
                if self.lidar_server.is_recieve():
                    self.do_send(msg)

                msg = self.do_read()

                self.lidar_server.response(msg)

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



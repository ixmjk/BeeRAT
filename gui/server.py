import time
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtTest
from PyQt5.QtCore import QThread
from PyQt5 import QtCore
import socket
import json
import os
import sys
import base64
import hashlib
import datetime
import subprocess
import threading
import getpass


FORMAT = 'utf-8'


class Server(qtw.QWidget, QtCore.QThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_file = 'server.ui'
        self.ui = loadUi(self.ui_file, self)
        self.ui.pb1.clicked.connect(self.start_thread)
        self.ui.pb3.clicked.connect(self.change_password)

    def change_password(self):
        password, done = qtw.QInputDialog.getText(self, 'Password', 'Enter your password:', qtw.QLineEdit.Password)
        if done:
            if len(password) >= 8:
                self.set_password(password)
                qtw.QMessageBox.information(self, 'Password', 'Password saved successfully.')
            else:
                qtw.QMessageBox.warning(self, 'Password', 'Password must be at least 8 characters long.')

    def closeEvent(self, event) -> None:
        os._exit(0)

    def clear(self):
        self.ui.tb.clear()

    def print(self, text):
        self.ui.tb.append(text)

    @staticmethod
    def log(log_message):
        with open('BeeRAT-log.txt', 'a') as file:
            file.write(log_message + '\n')
        return log_message

    @staticmethod
    def get_time():
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_password():
        with open('BeeRAT-password.txt', 'r') as file:
            return file.read().strip()

    def send(self, data):
        json_data = json.dumps(data)
        self.connection.send(json_data.encode(FORMAT))

    def recv(self):
        json_data = ''
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def pwd(self):
        return os.getcwd()

    def cd(self, path):
        try:
            os.chdir(path)
            return ''
        except FileNotFoundError:
            return f'cd: {path}: No such file or directory'

    def ls(self):
        return '  '.join(os.listdir())

    def read_file(self, path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode(FORMAT)

    def downloadable(self, file_path):
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(os.path.dirname(__file__), file_path)):
            return True
        return False

    def rename_file(self, file_name):
        filename, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(file_name):
            file_name = f'{filename} ({counter}){extension}'
            counter += 1
        return file_name

    def write_file(self, filename, content):
        filename = self.rename_file(filename)
        with open(filename, 'wb') as file:
            file.write(base64.b64decode(content))
            return f'[+] {filename} uploaded successfully.'

    @staticmethod
    def set_password(password):
        hash_object = hashlib.sha256(password.encode())
        password_hash = hash_object.hexdigest()
        with open('BeeRAT-password.txt', 'w') as file:
            file.write(password_hash)

    @staticmethod
    def get_password():
        with open('BeeRAT-password.txt', 'r') as file:
            return file.read().strip()

    @staticmethod
    def execute_system_command(command):
        result = subprocess.getoutput(command)
        return result

    def start_thread(self):
        self.print(self.log(f'[{Server.get_time()}] server started.'))
        self.ui.pb1.setEnabled(False)
        self.ui.pb3.setEnabled(False)
        background_thread = threading.Thread(target=self.start)
        background_thread.start()

    def start(self):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = 55555
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.ip, self.port))
        server.listen(0)
        self.print(self.log(f'[+] [{self.get_time()}] [{self.ip}] listening...'))
        self.connection, self.address = server.accept()
        self.print(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] is authenticating.'))
        password = self.recv()
        if password is None:
            self.start()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == Server.get_password():
            self.send(True)
            self.print(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] connected.'))
        else:
            self.print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] authentication failed.'))
            self.send(False)
            self.start()
        while True:
            try:
                command = self.recv().split(' ')
                self.print(self.log(f"[-] [{self.get_time()}] [{self.address[0]}] command: {' '.join(command)}"))
                if command[0] == 'exit':
                    self.print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
                    self.start()
                elif command[0] == 'prompt' and len(command) == 1:
                    self.send(f'{getpass.getuser()}@{socket.gethostname()}:{os.getcwd()}')
                elif command[0] == 'pwd' and len(command) == 1:
                    self.send(self.pwd())
                elif command[0] == 'cd' and len(command) > 1:
                    self.send(self.cd(' '.join(command[1:])))
                elif command[0] == 'ls' and len(command) == 1:
                    self.send(self.ls())
                elif command[0] == 'download' and len(command) > 1:
                    file_path = ' '.join(command[1:])
                    file_content = self.read_file(file_path)
                    self.send(file_content)
                elif command[0] == 'downloadable' and len(command) > 1:
                    file_path = ' '.join(command[1:])
                    self.send(self.downloadable(file_path))
                elif command[0] == 'upload' and len(command) > 1:
                    file_name = ' '.join(command[1:])
                    file_content = self.recv().encode(FORMAT)
                    self.send(self.write_file(file_name, file_content))
                elif command[0] == 'change-password':
                    password = ' '.join(command[1:])
                    self.set_password(password)
                    self.send(True)
                else:
                    command = ' '.join(command)
                    command_result = self.execute_system_command(command)
                    self.send(command_result)
            except ConnectionResetError:
                self.print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
                self.start()
            except Exception as e:
                self.send(str(e))


def main():
    app = qtw.QApplication([])
    widget = Server()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

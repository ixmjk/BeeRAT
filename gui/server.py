import base64
import datetime
import getpass
import hashlib
import json
import os
import socket
import subprocess

from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.uic import loadUi


FORMAT = 'utf-8'


class RestartServer(Exception):
    pass


class Server(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_file = 'server.ui'
        self.ui = loadUi(os.path.join(os.path.dirname(__file__), self.ui_file), self)
        self.ui.pb1.clicked.connect(self.start_thread)
        self.ui.pb3.clicked.connect(self.change_password)

    def closeEvent(self, event) -> None:
        os._exit(0)

    def change_password(self):
        password, done = qtw.QInputDialog.getText(self, 'Password', 'Enter your password:', qtw.QLineEdit.Password)
        if done:
            if len(password) >= 8:
                WorkerThread.set_password(password)
                qtw.QMessageBox.information(self, 'Password', 'Password saved successfully.')
            else:
                qtw.QMessageBox.warning(self, 'Password', 'Password must be at least 8 characters long.')

    def clear(self):
        self.ui.tb.clear()

    def print(self, text):
        self.ui.tb.append(text)

    def start_thread(self):
        self.ui.pb1.setEnabled(False)
        self.ui.pb3.setEnabled(False)
        self.print(WorkerThread.log(f'[{WorkerThread.get_time()}] server started.'))
        self.worker = WorkerThread()
        self.worker.start()
        self.worker.log_message.connect(self.print)


class WorkerThread(QThread):

    log_message = pyqtSignal(str)

    def listen(self):
        ip = socket.gethostbyname(socket.gethostname())
        port = 55555
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip, port))
        server.listen(0)
        self.log_message.emit(self.log(f'[+] [{self.get_time()}] [{ip}] listening...'))
        connection, address = server.accept()
        return connection, address

    def run(self) -> None:
        try:
            self.connection, self.address = self.listen()
            self.log_message.emit(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] is authenticating.'))
            password = self.recv()
            if password is None:
                raise RestartServer
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == WorkerThread.get_password():
                self.send(True)
                self.log_message.emit(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] connected.'))
            else:
                self.log_message.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] authentication failed.'))
                self.send(False)
                raise RestartServer
            while True:
                command = self.recv().split(' ')
                self.log_message.emit(
                    self.log(f"[-] [{self.get_time()}] [{self.address[0]}] command: {' '.join(command)}"))
                if command[0] == 'exit':
                    self.log_message.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
                    raise RestartServer
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
            self.log_message.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
            raise RestartServer
        except RestartServer:
            self.run()
        except Exception as e:
            self.send(str(e))

    @ staticmethod
    def log(log_message):
        with open('BeeRAT-log.txt', 'a') as file:
            file.write(log_message + '\n')
        return log_message

    @ staticmethod
    def get_time():
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @ staticmethod
    def get_password():
        with open(os.path.join(os.path.dirname(__file__), 'BeeRAT-password.txt'), 'r') as file:
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

    @ staticmethod
    def set_password(password):
        hash_object = hashlib.sha256(password.encode())
        password_hash = hash_object.hexdigest()
        with open(os.path.join(os.path.dirname(__file__), 'BeeRAT-password.txt'), 'w') as file:
            file.write(password_hash)

    @ staticmethod
    def get_password():
        with open(os.path.join(os.path.dirname(__file__), 'BeeRAT-password.txt'), 'r') as file:
            return file.read().strip()

    @ staticmethod
    def execute_system_command(command):
        result = subprocess.getoutput(command)
        return result


def main():
    if 'BeeRAT-password.txt' not in os.listdir(os.path.dirname(__file__)):
        WorkerThread.set_password('password')
    app = qtw.QApplication([])
    widget = Server()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

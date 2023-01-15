import base64
import datetime
import getpass
import hashlib
import json
import os
import pathlib
import socket
import subprocess
from typing import Any
from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.uic import loadUi


FORMAT = 'utf-8'


class RestartServer(Exception):
    pass


class Server(qtw.QWidget):
    """this class has all server gui related features
    """

    def __init__(self, *args, **kwargs) -> None:
        """the constructor for Server gui class
        """
        super().__init__(*args, **kwargs)
        self.ui_file = 'server.ui'
        self.ui = loadUi(os.path.join(os.path.dirname(__file__), self.ui_file), self)
        self.ui.pb1.clicked.connect(self.start_thread)
        self.ui.pb3.clicked.connect(self.change_password)

    def closeEvent(self, event) -> None:
        """custom window close method
        """
        os._exit(0)

    def start_thread(self) -> None:
        """start button click event
        """
        self.ui.pb1.setEnabled(False)
        self.ui.pb3.setEnabled(False)
        self.ui.tb.append(ServerThread().log(f'[{ServerThread().get_time()}] server started.'))
        self.server_thread = ServerThread()
        self.server_thread.start()
        self.server_thread.log_signal.connect(lambda text: self.ui.tb.append(text))

    def change_password(self) -> None:
        """change password button click event
        """
        self.ui.tb.append('BeeRAT-passwd: Change server password')
        d = InputDialog()
        if d.exec():
            new_password, renew_password = d.getInputs()
            if new_password and renew_password:
                if new_password == renew_password:
                    if len(new_password) >= 8:
                        ServerThread().set_password(new_password)
                        self.ui.tb.append('[+] Password saved successfully.')
                    else:
                        self.ui.tb.append('[-] Password must be at least 8 characters long.')
                else:
                    self.ui.tb.append('[-] Passwords dont match.')


class InputDialog(qtw.QDialog):
    """custom change password input dialog
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(350, 125)
        self.setWindowTitle('BeeRAT-passwd')

        self.first = qtw.QLineEdit(self)
        self.second = qtw.QLineEdit(self)
        self.first.setEchoMode(qtw.QLineEdit.Password)
        self.second.setEchoMode(qtw.QLineEdit.Password)
        buttonBox = qtw.QDialogButtonBox(qtw.QDialogButtonBox.Ok | qtw.QDialogButtonBox.Cancel, self)

        layout = qtw.QFormLayout(self)
        layout.addRow("New Password: ", self.first)
        layout.addRow("Retype new Password: ", self.second)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.text(), self.second.text()


class ServerThread(QThread):
    """this class is the start button click event thread
    """
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        """the constructor for ServerThread class
        """
        super(ServerThread, self).__init__(parent)
        self.script_location = pathlib.Path.home()  # save password and log file to user home directory
        self.password_file = os.path.join(self.script_location, 'BeeRAT-password.txt')
        self.log_file = os.path.join(self.script_location, 'BeeRAT-log.txt')

    def run(self) -> None:
        """this method executes when ServerThread object's start method is called
        """
        if 'BeeRAT-password.txt' not in os.listdir(self.script_location):
            self.set_password('password')
        try:
            self.connection, self.address = self.listen()
            self.connection.settimeout(300)
            self.log_signal.emit(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] is authenticating.'))
            password = self.recv()
            if password is None:
                raise RestartServer
            password_hash = self.hash_password(password)
            if password_hash == self.get_password():
                self.send(True)
                self.log_signal.emit(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] connected.'))
            else:
                self.log_signal.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] authentication failed.'))
                self.send(False)
                raise RestartServer
            while True:
                command = self.recv().split(' ')
                self.log_signal.emit(
                    self.log(f"[+] [{self.get_time()}] [{self.address[0]}] command: {' '.join(command)}"))
                if command[0] == 'exit':  # 10
                    self.log_signal.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
                    raise RestartServer
                elif command[0] == 'prompt' and len(command) == 1:  # 9
                    self.send(f'{getpass.getuser()}@{socket.gethostname()}:{os.getcwd()}')
                elif command[0] == 'pwd' and len(command) == 1:  # 8
                    self.send(self.pwd())
                elif command[0] == 'cd' and len(command) > 1:  # 7
                    self.send(self.cd(' '.join(command[1:])))
                elif command[0] == 'ls' and len(command) == 1:  # 6
                    self.send(self.ls())
                elif command[0] == 'download' and len(command) > 1:  # 5
                    file_path = ' '.join(command[1:])
                    file_content = self.read_file(file_path)
                    self.send(file_content)
                elif command[0] == 'downloadable' and len(command) > 1:  # 4
                    file_path = ' '.join(command[1:])
                    self.send(self.downloadable(file_path))
                elif command[0] == 'upload' and len(command) > 1:  # 3
                    file_name = ' '.join(command[1:])
                    file_content = self.recv()
                    self.send(self.write_file(file_name, file_content))
                elif command[0] == 'BeeRAT-passwd' and len(command) > 1:  # 2
                    password = ' '.join(command[1:])
                    if self.hash_password(password) == self.get_password():
                        self.send(True)
                        new_password = self.recv()
                        self.set_password(new_password)
                        self.send(True)
                    else:
                        self.send(False)
                else:  # 1
                    command = ' '.join(command)
                    command_result = self.execute_system_command(command)
                    self.send(command_result)
        except ConnectionResetError:
            self.log_signal.emit(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
            self.run()
        except RestartServer:
            self.run()
        except Exception as e:
            self.send(str(e))

    def listen(self) -> tuple[socket.socket, tuple[str, int]]:
        """listen for incoming connection

        Returns:
            tuple[socket.socket, tuple[str, int]]: connection, address
        """
        ip = socket.gethostbyname(socket.gethostname())
        port = 55555
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip, port))
        server.listen(0)
        self.log_signal.emit(self.log(f'[+] [{self.get_time()}] [{ip}] listening...'))
        connection, address = server.accept()
        return connection, address

    def send(self, data: Any) -> None:
        """custom socket send method

        Args:
            data (Any): data that you wish to send
        """
        json_data = json.dumps(data)
        self.connection.send(json_data.encode(FORMAT))

    def recv(self) -> Any:
        """custom socket recv method

        Returns:
            Any: data that you wish to receive
        """
        json_data = ''
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    @staticmethod
    def execute_system_command(command: str) -> str:
        """execute system command and return the result

        Args:
            command (str): command

        Returns:
            str: result of running the command
        """
        result = subprocess.getoutput(command)
        return result

    @staticmethod
    def pwd() -> str:
        """get the current working directory

        Returns:
            str: current working directory
        """
        return os.getcwd()

    @staticmethod
    def cd(path: str) -> str:
        """change the working directory

        Args:
            path (str): path or folder name

        Returns:
            str: result
        """
        try:
            os.chdir(path)
            return ''
        except FileNotFoundError:
            return f'cd: {path}: No such file or directory'

    @staticmethod
    def ls() -> str:
        """list files in current working directory

        Returns:
            str: file names
        """
        return '  '.join(os.listdir())

    @staticmethod
    def get_time() -> str:
        """get current date and time

        Returns:
            str: current date and time
        """
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def set_password(self, password: str) -> None:
        """set password for the app (save password hash to BeeRAT-password.txt)

        Args:
            password (str): your password
        """
        password_hash = self.hash_password(password)
        with open(self.password_file, 'w') as file:
            file.write(password_hash)

    def get_password(self) -> str:
        """read password hash from file (BeeRAT-password.txt)

        Returns:
            str: password hash (content of BeeRAT-password.txt)
        """
        with open(self.password_file, 'r') as file:
            return file.read().strip()

    @staticmethod
    def hash_password(password: str) -> None:
        """get the sha256 hash of given password

        Args:
            password (str): normal password

        Returns:
            _type_: hashed password
        """
        hash_object = hashlib.sha256(password.encode())
        password_hash = hash_object.hexdigest()
        return password_hash

    def log(self, log_message: str) -> str:
        """log the given message (append to BeeRAT-log.txt)

        Args:
            log_message (str): the log message

        Returns:
            str: the log message (no change)
        """
        with open(self.log_file, 'a') as file:
            file.write(log_message + '\n')
        return log_message

    @staticmethod
    def read_file(path: str) -> str:
        """read (i.e. upload) file

        Args:
            path (str): path to the file

        Returns:
            str: content of the file
        """
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode(FORMAT)

    def write_file(self, filename: str, content: str) -> str:
        """write (i.e. save, download) file

        Args:
            filename (str): name of the file
            content (str): content of the file

        Returns:
            str: file saved message
        """
        content = content.encode(FORMAT)
        filename = self.rename_file(filename)
        with open(filename, 'wb') as file:
            file.write(base64.b64decode(content))
            return f'[+] {filename} uploaded successfully.'

    @staticmethod
    def rename_file(file_name: str) -> str:
        """rename file if it exists

        Args:
            file_name (str): original file name

        Returns:
            str: new file name
        """
        filename, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(file_name):
            file_name = f'{filename} ({counter}){extension}'
            counter += 1
        return file_name

    @staticmethod
    def downloadable(file_path: str) -> bool:
        """check if file is downloadable (if client wants to download a certain file)

        Args:
            file_path (str): path to the file

        Returns:
            bool: result (True or False)
        """
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(os.path.dirname(__file__), file_path)):
            return True
        return False


def main() -> None:
    """main function that runs the client gui
    """
    app = qtw.QApplication([])
    widget = Server()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

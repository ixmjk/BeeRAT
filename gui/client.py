import base64
import json
import os
import socket
from typing import Any
from PyQt5 import QtTest
from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.uic import loadUi


FORMAT = 'utf-8'


class Client(qtw.QWidget):
    """this class has all client gui related features
    """

    def __init__(self, *args, **kwargs) -> None:
        """the constructor for Client gui class
        """
        super().__init__(*args, **kwargs)
        self.script_location = os.path.dirname(__file__)
        self.ui_file = 'client.ui'
        self.ui = loadUi(os.path.join(self.script_location, self.ui_file), self)
        self.ui.pb.clicked.connect(self.connect)
        self.ui.le.returnPressed.connect(self.enter)

    def closeEvent(self, event) -> None:
        """custom window close method
        """
        os._exit(0)

    def connection(self, client_socket: socket.socket) -> None:
        """alternative constructor (receive from socket_signal)

        Args:
            client_socket (socket.socket): the client socket
        """
        self.client_socket = client_socket

    def send(self, data: Any) -> None:
        """custom client_socket send method

        Args:
            data (Any): data that you wish to send
        """
        json_data = json.dumps(data)
        self.client_socket.send(json_data.encode(FORMAT))

    def recv(self) -> Any:
        """custom client_socket recv method

        Returns:
            Any: data that you wish to receive
        """
        json_data = ''
        while True:
            try:
                json_data = json_data + self.client_socket.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def disable_ui_elements(self, elements: list) -> None:
        """disable ui elements\n
        elements[le1: ip, le2: password, pb: connect, le: command bar]

        Args:
            elements (list): list of booleans\n
            e.g. elements=[True, True, True, True] -> enable all ui elements
        """
        self.ui.le1.setEnabled(not elements[0])
        self.ui.le2.setEnabled(not elements[1])
        self.ui.pb.setEnabled(not elements[2])
        self.ui.le.setEnabled(not elements[3])

    def connect(self) -> None:
        """connect button click event
        """
        self.connect_thread = ConnectThread(ip=self.ui.le1.text(), password=self.ui.le2.text())
        self.connect_thread.start()
        self.connect_thread.log_signal.connect(lambda text: self.ui.tb.append(text))
        self.connect_thread.elements_signal.connect(self.disable_ui_elements)
        self.connect_thread.socket_signal.connect(self.connection)
        self.connect_thread.placeholder_signal.connect(lambda text: self.ui.le.setPlaceholderText(text))

    def enter(self) -> None:
        """command bar enter event
        """
        command = self.ui.le.text()
        self.ui.le.clear()
        if command == 'upload':
            file_dialog = qtw.QFileDialog.getOpenFileName(self, 'Select a file', '', 'All files (*.*)')
            file_path = file_dialog[0]
            if file_path:
                self.ui.le.setText(f'upload {file_path}')
        elif command == 'BeeRAT-help':
            help_message = ('BeeRAT-help: display information about builtin commands\n'
                            'exit: exit the shell\n'
                            'clear: clear the terminal screen\n'
                            'download: download file from server\n'
                            '   usage: download [filepath]\n'
                            'upload: upload file to server\n'
                            '   usage: upload [filepath]\n'
                            'downloadable: check if file is downloadable from server\n'
                            '   usage: downloadable [filepath]\n'
                            'BeeRAT-passwd: change BeeRAT server password\n'
                            'pwd: print the name of the current working directory\n'
                            'cd: change the shell working directory\n'
                            'ls: list the files in current working directory\n')
            self.ui.tb.append(help_message)
        elif 'BeeRAT-passwd' in command:
            self.ui.tb.append('BeeRAT-passwd: Change server password')
            d = InputDialog()
            if d.exec():
                current_password, new_password, renew_password = d.getInputs()
                if current_password and new_password and renew_password:
                    if new_password == renew_password:
                        if len(new_password) >= 8:
                            self.send(f'BeeRAT-passwd {current_password}')
                            if self.recv():
                                self.send(new_password)
                                if self.recv():
                                    self.ui.tb.append('[+] Password changed successfully.')
                            else:
                                self.ui.tb.append('[-] Current password is wrong.')
                        else:
                            self.ui.tb.append('[-] Password must be at least 8 characters long.')
                    else:
                        self.ui.tb.append('[-] Passwords dont match.')
        else:
            self.enter_thread = EnterThread(client=self.client_socket, command=command)
            self.enter_thread.start()
            self.enter_thread.log_signal.connect(lambda text: self.ui.tb.append(text))
            self.enter_thread.elements_signal.connect(self.disable_ui_elements)
            self.enter_thread.placeholder_signal.connect(lambda text: self.ui.le.setPlaceholderText(text))
            self.enter_thread.clear_signal.connect(lambda: self.ui.tb.clear())
            self.enter_thread.focus_signal.connect(lambda: self.ui.le.setFocus())


class InputDialog(qtw.QDialog):
    """custom change password input dialog
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(350, 150)
        self.setWindowTitle('BeeRAT-passwd')

        self.first = qtw.QLineEdit(self)
        self.second = qtw.QLineEdit(self)
        self.third = qtw.QLineEdit(self)
        self.first.setEchoMode(qtw.QLineEdit.Password)
        self.second.setEchoMode(qtw.QLineEdit.Password)
        self.third.setEchoMode(qtw.QLineEdit.Password)
        buttonBox = qtw.QDialogButtonBox(qtw.QDialogButtonBox.Ok | qtw.QDialogButtonBox.Cancel, self)

        layout = qtw.QFormLayout(self)
        layout.addRow("Current Password: ", self.first)
        layout.addRow("New Password: ", self.second)
        layout.addRow("Retype new Password: ", self.third)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.text(), self.second.text(), self.third.text()


class ConnectThread(QThread):
    """this class is the connect button click event thread
    """
    log_signal = pyqtSignal(str)
    elements_signal = pyqtSignal(list)
    socket_signal = pyqtSignal(socket.socket)
    placeholder_signal = pyqtSignal(str)

    def __init__(self, ip: str, password: str, parent=None) -> None:
        """the constructor for ConnectThread class

        Args:
            ip (str): ip address of server
            password (str): server password
        """
        super(ConnectThread, self).__init__(parent)
        self.script_location = os.path.dirname(__file__)
        self.ip = ip
        self.password = password

    def run(self) -> None:
        """this method executes when ConnectThread object's start method is called
        """
        try:
            self.log_signal.emit(f'BeeRAT-Client$ connect {self.ip}')
            self.elements_signal.emit([True, True, True, True])
            QtTest.QTest.qWait(100)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(3)
            self.client.connect((self.ip, 55555))
            self.client.settimeout(None)
            self.send(self.password)
            result = self.recv()
            if result:
                self.log_signal.emit('[+] Connected.')
                self.placeholder_signal.emit(self.get_prompt())
                self.elements_signal.emit([True, True, True, False])
                self.socket_signal.emit(self.client)
            else:
                self.log_signal.emit('[-] Password is incorrect.')
                self.send(None)
                self.elements_signal.emit([False, False, False, True])
        except (ConnectionRefusedError, TimeoutError):
            self.log_signal.emit('[-] Connection failed.')
            self.elements_signal.emit([False, False, False, True])
        except Exception:
            self.log_signal.emit('[-] Invalid ip.')
            self.elements_signal.emit([False, False, False, True])

    def send(self, data: Any) -> None:
        """custom socket send method

        Args:
            data (Any): data that you wish to send
        """
        json_data = json.dumps(data)
        self.client.send(json_data.encode(FORMAT))

    def recv(self) -> Any:
        """custom socket recv method

        Returns:
            Any: data that you wish to receive
        """
        json_data = ''
        while True:
            try:
                json_data = json_data + self.client.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def get_prompt(self) -> str:
        """get the prompt from server

        Returns:
            str: command bar prompt ("$USER@$HOSTNAME:$PWD")
        """
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '


class EnterThread(QThread):
    """this class is the command bar enter event thread
    """
    log_signal = pyqtSignal(str)
    elements_signal = pyqtSignal(list)
    placeholder_signal = pyqtSignal(str)
    clear_signal = pyqtSignal()
    focus_signal = pyqtSignal()

    def __init__(self, client: socket.socket, command: str, parent=None) -> None:
        """the constructor for EnterThread class

        Args:
            client (socket.socket): client socket
            command (str): command to run on server
        """
        super(EnterThread, self).__init__(parent)
        self.script_location = os.path.dirname(__file__)
        self.client = client
        self.command = command

    def run(self) -> None:
        """this method executes when EnterThread object, start method is called
        """
        enable_le = True
        try:
            self.log_signal.emit(f'{self.get_prompt()}{self.command}')
            self.elements_signal.emit([True, True, True, True])
            command = self.command.split(' ')
            QtTest.QTest.qWait(100)
            if command[0] == 'exit':  # 6
                self.send('exit')
                self.log_signal.emit('[-] Disconnected.')
                self.placeholder_signal.emit('')
                self.elements_signal.emit([False, False, False, True])
                enable_le = False
            elif command[0] == 'clear':  # 5
                self.clear_signal.emit()
            elif command[0] == 'download':  # 4
                file_path = ' '.join(command[1:])
                self.send(f'downloadable {file_path}')
                downloadable = self.recv()
                if downloadable:
                    file_name = os.path.basename(file_path)
                    self.send(' '.join(command))
                    file_content = self.recv()
                    self.log_signal.emit(self.write_file(file_name, file_content))
                else:
                    self.log_signal.emit(f'download: {file_path}: Not downloadable')
            elif command[0] == 'upload':  # 3
                file_path = ' '.join(command[1:])
                if self.uploadable(file_path):
                    file_name = os.path.basename(file_path)
                    file_content = self.read_file(file_path)
                    self.send(f'upload {file_name}')
                    QtTest.QTest.qWait(100)
                    self.send(file_content)
                    self.log_signal.emit(self.recv())
                else:
                    self.log_signal.emit(f'upload: {file_path}: Not uploadable')
            else:  # 1
                command = ' '.join(command)
                self.send(command)
                result = self.recv()
                self.log_signal.emit(str(result))
                self.placeholder_signal.emit(self.get_prompt())
        except ConnectionResetError:
            self.log_signal.emit('[-] Server disconnected.')
            self.placeholder_signal.emit('')
            self.elements_signal.emit([False, False, False, True])
            enable_le = False
        except Exception as e:
            self.log_signal.emit(str(e))
        finally:
            if enable_le:
                self.elements_signal.emit([True, True, True, False])
                self.focus_signal.emit()

    def send(self, data: Any) -> None:
        """custom socket send method

        Args:
            data (Any): data that you wish to send
        """
        json_data = json.dumps(data)
        self.client.send(json_data.encode(FORMAT))

    def recv(self) -> Any:
        """custom socket recv method

        Returns:
            Any: data that you wish to receive
        """
        json_data = ''
        while True:
            try:
                json_data = json_data + self.client.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def get_prompt(self) -> str:
        """get the prompt from server

        Returns:
            str: command bar prompt ("$USER@$HOSTNAME:$PWD")
        """
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '

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
            return f'[+] {filename} downloaded successfully.'

    def uploadable(self, file_path: str) -> bool:
        """check if file is uploadable

        Args:
            file_path (str): path to the file

        Returns:
            bool: result (True or False)
        """
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(self.script_location, file_path)):
            return True
        return False


def main() -> None:
    """main function that runs the client gui
    """
    app = qtw.QApplication([])
    widget = Client()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

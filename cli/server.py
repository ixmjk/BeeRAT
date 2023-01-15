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


FORMAT = 'utf-8'


class RestartServer(Exception):
    pass


class Server:
    """this is a class that has all server related features
    """

    def __init__(self) -> None:
        """the constructor for Server class
        """
        self.script_location = pathlib.Path.home()
        self.password_file = os.path.join(self.script_location, 'BeeRAT-password.txt')
        self.log_file = os.path.join(self.script_location, 'BeeRAT-log.txt')

    def start(self) -> None:
        """start method starts the server
        first it will check for password file in script directory
        then will call the run method
        """
        self.clear()
        print('[+] Press ctrl+c or ctrl+break to stop the server.')
        self.log(f'[{self.get_time()}] server started.')
        if 'BeeRAT-password.txt' not in os.listdir(self.script_location):
            self.set_password('password')
        self.run()

    def run(self) -> None:
        """run method of Server class (i.e. core of the app)

        Raises:
            RestartServer: to restart the server (listen for connection)
        """
        try:
            self.connection, self.address = self.listen()
            self.connection.settimeout(300)
            # authenticate client
            print(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] is authenticating.'))
            password = self.recv()
            if password is None:
                raise RestartServer
            password_hash = self.hash_password(password)
            if password_hash == self.get_password():
                self.send(True)
                print(self.log(f'[+] [{self.get_time()}] [{self.address[0]}] connected.'))
            else:
                print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] authentication failed.'))
                self.send(False)
                raise RestartServer
            # authentication was successful
            while True:
                command = self.recv().split(' ')
                print(self.log(f"[+] [{self.get_time()}] [{self.address[0]}] command: {' '.join(command)}"))
                if command[0] == 'exit':
                    print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
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
                    file_content = self.recv()
                    self.send(self.write_file(file_name, file_content))
                elif command[0] == 'BeeRAT-passwd' and len(command) > 1:
                    password = ' '.join(command[1:])
                    if self.hash_password(password) == self.get_password():
                        self.send(True)
                        new_password = self.recv()
                        self.set_password(new_password)
                        self.send(True)
                    else:
                        self.send(False)
                else:
                    command = ' '.join(command)
                    command_result = self.execute_system_command(command)
                    self.send(command_result)
        except ConnectionResetError:
            print(self.log(f'[-] [{self.get_time()}] [{self.address[0]}] disconnected.'))
            self.run()
        except (RestartServer, TimeoutError):
            self.run()
        except Exception as e:
            print(f'!!! {str(e)} !!!')
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
        print(self.log(f'[+] [{self.get_time()}] [{ip}] listening...'))
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
    def clear():
        """clear the terminal screen
        """
        return os.system('cls' if os.name == 'nt' else 'clear')

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
    """main function that runs the Server class
    """
    while True:
        try:
            command = input('BeeRAT-Server$ ').split(' ')
            if command[0] == 'help' and len(command) == 1:
                print('Commands:\n\t\thelp\n\t\tclear\n\t\tpasswd\n\t\tstart\n\t\texit\n')
            elif command[0] == 'clear' and len(command) == 1:
                Server.clear()
            elif command[0] == 'exit' and len(command) == 1:
                os._exit(0)
            elif command[0] == 'passwd' and len(command) == 1:
                new_password = getpass.getpass('New Password: ')
                renew_password = getpass.getpass('Retype new Password: ')
                if new_password == renew_password:
                    if len(new_password) >= 8:
                        Server().set_password(new_password)
                        print('[+] Password saved successfully.')
                    else:
                        print('[-] Password must be at least 8 characters long.')
                else:
                    print('[-] Passwords dont match.')
            elif command[0] == 'start':
                server = Server()
                server.start()
            else:
                print('[-] Unknown command.')
        except (KeyboardInterrupt, EOFError):
            exit()
        except Exception as e:
            print(str(e))


if __name__ == '__main__':
    main()

import socket
import json
import os
import base64


FORMAT = 'utf-8'


class Client:
    def __init__(self, ip, port) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))

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

    def run(self):
        while True:
            try:
                self.send('info')
                info = self.recv()
                command = input(f'{info}# ').split(' ')
                if command[0] == 'exit':
                    self.send('exit')
                    exit()
                elif command[0] == 'clear':
                    def clear(): return os.system('cls' if os.name == 'nt' else 'clear')
                    clear()
                elif command[0] == 'download':
                    file_path = ' '.join(command[1:])
                    self.send(f'downloadable {file_path}')
                    downloadable = self.recv()
                    if downloadable:
                        file_name = os.path.basename(file_path)
                        self.send(' '.join(command))
                        file_content = self.recv().encode(FORMAT)
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
                else:
                    command = ' '.join(command)
                    self.send(command)
                    result = self.recv()
                    print(result)
            except Exception as e:
                print(str(e))
            except KeyboardInterrupt:
                pass


def main():
    SERVER = socket.gethostbyname(socket.gethostname())
    my_client = Client(SERVER, 4444)
    my_client.run()


if __name__ == '__main__':
    main()

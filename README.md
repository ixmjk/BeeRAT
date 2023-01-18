# BeeRAT
An easy-to-use remote access tool.

## Technologies
BeeRAT is written in [Python3](https://www.python.org/) which is an easy-to-use, general-purpose programming language. The core functionality uses [socket](https://docs.python.org/3/library/socket.html) module of [the Python standard library](https://docs.python.org/3/library/) for communication between two computers using TCP protocol and [subprocess](https://docs.python.org/3/library/subprocess.html) module, also from [the Python standard library](https://docs.python.org/3/library/), for executing the commands sent to the remote computer. BeeRAT uses [PyQT5](https://pypi.org/project/PyQt5/), a Python interface for Qt, one of the most powerful, and popular cross-platform GUI libraries.

## How to run BeeRAT?
### cli
```
git clone https://github.com/ixmjk/BeeRAT.git

cd BeeRAT/cli

python client.py  # run BeeRAT Client
python server.py  # run BeeRAT Server
```
### gui
```
git clone https://github.com/ixmjk/BeeRAT.git

cd BeeRAT/gui

pip install PyQt5

python client.py  # run BeeRAT Client
python server.py  # run BeeRAT Server
```

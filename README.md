# BeeRAT
An easy-to-use remote access tool.

## Technologies
BeeRAT is written in [Python3](https://www.python.org/) which is an easy-to-use, general-purpose programming language. The core functionality uses [socket](https://docs.python.org/3/library/socket.html) module of [the Python standard library](https://docs.python.org/3/library/) for communication between two computers using TCP protocol and [subprocess](https://docs.python.org/3/library/subprocess.html) module, also from [the Python standard library](https://docs.python.org/3/library/), for executing the commands sent to the remote computer. BeeRAT uses [PyQT5](https://pypi.org/project/PyQt5/), a Python interface for Qt, one of the most powerful, and popular cross-platform GUI libraries.

## Usage
BeeRAT offers two modes of operation: Command Line Interface (CLI) and Graphical User Interface (GUI). Choose the mode that best suits your needs and preferences.

### CLI
To use BeeRAT in CLI mode, follow these steps:

1. Clone the BeeRAT repository:
   ```
   git clone https://github.com/ixmjk/BeeRAT.git
   ```

2. Navigate to the CLI directory:
   ```
   cd BeeRAT/cli
   ```

3. Run the BeeRAT Client:
   ```
   python client.py
   ```

4. Run the BeeRAT Server:
   ```
   python server.py
   ```

### GUI
To use BeeRAT in GUI mode, follow these steps:

1. Clone the BeeRAT repository:
   ```
   git clone https://github.com/ixmjk/BeeRAT.git
   ```

2. Navigate to the GUI directory:
   ```
   cd BeeRAT/gui
   ```

3. Install PyQt5 (if not already installed):
   ```
   pip install PyQt5
   ```

4. Run the BeeRAT Client:
   ```
   python client.py
   ```

5. Run the BeeRAT Server:
   ```
   python server.py
   ```

### Important Notes
- Default BeeRAT-Server password is `password`.
- Default location for BeeRAT-Server password file is: `"C:\Users\<YourUserName>\BeeRAT-password.txt"`.
- Default location for BeeRAT-Server log file is: `"C:\Users\<YourUserName>\BeeRAT-log.txt"`.
- Using the `BeeRAT-help` command will display a help message containing a list of available commands.


### Precompiled Versions
If you prefer not to run the Python scripts directly, you can use the precompiled executable versions of the BeeRAT Client and Server. These versions offer a more portable way to use BeeRAT without needing Python or dependencies.
You can download the precompiled executables from the [BeeRAT Releases page](https://github.com/ixmjk/BeeRAT/releases).


## Screenshots

![BeeRAT-Server-gui-v0 1 0-windows_fqrcM3Rl8z](https://github.com/ixmjk/BeeRAT/assets/66163456/5343e83e-81e6-49f3-b07f-07823c32f7ae)

![BeeRAT-Client-gui-v0 1 0-windows_DKPv2hsXuh](https://github.com/ixmjk/BeeRAT/assets/66163456/c2a4557e-a3cf-45cc-9663-afcf1700f461)


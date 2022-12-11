from PyQt5.QtWidgets import QLineEdit, QFileDialog


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(QLineEdit, self).__init__(parent)

    def mouseDoubleClickEvent(self, event):
        file_dialog = QFileDialog.getOpenFileName(self, 'Select a file', '', 'All files (*.*)')
        file_path = file_dialog[0]
        if file_path:
            self.setText(f'upload {file_path}')

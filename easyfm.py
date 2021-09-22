import sys

from PyQt5.QtWidgets import QApplication

from app.gui.base import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def plt(self):
        plt.plot([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        plt.show()

    def initUI(self):

        qbtn = QPushButton('Quit', self)
        qbtn.clicked.connect(self.plt)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Quit button')
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

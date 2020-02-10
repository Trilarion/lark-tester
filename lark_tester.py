"""
  Lark grammar tester with a convenient GUI based on PyQt.
  For more information, see README.md.
"""

import sys
import os
from functools import partial
import pprint
from lark import Lark, Transformer, Discard
from PyQt5 import QtWidgets, QtCore, QtGui

def read_text(file):
    """
    Reads a whole text file (UTF-8 encoded).
    """
    with open(file, mode='r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    return text


def write_text(file, text):
    """
    Writes a whole text file (UTF-8 encoded).
    """
    with open(file, mode='w', encoding='utf-8') as f:
        f.write(text)


class MainWindow(QtWidgets.QWidget):


    #: signal, scenario has changed completely
    update = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        """
        Sets up the graphics view, the toolbar and the tracker rectangle.
        """
        super().__init__(*args, **kwargs)
        self.setMinimumSize(1200, 800)

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

        layout = QtWidgets.QGridLayout(self)


        box = QtWidgets.QGroupBox('Grammar')
        l = QtWidgets.QVBoxLayout()
        box.setLayout(l)
        #self.tb = QtWidgets.QToolBar()
        #self.ag = QtWidgets.QActionGroup(self.tb)
        #for i in range(4):
        #    a = QtWidgets.QAction('{}'.format(i), self.ag)
        #    a.setCheckable(True)
        #    self.tb.addAction(a)
        #l.addWidget(self.tb)
        #self.edit = QtWidgets.QTextEdit()
        #self.edit.setFont(font)
        tw = QtWidgets.QTabWidget()
        for i in range(4):
            edit = QtWidgets.QTextEdit()
            tw.addTab(edit, '{}'.format(i))
        l.addWidget(tw)
        tw.tabBar().tabBarClicked.connect(self.show_menu)
        # l.addWidget(self.edit)

        # transformer box
        boxx = QtWidgets.QGroupBox('Transformer')
        l7 = QtWidgets.QVBoxLayout()
        boxx.setLayout(l7)

        self.tb3 = QtWidgets.QToolBar()
        self.ag3 = QtWidgets.QActionGroup(self.tb3)
        for i in range(4):
            a = QtWidgets.QAction('{}'.format(i), self.ag3)
            a.setCheckable(True)
            self.tb3.addAction(a)
        a = QtWidgets.QAction('New', self.tb3)
        self.tb3.addAction(a)
        l7.addWidget(self.tb3)

        self.edit7 = QtWidgets.QTextEdit()
        self.edit7.setFont(font)
        l7.addWidget(self.edit7)

        # test content box
        box2 = QtWidgets.QGroupBox('Test content')
        l2 = QtWidgets.QVBoxLayout()
        box2.setLayout(l2)

        self.tb2 = QtWidgets.QToolBar()
        self.ag2 = QtWidgets.QActionGroup(self.tb2)
        for i in range(4):
            a = QtWidgets.QAction('{}'.format(i), self.ag2)
            a.setCheckable(True)
            self.tb2.addAction(a)
        l2.addWidget(self.tb2)

        self.edit2 = QtWidgets.QTextEdit()
        self.edit2.setFont(font)
        l2.addWidget(self.edit2)

        box3 = QtWidgets.QGroupBox('Parsed Tree')

        self.edit3 = QtWidgets.QTextEdit()
        self.edit3.setReadOnly(True)
        self.edit3.setFont(font)
        _ = QtWidgets.QVBoxLayout()
        _.addWidget(self.edit3)
        box3.setLayout(_)

        boxy = QtWidgets.QGroupBox('Transformed')

        self.edit4 = QtWidgets.QTextEdit()
        self.edit4.setReadOnly(True)
        self.edit4.setFont(font)
        self.edit4.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        _ = QtWidgets.QVBoxLayout()
        _.addWidget(self.edit4)
        boxy.setLayout(_)

        self.help_window = QtWidgets.QTextEdit(self)
        self.help_window.setWindowTitle('Help')
        self.help_window.setReadOnly(True)
        self.help_window.setWindowModality(QtCore.Qt.WindowModal)
        self.help_window.setWindowFlags(QtCore.Qt.Window)

        self.prop_window = QtWidgets.QWidget(self)
        self.prop_window.setWindowTitle('Properties')
        self.prop_window.setWindowModality(QtCore.Qt.WindowModal)
        self.prop_window.setWindowFlags(QtCore.Qt.Window)

        cc = QtWidgets.QComboBox(self.prop_window)
        cc.addItems(['Earley', 'LALR(1)', 'CYK Parser'])

        ll = QtWidgets.QFormLayout(self.prop_window)
        ll.addRow('Parser', cc)
        ll.addRow('Ambiguity', QtWidgets.QComboBox())
        ll.addRow('Starting rule', QtWidgets.QLineEdit('start'))
        self.prop_window.setLayout(ll)


        toolbar = QtWidgets.QToolBar(self)
        action = QtWidgets.QAction(load_icon('go'), 'Parse and transform', self)
        action.triggered.connect(self.update.emit)
        toolbar.addAction(action)

        action = QtWidgets.QAction(load_icon('settings'), 'Settings', self)
        action.triggered.connect(self.prop_window.show)
        toolbar.addAction(action)

        action = QtWidgets.QAction(load_icon('help'), 'Help', self)
        action.triggered.connect(self.help_window.show)
        toolbar.addAction(action)

        layout.addWidget(toolbar, 0, 0, 1, 3)
        layout.addWidget(box, 1, 0)
        layout.addWidget(boxx, 2, 0)
        layout.addWidget(box2, 3, 0)
        layout.addWidget(box3, 1, 1, 3, 1)
        layout.addWidget(boxy, 1, 2, 3, 1)

    def show_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction('Test'))
        menu.exec(QtGui.QCursor.pos())

    def set_test_content(self, content):
        self.edit2.setPlainText(content)

    def test_content(self):
        return self.edit2.toPlainText()

    def set_grammar(self, grammar):
        pass
        # self.edit.setPlainText(grammar)

    def grammar(self):
        return self.edit.toPlainText()

    def set_output(self, text):
        self.edit3.setPlainText(text)

    def set_transformed(self, text):
        self.edit4.setPlainText(text)


def update(main_window):
    try:
        parser = Lark(main_window.grammar(), debug=False)
        text = main_window.test_content()
        tree = parser.parse(text)
        obj = EntryTransformer().transform(tree)
        # obj = ListingTransformer().transform(tree)
    except Exception as e:
        main_window.set_output(str(e))
        print(e)
    else:
        main_window.set_output(tree.pretty())
        transformed = pprint.pformat(obj, indent=4, width=120, compact=True)
        main_window.set_transformed(transformed)


def load_icon(name):
    """

    :param name:
    :return:
    """
    path = os.path.join(root_path, 'resources', 'icon_' + name + '.png')
    icon = QtGui.QIcon(path)
    return icon

if __name__ == '__main__':

    # root path
    root_path = os.path.dirname(__file__)

    # create app
    app = QtWidgets.QApplication([])

    app.setWindowIcon(load_icon('app'))

    main_window = MainWindow()
    # TODO icon
    main_window.setWindowTitle('Lark Tester')
    main_window.show()

    # read developer.md
    #content = read_text(developer_file)
    content = ''
    main_window.set_test_content(content)

    # grammar_file = os.path.join(c.root_path, 'code', 'grammar_listing.lark')
    # content = read_text(grammar_file)
    main_window.set_grammar(content)

    main_window.update.connect(partial(update, main_window))

    # start Qt app execution
    sys.exit(app.exec_())
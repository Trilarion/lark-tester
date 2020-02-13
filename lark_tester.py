"""
  Lark grammar tester with a convenient GUI based on PyQt.
  For more information, see README.md.
"""

import sys
import os
from functools import partial
import pprint
import json
from lark import Lark, Transformer, Discard
from PyQt5 import QtWidgets, QtCore, QtGui
import utils


def get_setting(key, default_value):
    """
    Convenience function. Accesses a setting. If the setting key is not yet set, uses the default value and set it in
    the settings
    """
    if key not in settings:
        settings[key] = default_value
    return settings[key]


def set_setting(key, value):
    """

    """
    if key not in settings:
        raise RuntimeError('Unknown setting "{}" to be set.'.format(key))
    settings[key] = value


class TextEdit(QtWidgets.QTextEdit):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        """
        super().__init__(*args, **kwargs)
        self.setAcceptRichText(False)

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        """

        """
        if e.key() == QtCore.Qt.Key_Tab:
            # TODO insert the correct amount of spaces
            self.insertPlainText('    ')
        else:
            super().keyPressEvent(e)


class SettingsWindow(QtWidgets.QWidget):
    """
    Settings window.
    """

    def __init__(self, *args, **kwargs):
        """
        Sets up the settings window.
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Properties')
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumSize(600, 400)

        cc = QtWidgets.QComboBox(self)
        cc.addItems(['Earley', 'LALR(1)', 'CYK Parser'])

        ll = QtWidgets.QFormLayout(self)
        ll.addRow('Parser', cc)
        ll.addRow('Ambiguity', QtWidgets.QComboBox())
        ll.addRow('Starting rule', QtWidgets.QLineEdit('start'))
        self.setLayout(ll)


class MainWindow(QtWidgets.QWidget):
    """

    """

    #: signal, update button has been pressed
    update = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        """
        Sets up the graphics view, the toolbar and the tracker rectangle.
        """
        super().__init__(*args, **kwargs)

        MIN_WIDTH = 1200
        MIN_HEIGHT = 800
        self.setMinimumSize(1200, 800)
        self.resize(get_setting('window.size.width', MIN_WIDTH), get_setting('window.size.height', MIN_HEIGHT))

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

        grammar_groupbox = QtWidgets.QGroupBox('Grammar')
        self.grammar_tabs = QtWidgets.QTabWidget()
        self.grammars = []
        for i in range(4):
            edit = TextEdit()
            edit.setFont(font)
            self.grammar_tabs.addTab(edit, '{}'.format(i))
            self.grammars.append(edit)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.grammar_tabs)
        grammar_groupbox.setLayout(l)

        # transformer box
        transformer_groupbox = QtWidgets.QGroupBox('Transformer')
        self.transformer_tabs = QtWidgets.QTabWidget()
        self.transformers = []
        for i in range(4):
            edit = TextEdit()
            edit.setFont(font)
            self.transformer_tabs.addTab(edit, '{}'.format(i))
            self.transformers.append(edit)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.transformer_tabs)
        transformer_groupbox.setLayout(l)

        # test content box
        content_groupbox = QtWidgets.QGroupBox('Test content')
        self.content_tabs = QtWidgets.QTabWidget()
        self.contents = []
        for i in range(4):
            edit = QtWidgets.QTextEdit()
            edit.setFont(font)
            self.content_tabs.addTab(edit, '{}'.format(i))
            self.contents.append(edit)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.content_tabs)
        content_groupbox.setLayout(l)

        # parsed tree output
        parsed_groupbox = QtWidgets.QGroupBox('Parsed Tree')
        self.parsed = QtWidgets.QTextEdit()
        self.parsed.setReadOnly(True)
        self.parsed.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        self.parsed.setFont(font)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.parsed)
        parsed_groupbox.setLayout(l)

        # transformed output
        transformed_groupbox = QtWidgets.QGroupBox('Transformed')
        self.transformed = QtWidgets.QTextEdit()
        self.transformed.setReadOnly(True)
        self.transformed.setFont(font)
        self.transformed.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.transformed)
        transformed_groupbox.setLayout(l)

        # help window
        self.help_window = QtWidgets.QTextEdit(self)
        self.help_window.setWindowTitle('Help')
        self.help_window.setMinimumSize(600, 400)
        self.help_window.setReadOnly(True)
        self.help_window.setWindowModality(QtCore.Qt.WindowModal)
        self.help_window.setWindowFlags(QtCore.Qt.Window)
        self.help_window.setMarkdown(readme_text)

        # settings window
        self.settings_window = SettingsWindow()

        # top toolbar
        toolbar = QtWidgets.QToolBar(self)

        # parse and transform action
        action = QtWidgets.QAction(load_icon('go'), 'Parse and transform', self)
        action.triggered.connect(self.update.emit)
        toolbar.addAction(action)

        # show settings action
        action = QtWidgets.QAction(load_icon('settings'), 'Settings', self)
        action.triggered.connect(self.settings_window.show)
        toolbar.addAction(action)

        # show help action
        action = QtWidgets.QAction(load_icon('help'), 'Help', self)
        action.triggered.connect(self.help_window.show)
        toolbar.addAction(action)

        toolbar.addSeparator()

        # new action
        action = QtWidgets.QAction(load_icon('new'), 'New', self)
        action.triggered.connect(self.new_action)
        toolbar.addAction(action)

        # load action
        action = QtWidgets.QAction(load_icon('load'), 'Load', self)
        action.triggered.connect(self.load_action)
        toolbar.addAction(action)

        # save action
        action = QtWidgets.QAction(load_icon('save'), 'Save', self)
        action.triggered.connect(self.save_action)
        toolbar.addAction(action)

        # search action
        action = QtWidgets.QAction(load_icon('search'),'Search', self)
        action.triggered.connect(self.search_action)
        toolbar.addAction(action)

        # status bar
        self.statusbar = QtWidgets.QStatusBar()

        # wrap grammar, transformer and content boxes in single widget
        left_side = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        left_side.addWidget(grammar_groupbox)
        left_side.addWidget(transformer_groupbox)
        left_side.addWidget(content_groupbox)

        # create QSplitter and add all three columns
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left_side)
        splitter.addWidget(parsed_groupbox)
        splitter.addWidget(transformed_groupbox)

        # layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(toolbar)
        layout.addWidget(splitter, stretch=1)
        layout.addWidget(self.statusbar)

    def set_content(self, content):
        self.contents[self.content_tabs.currentIndex()].setPlainText(content)

    def content(self):
        return self.contents[self.content_tabs.currentIndex()].toPlainText()

    def set_grammar(self, grammar):
        self.grammars[self.grammar_tabs.currentIndex()].setPlainText(grammar)

    def grammar(self):
        return self.grammars[self.grammar_tabs.currentIndex()].toPlainText()

    def set_parsed(self, text):
        self.parsed.setPlainText(text)

    def set_transformed(self, text):
        self.transformed.setPlainText(text)

    def show_message(self, text):
        self.statusbar.showMessage(text)

    def new_action(self):
        pass

    def load_action(self):
        focus = self._determine_focus()
        if focus in ('grammar_tabs', 'transformer_tabs', 'content_tabs'):
            file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', root_path)
            print(file)

    def save_action(self):
        pass

    def search_action(self):
        pass

    def _determine_focus(self):
        if self.grammar_tabs.hasFocus():
            return 'grammar_tabs'
        if self.transformer_tabs.hasFocus():
            return 'transformer_tabs'
        if self.content_tabs.hasFocus():
            return 'content_tabs'
        if self.parsed.hasFocus():
            return 'parsed'
        if self.transformed.hasFocus():
            return 'transformed'
        return None

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """

        """

        # update settings
        set_setting('window.size.width', self.width())
        set_setting('window.size.height', self.height())

        # save setting
        text = json.dumps(settings, indent=1)
        utils.write_text(settings_file, text)

        event.accept()


def update(main_window):
    try:
        parser = Lark(main_window.grammar(), debug=False)
        text = main_window.content()
        tree = parser.parse(text)
        # obj = Transformer().transform(tree)
    except Exception as e:
        main_window.set_parsed(str(e))
        main_window.show_message('error occurred')
        print(e)
    else:
        main_window.set_parsed(tree.pretty())
        transformed = pprint.pformat('', indent=4, width=120, compact=True)
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

    # read readme file (for the help window)
    readme_text = utils.read_text(os.path.join(root_path, 'README.md'))

    # read settings
    settings = {}
    settings_file = os.path.join(root_path, 'settings.json')
    try:
        text = utils.read_text(settings_file)
        settings = json.loads(text)
    except:
        pass

    # create app
    app = QtWidgets.QApplication([])

    app.setWindowIcon(load_icon('app'))

    main_window = MainWindow()
    # TODO icon
    main_window.setWindowTitle('Lark Tester')
    main_window.show()

    # read developer.md
    content = ''
    main_window.set_content(content)
    main_window.set_grammar(content)
    main_window.update.connect(partial(update, main_window))

    # start Qt app execution
    sys.exit(app.exec_())
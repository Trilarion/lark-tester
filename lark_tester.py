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


def get_setting(key, *default_value):
    """
    Convenience function. Accesses a setting. If the setting key is not yet set, uses the default value and set it in
    the settings.
    """
    if key not in settings and default_value:
        settings[key] = default_value[0]
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

    def __init__(self, mode):
        """

        """
        super().__init__()
        self.setAcceptRichText(False)
        self.file = None
        if not mode in ('grammar', 'transformer', 'content'):
            raise RuntimeError('unknown mode')
        self.mode = mode
        if self.mode == 'grammar':
            self.file_filter = "Lark grammar (*.lark);;All files (*.*)"
        elif self.mode == 'transformer':
            self.file_filter = "Lark grammar (*.py);;All files (*.*)"
        else:
            self.file_filter = "All files (*.*)"

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        """
        Replace tab inputs with spaces, if desired.
        """
        if e.key() == QtCore.Qt.Key_Tab and self.mode in ('grammar', 'transformer'):
            # TODO insert the correct amount of spaces
            self.insertPlainText(' ' * get_setting('options.tab_replacement_spaces', 4))
        else:
            super().keyPressEvent(e)

    def new(self):
        """

        """
        if self.mode == 'transformer':
            content = '# transformer\n\nclass MyTransformer(Transformer):\n    null = lambda self, _: None\n    true = lambda self, _: True\n    false = lambda self, _: False\n'
        elif self.mode == 'grammar':
            content = '// grammar\n\nstart:'
        else:
            content = ''
        self.setPlainText(content)
        self.file = None

    def load(self, *args):
        if args:
            file = args[0]
            if not file or not os.path.isfile(file):
                return
        else:
            # show file open dialog
            file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', get_setting('path.current'), self.file_filter)
            file = file[0]
            if not file: # cancel in the dialog
                return

        # file exists, we should load it
        set_setting('path.current', os.path.dirname(file))
        content = utils.read_text(file)
        # TODO replace tabs
        self.setPlainText(content)
        self.file = file

    def save(self):
        if self.file:
            file = self.file
        else:
            # show file save dialog
            file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', get_setting('path.current'), self.file_filter)
            file = file[0]

        if not file:
            return

        # we should save
        file = file[0]
        set_setting('path.current', os.path.dirname(file))
        content = self.toPlainText()
        utils.write_text(file, content)

    def search(self):
        pass


class TabWidget(QtWidgets.QTabWidget):
    """

    """

    def __init__(self):
        """

        """
        super().__init__()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        """
        Directly select tabs with Ctrl+Digit
        """
        if e.modifiers() == QtCore.Qt.ControlModifier and QtCore.Qt.Key_1 <= e.key() < QtCore.Qt.Key_1 + min(10, self.count()):
            self.setCurrentIndex(e.key() - QtCore.Qt.Key_1)
        else:
            super().keyPressEvent(e)


class SettingsWindow(QtWidgets.QWidget):
    """
    Settings window.
    """

    def __init__(self):
        """
        Sets up the settings window.
        """
        super().__init__()
        self.setWindowTitle('Properties')
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumSize(600, 400)

        self.lark_parser_combobox = QtWidgets.QComboBox(self)
        lark_parsers = ['Earley', 'LALR(1)', 'CYK Parser']
        self.lark_parser_combobox.addItems(lark_parsers)
        self.lark_parser_combobox.setCurrentText(get_setting('options.parser', lark_parsers[0]))

        ll = QtWidgets.QFormLayout(self)
        ll.addRow('Parser', self.lark_parser_combobox)
        ll.addRow('Ambiguity', QtWidgets.QComboBox())
        ll.addRow('Starting rule', QtWidgets.QLineEdit('start'))
        self.setLayout(ll)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:

        # update settings
        set_setting('options.parser', self.lark_parser_combobox.currentText())


class LarkHighlighter(QtGui.QSyntaxHighlighter):
    """

    """

    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(*args, **kwargs)

    def highlightBlock(self, text: str) -> None:
        """

        :param text:
        :return:
        """
        # comments
        regex = QtCore.QRegularExpression('\/\/.*')
        i = regex.globalMatch(text)
        while i.hasNext():
            match = i.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), QtCore.Qt.gray)


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """

    """

    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(*args, **kwargs)

        # keywords in blue
        self.rules = [(QtCore.QRegularExpression('\\b{}\\b'.format(keyword)), QtCore.Qt.blue) for keyword in PythonHighlighter.keywords]

        # comments (from # till end of the line)
        self.rules.append((QtCore.QRegularExpression('#.*'), QtCore.Qt.gray))

    def highlightBlock(self, text: str) -> None:
        """

        :param text:
        :return:
        """
        # comments

        for regex, fmt in self.rules:

            i = regex.globalMatch(text)
            while i.hasNext():
                match = i.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class MainWindow(QtWidgets.QWidget):
    """

    """

    NUMBER_TABS = 4
    MIN_WIDTH = 1200
    MIN_HEIGHT = 800

    #: signal, update button has been pressed
    update = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        """
        Sets up the graphics view, the toolbar and the tracker rectangle.
        """
        super().__init__(*args, **kwargs)

        self.setMinimumSize(MainWindow.MIN_WIDTH, MainWindow.MIN_HEIGHT)
        self.resize(get_setting('window.size.width', MainWindow.MIN_WIDTH), get_setting('window.size.height', MainWindow.MIN_HEIGHT))
        self.setWindowTitle('Lark Tester')

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

        grammar_groupbox = QtWidgets.QGroupBox('Grammar')
        self.grammar_tabs = TabWidget()
        self.grammars = []
        files = get_setting('grammars.files', [None]*MainWindow.NUMBER_TABS)
        for i in range(MainWindow.NUMBER_TABS):
            edit = TextEdit(mode='grammar')
            edit.setFont(font)
            edit.load(files[i])  # load them all initially
            self.grammar_tabs.addTab(edit, '{}'.format(i+1))
            self.grammars.append(edit)
            # syntax highlighter
            LarkHighlighter(edit)
        self.grammar_tabs.setCurrentIndex(get_setting('grammars.active_tab', 0))
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.grammar_tabs)
        grammar_groupbox.setLayout(l)

        # transformer box
        transformer_groupbox = QtWidgets.QGroupBox('Transformer')
        self.transformer_tabs = TabWidget()
        self.transformers = []
        files = get_setting('transformers.files', [None]*MainWindow.NUMBER_TABS)
        for i in range(MainWindow.NUMBER_TABS):
            edit = TextEdit(mode='transformer')
            edit.setFont(font)
            edit.load(files[i])  # load them all initially
            self.transformer_tabs.addTab(edit, '{}'.format(i+1))
            self.transformers.append(edit)
            # syntax highlighter
            PythonHighlighter(edit)
        self.transformer_tabs.setCurrentIndex(get_setting('transformers.active_tab', 0))
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.transformer_tabs)
        transformer_groupbox.setLayout(l)

        # test content box
        content_groupbox = QtWidgets.QGroupBox('Test content')
        self.content_tabs = TabWidget()
        self.contents = []
        files = get_setting('contents.files', [None] * MainWindow.NUMBER_TABS)
        for i in range(MainWindow.NUMBER_TABS):
            edit = TextEdit(mode='content')
            edit.setFont(font)
            edit.load(files[i])  # load them all initially
            self.content_tabs.addTab(edit, '{}'.format(i+1))
            self.contents.append(edit)
        self.content_tabs.setCurrentIndex(get_setting('contents.active_tab', 0))
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
        self.transformed.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
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
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F5))
        action.triggered.connect(self.update.emit)
        toolbar.addAction(action)

        toolbar.addSeparator()

        # new action
        action = QtWidgets.QAction(load_icon('new'), 'New', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_N))
        action.triggered.connect(self.new_action)
        toolbar.addAction(action)

        # load action
        action = QtWidgets.QAction(load_icon('load'), 'Load', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_L))
        action.triggered.connect(self.load_action)
        toolbar.addAction(action)

        # save action
        action = QtWidgets.QAction(load_icon('save'), 'Save', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S))
        action.triggered.connect(self.save_action)
        toolbar.addAction(action)

        # search action
        action = QtWidgets.QAction(load_icon('search'),'Search', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F))
        action.triggered.connect(self.search_action)
        toolbar.addAction(action)

        toolbar.addSeparator()

        # show settings action
        action = QtWidgets.QAction(load_icon('settings'), 'Settings', self)
        action.triggered.connect(self.settings_window.show)
        toolbar.addAction(action)

        # show help action
        action = QtWidgets.QAction(load_icon('help'), 'Help', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        action.triggered.connect(self.help_window.show)
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

    def content(self):
        return self.contents[self.content_tabs.currentIndex()].toPlainText()

    def grammar(self):
        return self.grammars[self.grammar_tabs.currentIndex()].toPlainText()

    def set_parsed(self, text):
        self.parsed.setPlainText(text)

    def set_transformed(self, text):
        self.transformed.setPlainText(text)

    def show_message(self, text):
        self.statusbar.showMessage(text)

    def new_action(self):
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.new()

    def load_action(self):
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.load()

    def save_action(self):
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.save()

    def search_action(self):
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.search()
        # TODO also search in output windows

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """

        """

        # update settings
        set_setting('window.size.width', self.width())
        set_setting('window.size.height', self.height())

        set_setting('grammars.files', [x.file for x in self.grammars])
        set_setting('transformers.files', [x.file for x in self.transformers])
        set_setting('contents.files', [x.file for x in self.contents])

        set_setting('grammars.active_tab', self.grammar_tabs.currentIndex())
        set_setting('transformers.active_tab', self.transformer_tabs.currentIndex())
        set_setting('contents.active_tab', self.content_tabs.currentIndex())

        # save setting
        text = json.dumps(settings, indent=1, sort_keys=True)
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

    # fix settings (mostly search for broken paths)
    if 'path.current' not in settings or not os.path.isdir(settings['path.current']):
        settings['path.current'] = root_path

    # create app
    app = QtWidgets.QApplication([])

    app.setWindowIcon(load_icon('app'))

    main_window = MainWindow()
    main_window.show()
    main_window.update.connect(partial(update, main_window))

    # start Qt app execution
    sys.exit(app.exec_())
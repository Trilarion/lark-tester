"""
  Lark grammar tester with a convenient GUI based on PyQt5.
  For more information, see README.md.
"""

import sys
import os
import traceback
from functools import partial
import json
from lark import Lark, Transformer, Discard, v_args  # Transformer, Discard, v_args might be used in the Transformer
from PyQt5 import QtWidgets, QtCore, QtGui
import common

# constants
lark_parsers = ('earley', 'lalr', 'cyk')
lark_parser_names = ('Earley', 'LALR(1)', 'CYK')
minimal_window_size = (1200, 800)
number_tabs = 4
automatic_save_preferences = ['Ask for every open file', 'Always save', 'Never save']

# default settings
default_settings = {
    'options.edit.tabs.replace': True,
    'options.edit.tabs.replacement_spaces': 4,
    'options.edit.wrap_lines': True,
    'options.edit.show_line_numbers': True,
    'options.edit.automatic_save_preference': 0,
    'options.lark.parser': 0,
    'options.lark.starting_rule': 'start',
    'window.size.width': minimal_window_size[0],
    'window.size.height': minimal_window_size[1],
    'window.splitter.columns.size': None,
    'window.splitter.left.size': None,
    'content.active_tab': 0,
    'content.files': [None] * number_tabs,
    'grammar.active_tab': 0,
    'grammar.files': [None] * number_tabs,
    'transformer.active_tab': 0,
    'transformer.files': [None] * number_tabs
}


class TextDisplay(common.CodeEditor):
    """
    A text display that can store text to file.
    The mode is one of ('parsed', 'transformed').
    """

    def __init__(self, mode):
        """
        Initializes the widget. Sets the mode.
        """
        super().__init__(settings['options.edit.show_line_numbers'])
        if mode not in ('parsed', 'transformed'):
            raise RuntimeError('unknown mode')
        self.mode = mode
        self.file_filter = "All files (*.*)"

    def save(self):
        """
        Saves the content to file.
        """
        # show file save dialog
        file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save {} to file'.format(self.mode), settings['path.current'], "All files (*.*)")
        file = file[0]

        #  if the open save dialog was canceled or no file is given, do nothing
        if not file:
            return

        # we should save
        settings['path.current'] = os.path.dirname(file)
        content = self.toPlainText()
        common.write_text(file, content)


class TextEdit(common.CodeEditor):
    """
    A code editor that can load and store text from and to file.
    The mode is one of ('grammar', 'transformer', 'content') and influences the file filter.
    """

    def __init__(self, mode, tooltip_changer):
        """
        Initializes the widget. Sets the mode.
        """
        super().__init__(settings['options.edit.show_line_numbers'])
        if mode not in ('grammar', 'transformer', 'content'):
            raise RuntimeError('unknown mode')
        self.mode = mode
        self.tooltip_changer = tooltip_changer
        self.file = None
        self.read_content = ''
        if self.mode == 'grammar':
            self.file_filter = "Lark grammar (*.lark);;All files (*.*)"
        elif self.mode == 'transformer':
            self.file_filter = "Lark grammar (*.py);;All files (*.*)"
        else:
            self.file_filter = "All files (*.*)"

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        """
        Replace tab inputs with spaces, if desired (for 'grammar' and 'transformer' mode only)
        """
        if self.mode in ('grammar', 'transformer') and settings['options.edit.tabs.replace'] and e.key() == QtCore.Qt.Key_Tab:
            self.insertPlainText(' ' * settings['options.edit.tabs.replacement_spaces'])
        else:
            super().keyPressEvent(e)

    def new(self):
        """
        Sets a new default text depending on the mode.
        """
        if self.mode == 'transformer':
            content = '# transformer\n\nclass MyTransformer(Transformer):\n    null = lambda self, _: None\n    true = lambda self, _: True\n    false = lambda self, _: False\n'
        elif self.mode == 'grammar':
            content = '// grammar\n\nstart:'
        else:
            content = ''
        self.setPlainText(content)
        self.file = None
        self.tooltip_changer(self.file)
        self.read_content = ''

    def load(self, file=None):
        """
        Loads content from a file.
        :param file: If given, the file that content should be loaded from.
        """
        if file:
            # check if file is existing, if not do nothing
            if not os.path.isfile(file):
                return
        else:
            # no file specified, show file open dialog
            file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', settings['path.current'], self.file_filter)
            file = file[0]
            #  if the open file dialog was canceled, do nothing
            if not file:
                return

        # file exists, we should load it
        settings['path.current'] = os.path.dirname(file)
        content = common.read_text(file)
        self.file = file
        self.tooltip_changer(self.file)
        self.read_content = content

        # replace tabs if desired and set as content
        if settings['options.edit.tabs.replace']:
            content = content.replace('\t', ' ' * settings['options.edit.tabs.replacement_spaces'])
        self.setPlainText(content)

    def save(self):
        """
        Saves the content to file (either specified before or asks for a name.).
        """
        if self.file:
            file = self.file
        else:
            # show file save dialog
            file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', settings['path.current'], self.file_filter)
            file = file[0]

        #  if the open save dialog was canceled or no file is given, do nothing
        if not file:
            return

        # we should save
        settings['path.current'] = os.path.dirname(file)
        content = self.toPlainText()
        common.write_text(file, content)
        self.file = file
        self.tooltip_changer(self.file)
        self.read_content = content

    def is_modified(self):
        """
        :return: True if the content has been modified since the last load/save operation.
        """
        return self.read_content != self.toPlainText()


class TabWidget(QtWidgets.QTabWidget):
    """
    A tabwidget that can select a tab based on keyboard input Ctrl+Number.
    """

    def __init__(self, *args, **kwargs):
        """
        Just
        """
        super().__init__(*args, **kwargs)

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

    def __init__(self, parent):
        """
        Sets up the settings window.
        """
        super().__init__(parent)
        self.setWindowTitle('Properties')
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumWidth(600)

        # Lark group box
        lark_groupbox = QtWidgets.QGroupBox('Lark')

        self.lark_parser_combobox = QtWidgets.QComboBox(self)
        self.lark_parser_combobox.addItems(lark_parser_names)
        self.lark_parser_combobox.setCurrentIndex(settings['options.lark.parser'])

        self.lark_start_rule_edit = QtWidgets.QLineEdit(settings['options.lark.starting_rule'])

        l = QtWidgets.QFormLayout(lark_groupbox)
        l.addRow('Parser', self.lark_parser_combobox)
        l.addRow('Ambiguity', QtWidgets.QComboBox())
        l.addRow('Starting rule', QtWidgets.QLineEdit('start'))

        # edits group box
        edits_groupbox = QtWidgets.QGroupBox('Edit')

        self.edit_replace_tabs = QtWidgets.QCheckBox()
        self.edit_replace_tabs.setChecked(settings['options.edit.tabs.replace'])
        self.edit_number_spaces = QtWidgets.QSpinBox()
        self.edit_number_spaces.setRange(0, 20)
        self.edit_number_spaces.setValue(settings['options.edit.tabs.replacement_spaces'])
        self.edit_wrap_lines = QtWidgets.QCheckBox()
        self.edit_wrap_lines.setChecked(settings['options.edit.wrap_lines'])
        self.edit_show_line_numbers = QtWidgets.QCheckBox()
        self.edit_show_line_numbers.setChecked(settings['options.edit.show_line_numbers'])
        self.edit_automatic_save = QtWidgets.QComboBox()
        self.edit_automatic_save.addItems(automatic_save_preferences)
        self.edit_automatic_save.setCurrentIndex(settings['options.edit.automatic_save_preference'])

        l = QtWidgets.QFormLayout(edits_groupbox)
        l.addRow('Replace tabs', self.edit_replace_tabs)
        l.addRow('with how many spaces', self.edit_number_spaces)
        l.addRow('Wrap lines', self.edit_wrap_lines)
        l.addRow('Show line numbers', self.edit_show_line_numbers)
        l.addRow('Automatic save on exit', self.edit_automatic_save)

        # put all the group boxes in one layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(lark_groupbox)
        layout.addWidget(edits_groupbox)
        layout.addStretch()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Need to save the state of the dialog in the settings when closed.
        """

        # update settings
        settings['options.lark.parser'] = self.lark_parser_combobox.currentIndex()
        starting_rule = self.lark_start_rule_edit.text()
        if starting_rule:
            settings['options.lark.starting_rule'] = starting_rule
        settings['options.edit.tabs.replace'] = self.edit_replace_tabs.isChecked()
        settings['options.edit.tabs.replacement_spaces'] = self.edit_number_spaces.value()
        settings['options.edit.wrap_lines'] = self.edit_wrap_lines.isChecked()
        settings['options.edit.show_line_numbers'] = self.edit_show_line_numbers.isChecked()
        settings['options.edit.automatic_save_preference'] = self.edit_automatic_save.currentIndex()


class LarkHighlighter(QtGui.QSyntaxHighlighter):
    """
    Highlighter for the Lark Grammar. Follows the typical pattern for QSyntaxHighlighter and unfortunately doesn't use
    Lark.
    """

    styles = {
        'statement': common.createTextCharFormat('mediumblue', style='bold'),
        'comment': common.createTextCharFormat('darkgray', style='italic')
    }

    statements = ('%ignore', '%import', '%declare')

    operators = ('|', '?', '*', '+', '~')

    def __init__(self, *args, **kwargs):
        """
        Defines the Basic rules as well as color schemes.
        """
        super().__init__(*args, **kwargs)

        rules = []

        # rules
        rules += [(r'{}\b'.format(s), 'statement') for s in LarkHighlighter.statements]

        rules += [
            # from '#' until a newline
            (r'\/\/[^\n]*', 'comment')

            # alias
        ]

        self.rules = [(QtCore.QRegularExpression(pattern), LarkHighlighter.styles[format]) for (pattern, format) in rules]

    def highlightBlock(self, text: str) -> None:
        """
        Highlights a block.
        """

        for regex, fmt in self.rules:

            i = regex.globalMatch(text)
            while i.hasNext():
                match = i.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class SearchWidget(QtWidgets.QWidget):
    """
    The search widget.
    """

    def __init__(self):
        """
        Sets up the widget.
        """
        super().__init__()

        # label
        self.label = QtWidgets.QLabel('')

        # line edit
        self.edit = QtWidgets.QLineEdit()
        self.edit.setMaximumWidth(500)
        self.edit.textChanged.connect(self.update_search)

        # previous button
        self.button_previous = QtWidgets.QPushButton('<')
        self.button_previous.setFixedWidth(24)
        self.button_previous.pressed.connect(self.previous_action)

        # next button
        self.button_next = QtWidgets.QPushButton('>')
        self.button_next.setFixedWidth(24)
        self.button_next.pressed.connect(self.next_action)

        # internal parameters
        self.target = None
        self.all_extra_selections = []
        self.current_extra_selection = []

        # layout window
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.edit)
        layout.addWidget(self.button_previous)
        layout.addWidget(self.button_next)
        layout.addStretch()

        # format for highlighting all search results
        self.fmt_all = common.createTextCharFormat(background_color=QtCore.Qt.yellow)

        # format for highlighting the next search result
        self.fmt_current = common.createTextCharFormat(QtCore.Qt.white, QtCore.Qt.blue)

    def start_search(self, target):
        """
        Initializes itself with a new target and makes itself visible.
        :param target: A derivative of QPlainTextEdit/QTextEdit
        """
        # update target and connect
        self.target = target
        self.target.textChanged.connect(self.update_search)
        # update display
        self.label.setText('Search in ({})'.format(target.mode))
        self.edit.setText('')
        self.edit.setFocus()

    def update_search(self):
        """
        The search text has changed. Update the selections.
        """
        search_text = self.edit.text()

        self.all_extra_selections = []
        self.current_extra_selection = []

        if search_text:
            document = self.target.document()

            # find all occurrences of the search string in the document and highlight them
            cursor = self.target.textCursor()
            cursor.setPosition(0)
            while True:
                cursor = document.find(search_text, cursor)
                if cursor.position() == -1:
                    break
                extra_selection = QtWidgets.QTextEdit.ExtraSelection()
                extra_selection.cursor = cursor
                extra_selection.format = self.fmt_all
                self.all_extra_selections.append(extra_selection)

        self.update()

    def update_current(self, mode):
        """
        Updates the current selection.
        :param mode: 'forward' or 'backward'
        """
        search_text = self.edit.text()

        self.current_extra_selection = []

        if search_text:

            cursor = self.target.textCursor()
            document = self.target.document()
            if mode == 'forward':
                cursor = document.find(search_text, cursor)
            else:
                cursor = document.find(search_text, cursor, QtGui.QTextDocument.FindBackward)

            if cursor.position() != -1:

                extra_selection = QtWidgets.QTextEdit.ExtraSelection()
                extra_selection.cursor = cursor
                extra_selection.format = self.fmt_current
                self.current_extra_selection = [extra_selection]

                if mode == 'forward':
                    cursor.clearSelection()
                else:
                    cursor.setPosition(cursor.anchor())
                self.target.setTextCursor(cursor)

        self.update()

    def previous_action(self):
        """
        Updates the current selection in backward direction.
        """
        self.update_current('backward')

    def next_action(self):
        """
        Updates the current selection in forward direction.
        """
        self.update_current('forward')

    def update(self):
        """
        Sets the updated selections on the target, tests if previous/next buttons should be enabled or disabled.
        """
        self.target.setExtraSelections(self.all_extra_selections + self.current_extra_selection)

        # determine if search forward, backward is possible
        previous_search_possible = False
        next_search_possible = False
        search_text = self.edit.text()
        if search_text:
            document = self.target.document()
            cursor = self.target.textCursor()
            cursor = document.find(search_text, cursor)
            next_search_possible = cursor.position() != -1
            cursor = self.target.textCursor()
            cursor = document.find(search_text, cursor, QtGui.QTextDocument.FindBackward)
            previous_search_possible = cursor.position() != -1

        # enable/disable buttons
        self.button_previous.setEnabled(previous_search_possible)
        self.button_next.setEnabled(next_search_possible)

    def reset_and_hide(self):
        """
        Resets the search text, hides the widget and returns the focus to the target.
        """
        self.target.textChanged.disconnect(self.update_search)
        self.edit.setText('')
        self.hide()
        self.target.setFocus()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        """
        Whenever the escape key is pressed, we want to hide the search widget and abandon the search.
        """
        if e.key() == QtCore.Qt.Key_Escape:
            self.reset_and_hide()
        else:
            super().keyPressEvent(e)


class MainWindow(QtWidgets.QWidget):
    """
    The main window of the Lark tester.
    """

    #: signal, update button has been pressed
    update = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        """
        Sets up the graphics view, the toolbar and the tracker rectangle.
        """
        super().__init__(*args, **kwargs)

        # window size
        self.setMinimumSize(minimal_window_size[0], minimal_window_size[1])
        self.resize(settings['window.size.width'], settings['window.size.height'])
        self.setWindowTitle('Lark Tester')

        # use a fixed size font
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font_metrics = QtGui.QFontMetrics(font)
        tabstopwidth = 4 * font_metrics.horizontalAdvance(' ')

        # options that are used multiple times
        wrap_lines = settings['options.edit.wrap_lines']

        # grammar tabs
        grammar_groupbox = QtWidgets.QGroupBox('Grammar')
        self.grammar_tabs = TabWidget()
        self.grammars = []
        self.grammar_highlighters = []
        files = settings['grammar.files']
        for i in range(number_tabs):
            tooltip_changer = partial(self.grammar_tabs.setTabToolTip, i)
            edit = TextEdit('grammar', tooltip_changer)
            edit.setFont(font)
            edit.setTabStopWidth(tabstopwidth)
            if not wrap_lines:
                edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.grammar_tabs.addTab(edit, '{}'.format(i+1))
            self.grammars.append(edit)
            self.grammar_highlighters.append(LarkHighlighter(edit.document()))
            if files[i]:
                edit.load(files[i])
        self.grammar_tabs.setCurrentIndex(settings['grammar.active_tab'])
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.grammar_tabs)
        grammar_groupbox.setLayout(l)

        # transformer tabs
        transformer_groupbox = QtWidgets.QGroupBox('Transformer')
        self.transformer_tabs = TabWidget()
        self.transformers = []
        self.transformer_highlighters = []
        files = settings['transformer.files']
        for i in range(number_tabs):
            tooltip_changer = partial(self.transformer_tabs.setTabToolTip, i)
            edit = TextEdit('transformer', tooltip_changer)
            edit.setFont(font)
            edit.setTabStopWidth(tabstopwidth)
            if not wrap_lines:
                edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.transformer_tabs.addTab(edit, '{}'.format(i+1))
            self.transformers.append(edit)
            self.transformer_highlighters.append(common.PythonHighlighter(edit.document()))
            if files[i]:
                edit.load(files[i])
        self.transformer_tabs.setCurrentIndex(settings['transformer.active_tab'])
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.transformer_tabs)
        transformer_groupbox.setLayout(l)

        # test content tabs
        content_groupbox = QtWidgets.QGroupBox('Test content')
        self.content_tabs = TabWidget()
        self.contents = []
        files = settings['content.files']
        for i in range(number_tabs):
            tooltip_changer = partial(self.content_tabs.setTabToolTip, i)
            edit = TextEdit('content', tooltip_changer)
            edit.setFont(font)
            edit.setTabStopWidth(tabstopwidth)
            if not wrap_lines:
                edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.content_tabs.addTab(edit, '{}'.format(i+1))
            self.contents.append(edit)
            if files[i]:
                edit.load(files[i])
        self.content_tabs.setCurrentIndex(settings['content.active_tab'])
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.content_tabs)
        content_groupbox.setLayout(l)

        # parsed tree output
        parsed_groupbox = QtWidgets.QGroupBox('Parsed Tree')
        self.parsed = TextDisplay('parsed')
        self.parsed.setReadOnly(True)
        self.parsed.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        self.parsed.setFont(font)
        if not wrap_lines:
            self.parsed.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self.parsed)
        parsed_groupbox.setLayout(l)

        # transformed output
        transformed_groupbox = QtWidgets.QGroupBox('Transformed')
        self.transformed = TextDisplay('transformed')
        self.transformed.setReadOnly(True)
        self.transformed.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        self.transformed.setFont(font)
        if not wrap_lines:
            self.transformed.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
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
        self.settings_window = SettingsWindow(self)

        # search area
        self.search_area = SearchWidget()
        self.search_area.hide()

        # top toolbar
        toolbar = QtWidgets.QToolBar(self)

        # parse and transform action
        action = QtWidgets.QAction(load_icon('go'), 'Parse and transform (F5)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F5))
        action.triggered.connect(self.update.emit)
        toolbar.addAction(action)

        toolbar.addSeparator()

        # new action
        action = QtWidgets.QAction(load_icon('new'), 'New (Ctrl + N)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_N))
        action.triggered.connect(self.new_action)
        toolbar.addAction(action)

        # load action
        action = QtWidgets.QAction(load_icon('load'), 'Load (Ctrl + L)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_L))
        action.triggered.connect(self.load_action)
        toolbar.addAction(action)

        # save action
        action = QtWidgets.QAction(load_icon('save'), 'Save (Ctrl + S)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S))
        action.triggered.connect(self.save_action)
        toolbar.addAction(action)

        # search action
        action = QtWidgets.QAction(load_icon('search'), 'Search (Ctrl + F)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F))
        action.triggered.connect(self.search_action)
        toolbar.addAction(action)

        toolbar.addSeparator()

        # show settings action
        action = QtWidgets.QAction(load_icon('settings'), 'Settings', self)
        action.triggered.connect(self.settings_window.show)
        toolbar.addAction(action)

        # show help action
        action = QtWidgets.QAction(load_icon('help'), 'Help (F1)', self)
        action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        action.triggered.connect(self.help_window.show)
        toolbar.addAction(action)

        # status bar
        self.statusbar = QtWidgets.QStatusBar()

        # wrap grammar, transformer and content boxes in single widget
        self.left_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.left_splitter.addWidget(grammar_groupbox)
        self.left_splitter.addWidget(transformer_groupbox)
        self.left_splitter.addWidget(content_groupbox)
        sz = settings['window.splitter.left.size']
        if sz:
            self.left_splitter.setSizes(sz)

        # create QSplitter and add all three columns
        self.column_splitter = QtWidgets.QSplitter()
        self.column_splitter.addWidget(self.left_splitter)
        self.column_splitter.addWidget(parsed_groupbox)
        self.column_splitter.addWidget(transformed_groupbox)
        sz = settings['window.splitter.columns.size']
        if sz:
            self.column_splitter.setSizes(sz)

        # layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(toolbar)
        layout.addWidget(self.search_area)
        layout.addWidget(self.column_splitter, stretch=1)
        layout.addWidget(self.statusbar)

    def content(self):
        """
        Retrieves the content of the actual test content tab.
        """
        return self.contents[self.content_tabs.currentIndex()].toPlainText()

    def grammar(self):
        """
        Retrieves the content of the actual grammar tab.
        """
        return self.grammars[self.grammar_tabs.currentIndex()].toPlainText()

    def transformer(self):
        """
        Retrieves the content of the actual transformer tab.
        """
        return self.transformers[self.transformer_tabs.currentIndex()].toPlainText()

    def set_parsed(self, text):
        """
        Sets the content of the parsed output edit area to text.
        """
        self.parsed.setTextNoScroll(text)

    def set_transformed(self, text):
        """
        Sets the content of the transformed output area to text.
        """
        self.transformed.setTextNoScroll(text)

    def show_message(self, text):
        """
        Shows temporarily a message in the status bar.
        """
        self.statusbar.showMessage(text, 2000)

    def new_action(self):
        """
        The new content button has been pressed. If the focus is in one of the text edits on the left, call their
        respective method to set new default content.
        """
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.new()
        else:
            self.show_message('Cannot set new content here.')

    def load_action(self):
        """
        The load content button has been pressed. If the focus is in one of the text edits on the left, call their
        respective method to load new content.
        """
        focus = self.focusWidget()
        if isinstance(focus, TextEdit):
            focus.load()
        else:
            self.show_message('Cannot load content here.')

    def save_action(self):
        """
        The load content button has been pressed. If the focus is in one of the text edits on the left, call their
        respective method to load new content.
        """
        focus = self.focusWidget()
        if isinstance(focus, (TextEdit, TextDisplay)):
            focus.save()
        else:
            self.show_message('Cannot save content here.')

    def search_action(self):
        """
        The search button has been pressed. If the search area is visible, stop the search and make it invisible.
        """
        if self.search_area.isVisible():
            # if the search area is visible, hide it again
            self.search_area.reset_and_hide()
        else:
            # if the search area is hidden, and the focus is on a certain window, show it and set the focus
            focus = self.focusWidget()
            if isinstance(focus, (TextEdit, TextDisplay)):
                self.search_area.start_search(focus)
                self.search_area.show()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Before the main window (and with it the application) can be closed, we need to check for unsaved modifications
        of the grammar/transformer/test content as well as storing the settings in a file.
        """
        # check for modified files and ask if needed to save or just save depending on the preference
        if settings['options.edit.automatic_save_preference'] != 2:
            for edits, name in ((self.grammars, 'Grammar'), (self.transformers, 'Transformer'), (self.contents, 'Content')):
                for i in range(len(edits)):
                    edit = edits[i]
                    if edit.is_modified():
                        if settings['options.edit.automatic_save_preference'] == 1:
                            save = True
                        else:
                            answer = QtWidgets.QMessageBox.warning(self, 'Unsaved modification', '{} tab {} contains unsaved modifications. Save?'.format(name, i), QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                            save = answer == QtWidgets.QMessageBox.Ok
                        if save:
                            edit.save()

        # update settings
        settings['window.size.width'] = self.width()
        settings['window.size.height'] = self.height()
        settings['window.splitter.columns.size'] = self.column_splitter.sizes()
        settings['window.splitter.left.size'] = self.left_splitter.sizes()

        settings['grammar.files'] = [x.file for x in self.grammars]
        settings['transformer.files'] = [x.file for x in self.transformers]
        settings['content.files'] = [x.file for x in self.contents]

        settings['grammar.active_tab'] = self.grammar_tabs.currentIndex()
        settings['transformer.active_tab'] = self.transformer_tabs.currentIndex()
        settings['content.active_tab'] = self.content_tabs.currentIndex()

        # save setting
        text = json.dumps(settings, indent=1, sort_keys=True)
        common.write_text(settings_file, text)

        event.accept()


def update(main_window):
    """
    One complete Lark run.
    :param main_window: The main window to retrieve and set text.
    """
    # first the parse
    grammar = main_window.grammar()
    content = main_window.content()
    try:
        parser = Lark(grammar, start=settings['options.lark.starting_rule'], parser=lark_parsers[settings['options.lark.parser']], debug=False)
        parsed_tree = parser.parse(content)
    except Exception as e:
        main_window.set_parsed(traceback.format_exc())
        main_window.show_message('Exception during parse')

        # no need to transform
        main_window.set_transformed('')
        return
    main_window.set_parsed(parsed_tree.pretty())

    # then transform
    transformer = main_window.transformer()
    try:
        exec(transformer, globals(), globals())
        transformed_object = MyTransformer().transform(parsed_tree)  # MyTransformer should be a resolved reference at runtime
        if isinstance(transformed_object, (list, tuple)):
            main_window.set_transformed('\n'.join((str(x) for x in transformed_object)))
        elif isinstance(transformed_object, dict):
            main_window.set_transformed('\n'.join(('{}: {}'.format(k, v) for k, v in transformed_object.items())))
        else:
            main_window.set_transformed(str(transformed_object))
    except Exception as e:
        main_window.set_transformed(traceback.format_exc())
        main_window.show_message('Exception during transform')


def load_icon(name):
    """
    Loads an icon (as QIcon) from our resources place.
    :param name: Just the name part from the icon file.
    :return: The QIcon.
    """
    path = os.path.join(root_path, 'resources', 'icon_' + name + '.png')
    icon = QtGui.QIcon(path)
    return icon


def exception_hook(type, value, traceback):
    """
    Use sys.__excepthook__, the standard hook.
    """
    sys.__excepthook__(type, value, traceback)


if __name__ == '__main__':

    # fix PyQt5 eating exceptions (see http://stackoverflow.com/q/14493081/1536976)
    sys.excepthook = exception_hook

    # root path is file path
    root_path = os.path.dirname(__file__)

    # read readme file (for the help window)
    readme_text = common.read_text(os.path.join(root_path, 'README.md'))

    # read settings
    settings_file = os.path.join(root_path, 'settings.json')
    settings = default_settings
    try:
        text = common.read_text(settings_file)
        settings = json.loads(text)
        # we delete all keys in settings that are not in default_settings (cleanup obsolete keys)
        settings = {k: v for k, v in settings.items() if k in default_settings}
    except:
        pass

    # fix settings (mostly search for broken paths)
    if 'path.current' not in settings or not os.path.isdir(settings['path.current']):
        settings['path.current'] = root_path

    # create app
    app = QtWidgets.QApplication([])
    app.setWindowIcon(load_icon('app'))

    # show main window
    main_window = MainWindow()
    main_window.show()
    main_window.update.connect(partial(update, main_window))
    main_window.update.emit()

    # start Qt app execution
    sys.exit(app.exec_())

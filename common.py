"""
Common classes/methods not directly related to the project.
"""

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


class LineNumberArea(QtWidgets.QWidget):
    """
    Translated from https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QtWidgets.QPlainTextEdit):
    """
    Translated from https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """

    def __init__(self, show_line_numbers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.show_line_numbers = show_line_numbers

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)

    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberArea(self, rect, dy):
        if dy != 0:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        if not self.show_line_numbers:
            return 0

        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QtCore.Qt.black)
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(), QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    def setTextNoScroll(self, text):
        """
        Addition: Tries to keep the vertical scroll bar position when setting a new text.
        """
        vertical_scroll_position = self.verticalScrollBar().sliderPosition()
        self.clear()
        self.setPlainText(text)
        self.verticalScrollBar().setSliderPosition(vertical_scroll_position)


def createTextCharFormat(foreground_color=None, background_color=None, style=None):
    """
    Return a QTextCharFormat with the given attributes.
    """
    char_format = QtGui.QTextCharFormat()
    if foreground_color:
        char_format.setForeground(QtGui.QColor(foreground_color))

    if background_color:
        char_format.setBackground(QtGui.QColor(background_color))

    if style:
        if 'bold' in style:
            char_format.setFontWeight(QtGui.QFont.Bold)
        if 'italic' in style:
            char_format.setFontItalic(True)

    return char_format


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """
    Highlighter for Python. Follows a bit the highlighting scheme used in PyCharm.
    Code inspired by https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting.
    """

    styles = {
        'keyword': createTextCharFormat('mediumblue', style='bold'),
        'operator': createTextCharFormat('black'),
        'brace': createTextCharFormat('black'),
        'defclass': createTextCharFormat('mediumblue', style='bold'),
        'string': createTextCharFormat('darkcyan'),
        'string2': createTextCharFormat('darkcyan'),
        'comment': createTextCharFormat('darkgray', style='italic'),
        'self': createTextCharFormat('darkorchid'),
        'numbers': createTextCharFormat('mediumblue'),
    }

    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
         '=',
         '==', '!=', '<', '<=', '>', '>=',  # Comparison
         r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',  # Arithmetic
         r'\+=', '-=', r'\*=', '/=', r'\%=',  # In-place
         r'\^', r'\|', r'\&', r'\~', '>>', '<<']  # Bitwise

    # Python braces
    braces = [r'\{', r'\}', r'\(', r'\)', r'\[', r'\]']

    def __init__(self, *args, **kwargs):
        """
        Defines the Basic rules as well as color scheme
        """
        super().__init__(*args, **kwargs)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the syntax highlighting from this point onward
        self.tri_single = (QtCore.QRegExp("'''"), 1, PythonHighlighter.styles['string2'])
        self.tri_double = (QtCore.QRegExp('"""'), 2, PythonHighlighter.styles['string2'])

        rules = []

        # keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, PythonHighlighter.styles['keyword']) for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, PythonHighlighter.styles['operator']) for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, PythonHighlighter.styles['brace']) for b in PythonHighlighter.braces]

        # all other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, PythonHighlighter.styles['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, PythonHighlighter.styles['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, PythonHighlighter.styles['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, PythonHighlighter.styles['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, PythonHighlighter.styles['defclass']),

            # from '#' until a newline
            (r'#[^\n]*', 0, PythonHighlighter.styles['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, PythonHighlighter.styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, PythonHighlighter.styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, PythonHighlighter.styles['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QtCore.QRegExp(pattern), index, fmt) for (pattern, index, fmt) in rules]

    def highlightBlock(self, text: str) -> None:
        """
        Highlights a given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """
        Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = text.length() - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False

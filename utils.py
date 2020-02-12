"""
Utility methods
"""


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
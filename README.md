# Lark parser tester

A small Editor using PyQt5 for rapid development and testing of [Lark parser](https://github.com/lark-parser/lark)
grammars and transformers. It can be found at https://github.com/Trilarion/lark-tester.

## Features

- Multiple text edits for Lark grammars, transformers and test content with syntax highlighting, line numbers, search
  function and load/save capability.
- Parses the test content and transforms it with the Lark parser using the defined grammar and transformer.
- Displays parsed tree as well as transformed output.
- Allows rapid cycles of changing the grammar, transformer or test content and seeing the parsed/transformed output

![Screenshot](/examples/json_screenshot.png)

## User guide

### Getting started

TODO how to run

### Typical usage

TODO describe default workflow

### Keyboard shortcuts

- F1 : Shows help window
- F5 : Executes a parse and transform the content with Lark run
- Ctrl+F : Toggles search area
- Ctrl+L : Loads from file in actual tab window
- Ctrl+N : Creates new/empty content in actual tab window
- Ctrl+S : Saves actual tab window content to file
- Ctrl+(1,2,..) : Selects a specific tab in the grammar/transformer/content areas

Within a editable text window undo (Ctrl+Z), redo (Ctrl+Y), cut (Ctrl+X), copy (Ctrl+C), paste (Ctrl+V),
select all (Ctrl+A) are available.

### Settings

TODO describe settings and explain how they are stored, return to default settings

Changes in some edit settings may only take effect after a restart.

## Contribution

Contributions are welcome. Please create an [issue](https://github.com/Trilarion/lark-tester/issues) or fork the
repository and create a pull request.

## License

See [license](LICENSE) file.
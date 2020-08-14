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

Make sure that the required dependencies (lark-parser and PyQt5) are installed, then run the *lark_teser.py* script, for
example by executing *python lark_tester.py* after download of this software.

### Typical usage

The recommended way to use the Lark tester is

- insert some simple test content in a Test content tab
- write a simple version of the desired grammar, ignore the Transformer
- try to parse the test content with the simple grammar
- fix errors in the grammar
- inspect the parsed result
- iterate on test content and grammar, bringing both to more production ready levels
- hint: using the different tabs, it's easy to switch between different test contents or grammars
- if the grammar is advanced, produce a simple transformer
- inspect the transformed result, fix errors and iteratively improve the transformer

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

Settings are stored in a file *settings.json* in the directory of the Lark tester script and can be removed at any
time to return to the default values. Tabs with grammar/transformer/content that have been saved will be loaded again
at the next start. Changes in settings or window / splitter sizes are also persistent.

Note: Changes in some edit settings may only take effect after a restart.

## Contribution

Contributions are welcome. Please create an [issue](https://github.com/Trilarion/lark-tester/issues) or fork the
repository and create a pull request.

## License

See [license](LICENSE) file.

Icons made by [Those Icons](https://www.flaticon.com/authors/those-icons) and [Freepik](https://www.flaticon.com/authors/freepik) from [www.flaticon.com](https://www.flaticon.com/)
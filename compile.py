import os
import string
from pathlib import Path

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

# todo:
# <!-- @datetime -->
# this will be replaced with the date the particular file was changed

def collect_files(d = '.'):
    return list(filter(lambda x: (x[-5:] == '.html' or x[-4:] == '.css') and (x[-13:] != '.include.html' or x[-12:] == '.include.css'), os.listdir(d)))


def locate_keyword(substr):
    start_str = '<!-- @'
    start = substr.find(start_str)
    if start == -1:
        return None
    else:
        end = start + substr[start:].find('-->')
        if end == -1:
            return None
        else:
            option_start = start + len(start_str)
            option_end = option_start + substr[option_start:].find(' ')
            option = substr[option_start:option_end]
            return start, end+3, option


def extract_filename_from_include(substr):
    start = substr.find('\'') + 1
    end = start + substr[start:].find('\'')
    return substr[start:end]


def collect_imports_from_file(buf):
    occurrences = []
    i = 0
    
    while i < len(buf):
        pos = locate_keyword(buf[i:])
        if pos != None:
            start, end, option = pos
            occurrences.append((extract_filename_from_include(buf[i+start:i+end]), start, end, option))
            i += end
        else:
            break
    return occurrences


def replace_include(output_path, file_contents, includes):
    print('Writing to', output_path)
    with open(output_path, 'w') as of:
        if len(includes) == 0:
            of.write(file_contents)
        else:
            prev = 0
            for include_path, start, end, option in includes:
                if option == 'include' or option == 'code':
                    of.write(file_contents[prev:start])
                    with open(include_path) as include_contents:
                        include_data = include_contents.read()
                        if option == 'code':
                            lexer = get_lexer_for_filename(include_path)
                            formatter = HtmlFormatter(noclasses=True, style='algol_nu', nobackground=True, cssclass='highlight', linenos='table')
                            include_data = highlight(include_data, lexer, formatter)
                        # remove final newline
                        if include_data[-1] == '\n':
                            include_data = include_data[:-1]
                            of.write(include_data)
                            prev = end
                            of.write(file_contents[prev:])
                elif option == 'datetime':
                    print("datetime not implemented! Ignored")

            
def collect_imports(files, output_dir):
    for fn in files:
        with open(fn) as f:
            buf = f.read()
            includes = collect_imports_from_file(buf)
            replace_include(Path(output_dir, fn), buf, includes)


def main():
    # the following highlights code
    # python3 -m pygments -f html -O "noclasses=True" ./pygments/cmdline.py > output.html

    output_dir = Path('build')
    if not output_dir.is_dir():
        os.makedirs(output_dir)
    
    collect_imports(collect_files(), output_dir)


if __name__ == '__main__':
    main()

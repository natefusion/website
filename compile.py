import os
import string
from pathlib import Path

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time

output_dir = Path('build')
input_dir = Path('src')

class Keyword(Enum):
    code = 0
    include = 1
    datetime = 2

    
def keyword_is_valid(keyword):
    if keyword == 'code':
        return Keyword.code
    elif keyword == 'include':
        return Keyword.include
    elif keyword == 'datetime':
        return Keyword.datetime
    else:
        return None


@dataclass
class Keyword_Info:
    start: int
    end: int
    keyword: Keyword

    
# todo:
# <!-- @datetime -->
# this will be replaced with the date the particular file was changed
def get_datetime(filename):
    return time.strftime("%A, %B %d %Y", time.strptime(time.ctime(os.path.getmtime(filename))))


def collect_files(output_dir, input_dir):
    def valid_file(filename):
        suffixes = filename.suffixes
        if len(suffixes) == 0:
            return False
        filetypes_to_check = ['.html', '.css', '.js']
        regular_filetype = suffixes[-1] in filetypes_to_check
        snippet_filetype = suffixes[0] == '.include'
        return regular_filetype and not snippet_filetype
    
    return list(filter(valid_file, list(Path(input_dir).rglob('*'))))


def extract_filename(cwd, substr):
    start = substr.find('\'') + 1
    end = start + substr[start:].find('\'')
    f = substr[start:end]
    if f[0] == '/':
        return Path(input_dir, f[1:])
    else:
        return Path(cwd, f)


def locate_keyword(filename, file_contents, i):
    start_str = '<!-- @'
    start = file_contents[i:].find(start_str)
    if start == -1:
        return None, False

    start += i
    end_str = '-->'
    end = file_contents[start:].find('-->')
    if end == -1:
        print(f'Error:\n{filename}:\n{file_contents[start:]}\nThe comment didn\'t end!')
        return None, True

    end += start + len(end_str)
    keyword_start = start + len(start_str)
    keyword_end = keyword_start + file_contents[keyword_start:].find(' ')
    raw_keyword = file_contents[keyword_start:keyword_end]
    keyword = keyword_is_valid(raw_keyword)
    if keyword == None:
        print(f'Error:\n{filename}:\n{file_contents[start:end]}\nInvalid keyword \'{keyword}\' on the above line')
        return None, True
    else:
        return Keyword_Info(keyword=keyword, start=start, end=end), False


def parse_file(filename, file_contents):
    i = 0
    occurrences = []
    had_error = False
    while i < len(file_contents):
        keyword_info, err = locate_keyword(filename, file_contents, i)
        if err:
            had_error = True
        if keyword_info != None:
            occurrences.append(keyword_info)
            i += keyword_info.end
        else:
            break
    return occurrences, had_error


def replace_keywords(output_file, filename, file_contents, keywords):
    cwd = Path(filename.parent)
    cursor = 0

    def read_file_skip_newline(f):
        data = f.read()
        if data[-1] == '\n':
            data = data[:-1]
        return data

    for keyword_info in keywords:
        include_data = None
        output_file.write(file_contents[cursor:keyword_info.start])

        if Keyword.include == keyword_info.keyword:
            print('\tIncluding text')
            keyword_str = file_contents[keyword_info.start:keyword_info.end]
            with open(extract_filename(cwd, keyword_str)) as include_file:
                include_data = read_file_skip_newline(include_file)
                        
        elif Keyword.code == keyword_info.keyword:
            print('\thighlighting code')
            keyword_str = file_contents[keyword_info.start:keyword_info.end]
            code_path = extract_filename(cwd, keyword_str)
            with open(code_path) as include_file:
                raw_data = read_file_skip_newline(include_file)
                lexer = get_lexer_for_filename(code_path)
                formatter = HtmlFormatter(noclasses=True, style='algol_nu', nobackground=True, cssclass='highlight', linenos='table')
                include_data = highlight(raw_data, lexer, formatter)
                        
        elif Keyword.datetime == keyword_info.keyword:
            print('\tGetting the date')
            include_data = get_datetime(filename)

        output_file.write(include_data)
        cursor = keyword_info.end
            
    output_file.write(file_contents[cursor:])

            
def main():
    if not output_dir.is_dir():
        os.makedirs(output_dir)

    files =  [(x,open(x).read()) for x in collect_files(output_dir, input_dir)]

    for filename, file_contents in files:
        keywords, err = parse_file(filename, file_contents)

        if err:
            continue
        
        output_path = Path(output_dir, Path(*filename.parts[1:]))
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as output_file:
            print('Writing to', output_path)
            replace_keywords(output_file, filename, file_contents, keywords)


if __name__ == '__main__':
    main()

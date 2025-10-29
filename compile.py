import os
import string
from pathlib import Path
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time
import shutil
import sys

output_dir = Path('build')
input_dir = Path('src')

class Keyword(Enum):
    code = 0
    include = 1
    datetime = 2
    code_lit = 3
    code_raw = 4
    sidenote = 5
    marginnote = 6


# Keyword['code'] == Keyword.code
def keyword_is_valid(keyword):
    keyword_map = {
        'code': Keyword.code,
        'include': Keyword.include,
        'datetime': Keyword.datetime,
        'code-lit': Keyword.code_lit,
        'code-raw': Keyword.code_raw,
        'sidenote': Keyword.sidenote,
        'marginnote': Keyword.marginnote,
    }

    return keyword_map.get(keyword)


@dataclass
class Keyword_Info:
    start: int
    end: int
    start_keyword: int
    end_keyword: int
    start_argument: int
    end_argument: int
    keyword: Keyword

    
# todo:
# <!-- @datetime -->
# this will be replaced with the date the particular file was changed
def get_datetime(filename):
    return time.strftime("%A, %B %d %Y", time.strptime(time.ctime(os.path.getmtime(filename))))


def find(string, chars):
    i = 0
    while i < len(string):
        if string[i] in chars:
            return i
        i += 1
    return -1


def find_not(string, chars):
    i = 0
    while i < len(string):
        if string[i] not in chars:
            return i
        i += 1
    return -1


def collect_files(input_dir, filetypes_to_check):
    def valid_file(filename):
        suffixes = filename.suffixes
        if len(suffixes) == 0:
            return False
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
        return Keyword_Info(keyword=keyword,
                            start=start,
                            end=end,
                            start_argument=keyword_end+1,
                            end_argument=end-len(end_str)-1,
                            start_keyword=keyword_start-1,
                            end_keyword=keyword_end), False


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
            i = keyword_info.end
        else:
            break
    return occurrences, had_error


def find_prev_indent(data, i):
    count = 0
    while(i > 0):
        if data[i] == '\n':
            break
        count += 1
        i -= 1
    return count


def adjust_indent(data, indent):
    lines = data.split('\n')
    out = ''
    for l_idx,l in enumerate(lines):
        if indent > len(l)-1:
            out += l
        else:
            i = 0
            while i < indent:
                if l[i] == ' ' or l[i] == '\t':
                    i += 1
                else:
                    break

            out += l[indent:]
        if l_idx < len(lines)-1:
            out += '\n'
    return out.rstrip()


def has_file_changed(filename, output_path):
    if output_path.exists():
        src = os.path.getmtime(filename)
        dst = os.path.getmtime(output_path)
        is_different_file = src > dst
        return is_different_file
    else:
        return True


def has_included_file_changed(filename, output_path, file_contents, keywords):
    cwd = Path(filename.parent)
    for keyword_info in keywords:
        if Keyword.include == keyword_info.keyword:
            keyword_str = file_contents[keyword_info.start:keyword_info.end]
            included_filename = extract_filename(cwd, keyword_str)
            if has_file_changed(included_filename, output_path):
                return True
    return False


def replace_keywords(output_file, filename, file_contents, keywords):
    cwd = Path(filename.parent)
    cursor = 0

    sidenote_counter = 0

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
                formatter = HtmlFormatter(noclasses=True, style='algol_nu', nobackground=False, cssclass='highlight', linenos='table')
                include_data = highlight(raw_data, lexer, formatter)

        elif Keyword.code_lit == keyword_info.keyword:
            print('\thighlighting code')
            data = file_contents[keyword_info.start_argument:keyword_info.end_argument]
            language_end = find(data, [' ', '\t', '\n'])
            language = data[:language_end]
            raw_code = data[language_end+1:]
            if data[language_end] == '\n':
                indent = find_prev_indent(file_contents, keyword_info.start_keyword-1)
                raw_code = adjust_indent(raw_code, indent)
            
            lexer = get_lexer_by_name(language)
            formatter = HtmlFormatter(noclasses=True, style='algol_nu', nobackground=False, cssclass='highlight')
            include_data = highlight(raw_code, lexer, formatter)

        elif Keyword.code_raw == keyword_info.keyword:
            print('\thighlighting code')
            data = file_contents[keyword_info.start_argument:keyword_info.end_argument]
            language_end = find(data, [' ', '\t', '\n'])
            language = data[:language_end]
            raw_code = data[language_end+1:]
            lexer = get_lexer_by_name(language)
            cssclass = 'highlightraw'
            formatter = HtmlFormatter(noclasses=True, style='algol_nu', nobackground=True, cssclass=cssclass, nowrap=True)
            include_data = highlight(raw_code, lexer, formatter)
            if include_data[-1] == '\n':
                include_data = include_data[:-1]
            include_data = f'<code class=\'{cssclass}\'>' + include_data + '</code>'

        elif Keyword.sidenote == keyword_info.keyword:
            print('\tAdding sidenote')
            data = file_contents[keyword_info.start_argument:keyword_info.end_argument]
            sidenote_counter += 1
            include_data = f"""
            <label for="sn-{sidenote_counter}" class="margin-toggle sidenote-number"></label>
            <input type="checkbox" id="sn-{sidenote_counter}" class="margin-toggle"/>
            <span class="sidenote">{data}</span>
            """

        elif Keyword.marginnote == keyword_info.keyword:
            print('\tAdding marginnote')
            data = file_contents[keyword_info.start_argument:keyword_info.end_argument]
            include_data = f"""
            <span class="marginnote">{data}</span>
            """

        elif Keyword.datetime == keyword_info.keyword:
            print('\tGetting the date')
            include_data = get_datetime(filename)

        output_file.write(include_data)
        cursor = keyword_info.end
            
    output_file.write(file_contents[cursor:])
    return True

            
def main():
    full_rebuild = False

    if len(sys.argv) >= 2 and sys.argv[1] == 'full':
        print('Doing a full rebuild')
        full_rebuild = True

    if not output_dir.is_dir():
        os.makedirs(output_dir)

    files =  [(x,open(x).read()) for x in collect_files(input_dir, ['.html', '.css', '.js'])]
    images = collect_files(input_dir, ['.png', '.jpg', '.ico', '.pdf', '.woff2'])

    for filename in images:
        output_path = Path(output_dir, Path(*filename.parts[1:]))
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)
        if has_file_changed(filename, output_path):
           print('Copying image: ', filename)
           shutil.copyfile(filename, output_path)

    for filename, file_contents in files:
        output_path = Path(output_dir, Path(*filename.parts[1:]))
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)
        keywords, err = parse_file(filename, file_contents)

        if err:
            continue

        if not full_rebuild:
            if not has_file_changed(filename, output_path) and not has_included_file_changed(filename, output_path, file_contents, keywords):
                print(f'Skipping {filename}. It hasn\'t changed');
                continue
        
        with open(output_path, 'w') as output_file:
            print('Writing to', output_path)
            replace_keywords(output_file, filename, file_contents, keywords)


if __name__ == '__main__':
    main()

import os
import string
from pathlib import Path

# todo:
# <!-- @datetime -->
# this will be replaced with the date the particular file was changed

def collect_files(d = '.'):
    return list(filter(lambda x: (x[-5:] == '.html' or x[-4:] == '.css') and (x[-13:] != '.include.html' or x[-12:] == '.include.css'), os.listdir(d)))


def locate_include(substr):
    start = substr.find('<!-- @include')
    if start == -1:
        return None
    else:
        end = start + substr[start:].find('-->')
        if end == -1:
            return None
        else:
            return start, end+3


def extract_filename_from_include(substr):
    start = 15
    end = -5

    if substr[start-2:start] != ' \'':
        print('WUT in tarnation:', substr[start-2:start])

    if substr[end:end+2] != '\' ':
        print('WUT in tarnation:', substr[end:end+2])
    return substr[15:-5]


def collect_imports_from_file(buf):
    occurrences = []
    i = 0
    
    while i < len(buf):
        pos = locate_include(buf[i:])
        if pos != None:
            start, end = pos
            occurrences.append((extract_filename_from_include(buf[i+start:i+end]), start, end))
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
            for include_path, start, end in includes:
                of.write(file_contents[prev:start])
                with open(include_path) as include_contents:
                    include_data = include_contents.read()
                    # remove final newline
                    if include_data[-1] == '\n':
                        include_data = include_data[:-1]
                    of.write(include_data)
                    prev = end
            of.write(file_contents[prev:])

            
def collect_imports(files, output_dir):
    for fn in files:
        with open(fn) as f:
            buf = f.read()
            includes = collect_imports_from_file(buf)
            replace_include(Path(output_dir, fn), buf, includes)


def main():
    output_dir = Path('build')
    if not output_dir.is_dir():
        os.makedirs(output_dir)
    
    collect_imports(collect_files(), output_dir)


if __name__ == '__main__':
    main()

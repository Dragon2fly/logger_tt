__author__ = "Duc Tin"

import re
import tokenize
import linecache
from io import StringIO
from traceback import StackSummary, walk_tb
from logging import getLogger

logger = getLogger(__name__)
ID_PATTERN = re.compile(r'([a-zA-Z_][a-zA-Z_0-9.]*)')
MEM_PATTERN = re.compile(r'<.*object at 0x[0-9A-F]+>')


def get_recur_attr(obj, attr: str):
    """
    Follow the dot `.` in attribute string `attr` to the final object
    :param obj: any object
    :param attr: string of attribute access
    :return: the final desire object or '!!! Not Exists'

    example: if we need to access `c` object as in `a.b.c`,
    then `obj=a, attr='b.c'`
    If `b` or `c` doesn't exists, then `'!!! Not Exists'` is returned
    """
    this_level, *next_levels = attr.split('.', maxsplit=1)
    if not next_levels:
        try:
            return getattr(obj, this_level)
        except AttributeError:
            return "!!! Not Exists"
    else:
        obj = getattr(obj, this_level)
        return get_recur_attr(obj, next_levels[0])


def get_repr(obj) -> str:
    """
    Pick a more useful representation of object `obj` between __str__ and __repr__
     if it available.
    :param obj: any of object
    :return: string of object representation
    """
    _repr_ = repr(obj)
    _str_ = str(obj)
    return _str_ if MEM_PATTERN.match(_repr_) else _repr_


def is_full_statement(*lines:str) -> bool:
    """
    Check if a set of lines makes up a full python statement
    :param lines: list of line of python code
    :return: True if line in `lines` made up a full python statement
    """
    try:
        stream = StringIO()
        stream.write('\n'.join(lines))
        stream.seek(0)
        for t in tokenize.generate_tokens(stream.readline):
            pass
    except tokenize.TokenError as e:
        if 'EOF in multi-line statement' in str(e):
            return False
        raise
    else:
        return True


def get_full_statement(filename, lineno:int) -> list:
    """
    Get all lines of python file `filename` that makes up a full statement starting from `lineno`
    :param filename: path to python source code file
    :param lineno: line number at with the statement started
    :return: list of all lines that made up a python statement with indent striped
    """
    lines = []
    while True:
        line = linecache.getline(filename, lineno)
        if not line:
            break

        lines.append(line)
        if is_full_statement(*lines):
            break

        lineno += 1

    lines[-1] = lines[-1].strip('\n')   # remove newline in last line
    indent = re.search(r'^(\s+)', lines[0]).group(1)
    return [x.replace(indent, '', 1) for x in lines]


def analyze_frame(trace_back, full_context=False) -> str:
    """
    Read out variables' content surrounding the error line of code
    :param trace_back: A traceback object when exception occur
    :param full_context: Also export local variables that is not in the error line
    :return: string of analyzed frame
    """
    result = []
    # todo: add color
    bullet_1 = '├─>'
    bullet_2 = '=>'
    for idx, obj in enumerate(walk_tb(trace_back)):
        frame, _ = obj

        global_var = frame.f_globals
        local_var = frame.f_locals

        summary = StackSummary.extract([obj], capture_locals=True)[0]
        line = summary.line
        if not is_full_statement(summary.line):
            line = get_full_statement(summary.filename, summary.lineno)
            line = '    '.join(line)

        txt = [f'  File "{summary.filename}", line {summary.lineno}, in {summary.name}',
               f'    {line}']

        identifiers = ID_PATTERN.findall(line)
        seen = set()
        outer = "(outer) " if idx else ""       # ground level variables are not outer for sure
        for i in identifiers:
            if i in seen:
                continue

            seen.add(i)
            if i in local_var:
                value = get_repr(local_var[i])
                txt.append(f'     {bullet_1} {i} = {value}')
            elif i in global_var:
                value = get_repr(global_var[i])
                txt.append(f'     {bullet_1} {outer}{i} = {value}')
            elif '.' in i:
                # class attribute access
                instance = i.split('.')[0]
                obj = local_var.get(instance, global_var.get(instance))
                value = get_repr(get_recur_attr(obj, i[len(instance) + 1:]))
                scope = outer if instance in global_var else ''
                txt.append(f'     {bullet_1} {scope}{i} = {value}')
            else:
                # reserved Keyword or non-identifier, eg. word inside the string
                pass

        if full_context or summary.line.strip().startswith("raise"):
            other_local_var = set(local_var) - set(identifiers)
            if other_local_var:
                txt.extend([f'     {bullet_2} {k} = {get_repr(v)}'
                            for k, v in local_var.items() if k in other_local_var])

        txt.append('')
        result.append('\n'.join(txt))

    return '\n'.join(result)



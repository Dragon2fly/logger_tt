__author__ = "Duc Tin"

import re
import logging
import tokenize
import linecache
from io import StringIO
from contextlib import contextmanager
from traceback import StackSummary, walk_tb

ID_PATTERN = re.compile(r'([a-zA-Z_][a-zA-Z_0-9.]*)')
MEM_PATTERN = re.compile(r'<.*object at 0x[0-9A-Fa-f]+>')


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
        except Exception as e:
            return f"!!! Attribute Error: {e}"
    else:
        try:
            obj = getattr(obj, this_level)
        except AttributeError:
            return "!!! Not Exists"
        return get_recur_attr(obj, next_levels[0])


def get_repr(obj, multiline_indent: int = 0) -> str:
    """
    Pick a more useful representation of object `obj` between __str__ and __repr__
     if it available.

    :param obj: any of object
    :param multiline_indent: indent level for the second line onward
    :return: string of object representation
    """
    try:
        _repr_ = repr(obj)
        if not MEM_PATTERN.match(_repr_):
            return _repr_
    except Exception as e:
        _repr_ = f"!!! repr error: {e}"

    try:
        _str_ = str(obj).replace('\r\n', '\n')
        if '\n' in _str_:
            indent = ' ' * multiline_indent
            _str_ = _str_.replace('\n', '\n' + indent)

        return _str_

    except Exception as e:
        return _repr_


def is_half_ended(line: str) -> bool:
    """
    Check if we a given a last line of a multiline statement with brackets
    """
    if line.count(')') > line.count('('):
        return True
    if line.count('}') > line.count('{'):
        return True
    if line.count(']') > line.count('['):
        return True


def is_full_statement(*lines: str) -> bool:
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
        if 'EOF in multi-line' in str(e):
            return False
        else:
            return True
    else:
        return True


def get_statement_up(filename: str, lineno: int) -> list:
    """The python interpreter return the last line of exception lines
        This behavior is of python 3.6, 3.7
        We have to go up to grab the full statement

        Grab maximum 10 lines
    """
    startno = lineno
    lines = []

    while lineno >= max(0, startno - 9):
        line = linecache.getline(filename, lineno)
        lines.insert(0, line)

        temp = ''.join(lines)
        if not is_half_ended(temp):
            break

        lineno -= 1

    return lines


def get_statement_down(filename: str, lineno: int) -> list:
    """The python interpreter return the first line of exception lines
        This behavior is of python 3.9
        We go down normally to grab the full statement

        Grab maximum 10 lines
    """
    lines = []
    startno = lineno
    while lineno <= startno + 9:
        line = linecache.getline(filename, lineno)
        if not line:
            break

        lines.append(line)
        if is_full_statement(*lines):
            break

        lineno += 1

    return lines


def get_full_statement(filename, lineno: int) -> list:
    """
    Get all lines of python file `filename` that makes up a full statement starting from `lineno`

    :param filename: path to python source code file
    :param lineno: line number at with the statement started
    :return: list of maximum 5 lines that made up a python statement with indent striped,
    """

    line = linecache.getline(filename, lineno)
    if is_half_ended(line):
        lines = get_statement_up(filename, lineno)
    else:
        lines = get_statement_down(filename, lineno)

    lines[-1] = lines[-1].strip('\n')  # remove newline in last line
    indent = re.search(r'^(\s+)', lines[0])
    if indent:
        indent = indent.group(1)
        return [x.replace(indent, '', 1) for x in lines]
    else:
        return lines


@contextmanager
def logging_disabled():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def get_traceback_depth(trace_back) -> int:
    count = 0
    tb = trace_back
    while tb is not None:
        tb = tb.tb_next
        count += 1

    return count


def get_basic_exception_info(summary) -> tuple:
    """Return a normal 2 lines of of an exception and a full python statement in case of multiline"""

    line = summary.line
    if not is_full_statement(summary.line):
        line = get_full_statement(summary.filename, summary.lineno)
        line = '    '.join(line)

    txt = [f'  File "{summary.filename}", line {summary.lineno}, in {summary.name}',
           f'    {line}']
    return txt, line


def parse_line(identifiers, frame, outer) -> list:
    """List variables appear on the exception line and their values"""
    seen = set()

    bullet_1 = '|->'
    multi_line_indent1 = 8 + len(bullet_1)

    global_var = frame.f_globals
    local_var = frame.f_locals

    txt = []
    for i in identifiers:
        if i in seen or i.endswith('.'):
            continue

        seen.add(i)
        spaces = multi_line_indent1 + len(i)
        if i in local_var:
            value = get_repr(local_var[i], spaces)
            txt.append(f'     {bullet_1} {i} = {value}')
        elif i in global_var:
            spaces += len(outer)
            value = get_repr(global_var[i], spaces)
            txt.append(f'     {bullet_1} {outer}{i} = {value}')
        elif '.' in i:
            # class attribute access
            spaces += len(outer)
            instance = i.split('.')[0]
            obj = local_var.get(instance, global_var.get(instance))
            attribute = get_recur_attr(obj, i[len(instance) + 1:])
            value = get_repr(attribute, spaces)
            scope = outer if instance in global_var else ''
            txt.append(f'     {bullet_1} {scope}{i} = {value}')
        else:
            # reserved Keyword or non-identifier, eg. word inside the string
            pass

    return txt


def parse_full_context(identifiers, frame) -> list:
    """List variables within the scope of the exception line and their values"""
    bullet_2 = '=>'
    multi_line_indent2 = 8 + len(bullet_2)

    local_var = frame.f_locals
    other_local_var = set(local_var) - set(identifiers)
    txt = []
    if other_local_var:
        spaces = multi_line_indent2
        txt = [f'     {bullet_2} {k} = {get_repr(v, spaces + len(k))}'
               for k, v in local_var.items() if k in other_local_var]
    return txt


def analyze_exception_recur(e: BaseException, full_context: int, limit_line_length: int, analyze_raise_statement: bool,
                            text: str = '') -> str:
    cause = e.__cause__ or e.__context__
    if cause:
        text = analyze_exception_recur(cause, full_context, limit_line_length, analyze_raise_statement, text)
        text += '\nDuring handling of the above exception, another exception occurred:\n\n'

    text += ("Traceback (most recent call last):\n"
             + analyze_frame(e.__traceback__, full_context, limit_line_length, analyze_raise_statement)
             + f'{type(e).__name__}: {e}\n')
    return text


def analyze_frame(trace_back, full_context: int, limit_line_length: int, analyze_raise_statement: bool) -> str:
    """
    Read out variables' content surrounding the error line of code

    :param trace_back: A traceback object when exception occur
    :param full_context: Also export local variables that is not in the error line
            full_context == 0: export only variables that appear on the error line
            full_context == 1: export variables within the error function's scope
            full_context >= 2: export variables along the function's call stack up to `full_context` level
    :param limit_line_length: maximum character on one line of traceback, 0 for unlimited
    :param analyze_raise_statement: should the variables in `raise` exception line be shown or not
    :return: string of analyzed frame
    """
    result = []
    full_context = max(0, int(full_context))
    stack_depth = get_traceback_depth(trace_back)
    # todo: add color

    with logging_disabled():
        for idx, obj in enumerate(walk_tb(trace_back)):
            frame, _ = obj

            summary = StackSummary.extract([obj], capture_locals=True)[0]
            txt, line = get_basic_exception_info(summary)

            # todo: dump all level to different file?
            parse_level = max(full_context - 1, 0)
            if idx + 1 < (stack_depth - parse_level):
                # don't parse variables for top levels
                txt.append('')
                result.append('\n'.join(txt))
                continue

            # get value of variables on the error line
            identifiers = ID_PATTERN.findall(line)
            if analyze_raise_statement or not line.strip().startswith('raise '):
                outer = "(outer) " if idx else ""  # ground level variables are not outer for sure
                new_info = parse_line(identifiers, frame, outer)
                txt.extend(new_info)

            # get value of other variables within local scope
            if full_context:
                new_info = parse_full_context(identifiers, frame)
                txt.extend(new_info)

            # limit the length of the line
            if limit_line_length > 0:
                for i, line in enumerate(txt):
                    if len(line) > limit_line_length:
                        char_left = len(line) - limit_line_length
                        txt[i] = line[:limit_line_length] + f'... ({char_left} characters more)'

            txt.append('')
            result.append('\n'.join(txt))

    return '\n'.join(result)

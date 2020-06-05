__author__ = "Duc Tin"

import re
from traceback import StackSummary, walk_tb
from logging import getLogger

logger = getLogger(__name__)
ID_PATTERN = re.compile(r'([a-zA-Z_][a-zA-Z_0-9.]*)')
MEM_PATTERN = re.compile(r'<.*object at 0x[0-9A-F]+>')


def get_recur_attr(obj, attr: str):
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
    _repr_ = repr(obj)
    _str_ = str(obj)
    return _str_ if MEM_PATTERN.match(_repr_) else _repr_


def analyze_frame(trace_back, full_context=False):
    result = []

    for idx, obj in enumerate(walk_tb(trace_back)):
        frame, _ = obj

        global_var = frame.f_globals
        local_var = frame.f_locals

        summary = StackSummary.extract([obj], capture_locals=True)[0]
        txt = [f'  File "{summary.filename}", line {summary.lineno}, in {summary.name}',
               f'    {summary.line}']

        identifiers = ID_PATTERN.findall(summary.line)
        outer = "(outer) " if idx else ""
        for i in identifiers:
            if i in local_var:
                value = get_repr(local_var[i])
                txt.append(f'     -> {i} = {value}')
            elif i in global_var:
                value = get_repr(global_var[i])
                txt.append(f'     -> {outer}{i} = {value}')
            elif '.' in i:
                # class attribute access
                instance = i.split('.')[0]
                obj = local_var.get(instance, global_var.get(instance))
                value = get_repr(get_recur_attr(obj, i[len(instance) + 1:]))
                scope = outer if instance in global_var else ''
                txt.append(f'     -> {scope}{i} = {value}')
            else:
                # reserved Keyword or non-identifier, eg. word inside the string
                pass

        if full_context or summary.line.strip().startswith("raise"):
            other_local_var = set(local_var) - set(identifiers)
            if other_local_var:
                # txt.append('     ┌──────────────────────────┐')
                # txt.append('     │ => other local variables │')
                # txt.append('     └──────────────────────────┘')
                txt.extend([f'       => {k} = {get_repr(v)}' for k, v in local_var.items() if k in other_local_var])
                txt.append('')
        result.append('\n'.join(txt))

    return '\n'.join(result)

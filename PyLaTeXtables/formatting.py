#! /usr/bin/env python3

import os.path
import re

try:
    import jinja2
except ImportError:
    raise ImportError("Please make sure that the python3-jinja2 package is installed.")

__all__ = ["write_latex"]

def _get_spans(sparse_labels):
    # calculate column/row spans
    spans = [i for i, label in enumerate(sparse_labels) if label]
    spans.append(len(sparse_labels))

    # difference between consecutive elements
    spans = [x - spans[i - 1] for i, x in enumerate(spans) if i > 0]

    sparse_spans = []
    for i in sparse_labels:
        if i:
            sparse_spans.append(spans.pop(0))
        else:
            sparse_spans.append(1)

    return sparse_spans

def get_sparse_labels(multiindex, transpose=True):
    sparse_labels = multiindex.format(sparsify=True, adjoin=False)
    # convert 1D arrays into 2D
    if not isinstance(sparse_labels[0], tuple):
        sparse_labels = [tuple(sparse_labels)]
    sparse_spans = [_get_spans(labels) for labels in sparse_labels]

    # transpose the lists of tuples
    if transpose is True:
        sparse_labels = list(zip(*sparse_labels))
        sparse_spans = list(zip(*sparse_spans))

    # zip into (label, span) pairs
    zipped = []
    for a, b in zip(sparse_labels, sparse_spans):
        r = []
        for pair in zip(a, b):
            r.append(pair)
        zipped.append(r)
    return zipped

def write_latex(df, output_file, *, header_dict=None, template_name="eoc_table_template.tex"):
    if header_dict is None:
        header_dict = {}

    # custom filters
    LATEX_SUBS = (
        (re.compile(r'\\'), r'\\textbackslash'),
        (re.compile(r'([{}_#%&$])'), r'\\\1'),
        (re.compile(r'~'), r'\~{}'),
        (re.compile(r'\^'), r'\^{}'),
        (re.compile(r'"'), r"''"),
        (re.compile(r'\.\.\.+'), r'\\ldots'),
    )

    def escape_tex(value):
        newval = value
        for pattern, replacement in LATEX_SUBS:
            newval = pattern.sub(replacement, newval)
        return newval

    def vertical_text(value):
        if value:
            return r"\rotatebox[origin=c]{90}{" + str(value) + "}"
        return ""

    def multirow(value, span):
        return r"\multirow{" + str(span) + "}{*}{" + str(value) + "}"

    def np(value, digits=None, maybe_int=True, exponents=True):
        if str(value) == "nan":
            return str(value)
        if isinstance(value, int):
            return r"\np{" + str(int(value)) + "}"
        try:
            value = float(value)
            if maybe_int is True and value == int(value):
                return r"\np{" + str(int(value)) + "}"
            if exponents is True:
                if value < 0.25:
                    f = "e"
                elif value < 1000:
                    f = "f"
                else:
                    f = "g"
            else:
                f = "f"
            fnum = r"\np{" + "{:.0{}{}}".format(value, digits, f) + "}"
            # remove leading zeros from exponent
            if "e" in fnum:
                a, b = fnum.split("e")
                a += "e"
                if b.startswith("-") or b.startswith("+"):
                    a += b[0]
                    b = b[1:]
                return a + b.lstrip("0")
            return fnum
        except ValueError:
            return str(value)

    def header_fmt(value):
        if value in header_dict:
            return header_dict[value]
        if "$" in value:
            return value
        if value:
            return "$ {} $".format(value)
        return ""

    if os.path.isfile(template_name):
        template_dir, template_name = os.path.split(template_name)
        loader=jinja2.FileSystemLoader(template_dir)
    else:
        loader=jinja2.PackageLoader("PyLaTeXtables", "templates")

    env = jinja2.Environment(
            block_start_string="((*",
            block_end_string="*))",
            variable_start_string="(((",
            variable_end_string=")))",
            comment_start_string="((#",
            comment_end_string="#))",
            line_comment_prefix="%%>",
            trim_blocks=True,
            loader=loader,
          )
    env.filters["escape_tex"] = escape_tex
    env.filters["vertical_text"] = vertical_text
    env.filters["multirow"] = multirow
    env.filters["np"] = np
    env.filters["header_fmt"] = header_fmt

    t = env.get_template(template_name)
    latex = t.render(df=df,
                     sparse_header=get_sparse_labels(df.columns, transpose=False),
                     sparse_index=get_sparse_labels(df.index, transpose=True)
                )
    f = open(output_file, "w")
    print(latex, file=f)

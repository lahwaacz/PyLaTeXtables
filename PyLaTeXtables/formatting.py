#! /usr/bin/env python3

import os.path
import re
import decimal

try:
    import jinja2
except ImportError:
    raise ImportError("Please make sure that the python3-jinja2 package is installed.")

__all__ = ["get_column_types", "write_latex"]

def get_column_types(df, f="N", hide_nans=False):
    assert f in {"n", "N"}

    def count_places_before(d):
        if not d.is_finite():
            return 0 if hide_nans is True else len(str(d))
        t = d.as_tuple()
        return max(1, t.sign + len(t.digits) + t.exponent)

    def count_places_after(d):
        e = d.as_tuple().exponent
        if not isinstance(e, int):
            return 0  # NaN
        return max(0, -e)

    decimals = df.map(lambda v: decimal.Decimal(str(v)).normalize())
    places_before = decimals.map(count_places_before).apply(max)
    places_after = decimals.map(count_places_after).apply(max)

    column_types = []
    for before, after in zip(places_before, places_after):
        column_types.append(f + "{" + str(before) + "}{" + str(after) + "}")

    return " ".join(column_types), places_before, places_after

def _get_spans(sparse_labels):
    # calculate column/row spans
    spans = [i for i, label in enumerate(sparse_labels) if label]
    spans.append(len(sparse_labels))

    # difference between consecutive elements
    spans = [x - spans[i - 1] for i, x in enumerate(spans) if i > 0]

    sparse_spans = []
    popped = False
    for i in sparse_labels:
        if i:
            sparse_spans.append(spans.pop(0))
            popped = True
        elif popped:
            sparse_spans.append(0)
        else:
            # empty labels from the start get 1
            sparse_spans.append(1)

    return sparse_spans

def get_sparse_labels(multiindex, transpose=True):
    sparse_labels = [
        [value if (i == 0 or value != level[i - 1]) else '' for i, value in enumerate(level)]
        for level in zip(*multiindex.tolist())
    ] # Sparsify effect for multiindex
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

def write_latex(df, output_file, *, template_name="general.tex",
                header_dict=None, header_in_math=True,
                column_types=None, places_after=None, data_formats=None,
                index_column_types="r", vertical_multirow_cells=True,
                exp_low_threshold=0.25, exp_high_threshold=1000, hide_nans=False,
                sparsify_header=True, sparsify_index=True):
    if header_dict is None:
        header_dict = {}

    if column_types is None:
        column_types, _, places_after = get_column_types(df, hide_nans=hide_nans)
    assert index_column_types in ["l", "c", "r"]

    if sparsify_header is True:
        sparse_header = get_sparse_labels(df.columns, transpose=False)
    else:
        sparse_header = [[(c, 1) for c in df.columns]]
    if sparsify_index is True:
        sparse_index = get_sparse_labels(df.index, transpose=True)
    else:
        sparse_index = None

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
        if vertical_multirow_cells is True:
            value = vertical_text(value)
        return r"\multirow{" + str(span) + "}{*}{" + str(value) + "}"

    def _remove_zeros_from_exponent(fnum):
        if "e" in fnum:
            a, b = fnum.split("e")
            a += "e"
            if b == "-00" or b == "+00":
                return a + "0"
            elif b.startswith("-") or b.startswith("+"):
                a += b[0]
                b = b[1:]
            return a + b.lstrip("0")
        return fnum

    def np(value, digits=None, maybe_int=True, exponents=True):
        if str(value) == "nan":
            if hide_nans is True:
                return ""
            return str(value)
        if isinstance(value, int):
            return r"\np{" + str(int(value)) + "}"
        try:
            value = float(value)
            if maybe_int is True and value == int(value):
                return r"\np{" + str(int(value)) + "}"
            if exponents is True:
                if value < exp_low_threshold:
                    f = "e"
                elif value < exp_high_threshold:
                    f = "f"
                else:
                    f = "g"
            else:
                f = "f"
            if digits is None:
                fnum = r"\np{" + _remove_zeros_from_exponent("{:{}}".format(value, f)) + "}"
            else:
                fnum = r"\np{" + _remove_zeros_from_exponent("{:.0{}{}}".format(value, digits, f)) + "}"
            return fnum
        except ValueError:
            return str(value)

    def header_fmt(value):
        if value in header_dict:
            return header_dict[value]
        if "$" in value or header_in_math is False:
            return value
        if value:
            return "$ {} $".format(value)
        return ""

    def data_fmt(value, column):
        if places_after is None:
            return value
        if hide_nans is True and str(value) == "nan":
            return ""
        if data_formats is None:
            fmt = "{:.0{}f}"
        else:
            fmt = data_formats[column]
        fnum = fmt.format(value, places_after[column])
        return _remove_zeros_from_exponent(fnum)

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
            lstrip_blocks=True,
            loader=loader,
          )
    env.filters["escape_tex"] = escape_tex
    env.filters["vertical_text"] = vertical_text
    env.filters["multirow"] = multirow
    env.filters["np"] = np
    env.filters["header_fmt"] = header_fmt
    env.filters["data_fmt"] = data_fmt

    t = env.get_template(template_name)
    latex = t.render(df=df,
                     sparse_header=sparse_header,
                     sparse_index=sparse_index,
                     data_column_types=column_types,
                     index_column_types=index_column_types,
                )
    f = open(output_file, "w")
    print(latex, file=f)

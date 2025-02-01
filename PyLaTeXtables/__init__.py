#! /usr/bin/env python3

"""
Random reference links:

- http://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html
- http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_latex.html
- https://pypi.python.org/pypi/tabulate   (currently not used here)
- http://jinja.pocoo.org/docs/dev/api/
- http://jinja.pocoo.org/docs/dev/templates/
"""
import os

from .utils import *
from .formatting import *

import pandas

def make_table(filename, *, index_columns=1, transpose=False, **kwargs):
    parts = []

    # load data frame
    for df in utils.load_dataframes(filename):
        df = utils.cleanup_dataframe(df, index_columns=index_columns)
        
        if not df.empty:
            parts.append(df)

    # join the parts horizontally, use the same index
    df = pandas.concat(parts, axis=1).reindex(parts[0].index)

    if transpose is True:
        df = df.transpose()

    # output to LaTeX
    basename, ext = os.path.splitext(filename)
    basename = os.path.split(basename)[1]
    output_file = basename + ".tex"
    return write_latex(df, output_file, **kwargs)

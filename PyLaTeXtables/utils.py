#! /usr/bin/env python3

import os.path
import subprocess

try:
    import pandas
    pandas.set_option('display.max_columns', 100)
    pandas.set_option('display.max_rows', 200)
    pandas.set_option('display.width', 150)
except ImportError:
    raise ImportError("Please make sure that the python3-pandas package is installed.")

__all__ = ["load_dataframes", "build_header", "cleanup_dataframe"]

def load_dataframes(filename):
    basename, ext = os.path.splitext(filename)
    basename = os.path.split(basename)[1]
    if ext != ".csv":
        csv = basename + ".csv"
        # the FilterOptions set "\t" as delimiter and text quoting
        cmd = "unoconv -f csv -e FilterOptions='9,34,UNICODE,1' -o '{}' '{}'".format(csv, filename)
        subprocess.check_call(cmd, shell=True)
    else:
        csv = filename

    df = pandas.read_csv(csv,
                         delimiter="\t",
                         header=None,
                         na_values=["#DIV/0!", "Err:502"],
                         skip_blank_lines=False)

    # split on null rows
    null_rows = []              
    for i, row in df.iterrows():
        if row.isnull().all(): 
            null_rows.append(i)
    # ghost rows
    null_rows.insert(0, -1)
    null_rows.append(len(df))

    # yield the split parts
    for a, b in zip(null_rows[:-1], null_rows[1:]):
        if b - a > 1:
            yield df[a+1:b]

def build_header(df):
    header_rows = []
    for i, row in df.iterrows():
        # detect header rows: those that don't start with numbers
        value = row.get_values()[0]
        isnull = row.isnull().get_values()[0]
        try:
            float(value)
            isfloat = True
        except ValueError:
            isfloat = False
        if isfloat and not isnull:
            break

        header = []
        header_rows.append(header)

        # fill in missing header cells (left out in CSV due to spanning)
        prev = None
        for j, value in enumerate(row):
            if value and not pandas.isnull(value):
                prev = value
                header.append(value)
            elif prev:
                header.append(prev)
            else:
                header.append("")

    # transpose
    header_columns = list(zip(*header_rows))

    # drop header rows
    df = df[len(header_rows):]

    # set header
    df.columns = pandas.MultiIndex.from_tuples(header_columns)

    return df

def cleanup_dataframe(df, *, index_columns=1):
    # drop empty rows
    df = df.dropna(axis=0, how="all")
    # drop empty columns
    df = df.dropna(axis=1, how="all")

    # build header
    df = build_header(df)

    # skip empty dataframes (parts of the tables that contained only the header, no data)
    if df.empty:
        return df

    # explicitly convert strings to numbers
    # (this would not be necessary if we could use the 'header' parameter of pandas.read_csv)
    for col in df.columns:
        df[col] = pandas.to_numeric(df[col], errors="ignore")

    # set index
    # gotcha: DataFrame.set_index is completely incomprehensible for multiindexes,
    # so we need to cast the multiindex to list of tuples
    labels = list(df.columns[:index_columns])
    df = df.set_index(labels)

    # fix index column names (drop empty items from the tuple)
    names = []
    for label in labels:
        if isinstance(label, tuple):
            if label[:-1] == ("", ) * (index_columns - 2):
                label = label[-1]
        names.append(label)
    df.index = df.index.set_names(names)

    return df

#! /usr/bin/env python3

import os.path
import subprocess

try:
    import pandas
    pandas.set_option('display.max_columns', 100)
    pandas.set_option('display.max_rows', 200)
    pandas.set_option('display.width', 128)
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
                         na_values=["#DIV/0!", "Err:502", "#VALUE!"],
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
    def is_number(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def is_header_row(row):
        for value in row.values:
            if is_number(value) and not pandas.isnull(value):
                return False
        return True

    header_rows = []
    for i, row in df.iterrows():
        # detect header rows: those that don't contain any numbers
        if not is_header_row(row):
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

    # set index
    # gotcha: DataFrame.set_index is completely incomprehensible for multiindexes,
    # so we need to cast the multiindex to list of tuples
    labels = list(df.columns[:index_columns])
    df = df.set_index(labels)

    if index_columns > 1:
        # fill in missing index cells (left out in CSV due to spanning)
        index = list(df.index)
        index = [list(r) for r in index]
        for c in range(index_columns):
            prev = None
            for r in range(len(index)):
                value = index[r][c]
                if value and not pandas.isnull(value):
                    prev = value
                elif prev:
                    value = prev
                else:
                    value = ""
                index[r][c] = value
        # index has to be transposed for set_index
        index = list(map(list, zip(*index)))
        df = df.set_index(index)

    # fix index column names (drop empty items from the tuple)
    names = []
    for label in labels:
        if isinstance(label, tuple):
            if label[:-1] == ("", ) * (len(label) - 1):
                label = label[-1]
        names.append(label)
    df.index = df.index.set_names(names)

    # explicitly convert strings to numbers - should be done only after we assemble the header and index
    # Updated: Convert columns to numeric; invalid parsing is now set to NaN instead of being ignored.
    for col in df.columns:
        df[col] = pandas.to_numeric(df[col], errors="coerce")

    return df

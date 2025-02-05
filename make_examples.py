#! /usr/bin/env python3

import os.path
import math
import subprocess

import PyLaTeXtables as plt

import pandas

examples_dir = os.path.join(os.path.dirname(__file__), "examples")
#Updated HEADER_DICTIONARY to include 'level' and 'col_span' keys for each header.
    # This allows us to handle multi-level headers in eoc.tex or other LaTeX templates more cleanly.
HEADER_DICTIONARY = {
    "Index": {"level": 0, "text": r"$ h~[\textup{m}] $", "col_span": 1},  # Index header
    "dt": {"level": 0, "text": r"$ \tau~[\textup{s}] $", "col_span": 1},
    "DOF": {"level": 0, "text": r"$ N_{dof} $", "col_span": 1},
    "EOC 1": {"level": 0, "text": r"$ eoc_{S_n,1} $", "col_span": 1},
    "EOC 2": {"level": 0, "text": r"$ eoc_{S_n,2} $", "col_span": 1},
    "L1": {"level": 0, "text": r"$ \lVert E_{h,S_n} \rVert_1 $", "col_span": 1},
    "L2": {"level": 0, "text": r"$ \lVert E_{h,S_n} \rVert_2 $", "col_span": 1},
    "BC": {"level": 0, "text": r"{\footnotesize Brooks \& Corey}", "col_span": 1},
    "VG": {"level": 0, "text": r"{\footnotesize van Genuchten}", "col_span": 1},
}

def recalculate_eocs(df, norm_columns):
    for multiindex in df.columns:
        # skip non-norm columns
        if multiindex[-1] not in norm_columns:
            continue
        # calculate eoc for given norm
        eoc_multiindex = (*multiindex[:-1], multiindex[-1] + "_eoc")
        for i, norm in zip(df.index, df[multiindex]):
            # h is the second part of the index
            h = i[1]
            if i != df.index[0]:
                df.loc[prev_i, eoc_multiindex] = math.log( norm / prev_norm ) / math.log( h / prev_h )
            prev_i = i
            prev_h = h
            prev_norm = norm
        df.loc[i, eoc_multiindex] = None

def make_table(filename):
    filename = os.path.join(examples_dir, filename)
    basename, ext = os.path.splitext(filename)

    parts = []

    # load data frame
    for df in plt.load_dataframes(filename):
        df = plt.cleanup_dataframe(df, index_columns=3)

        if not df.empty:
            parts.append(df)

    # join the parts horizontally, use the same index
    df = pandas.concat(parts, axis=1)
    df = df.reindex(parts[0].index)

    # recalculate EOCs
    recalculate_eocs(df, ["S_L1", "S_L2"])

    # reorder BC and VG models below each other
    df = pandas.concat([df["BC"], df["VG"]], keys=["BC", "VG"])

    # output to LaTeX
    output_file = basename + ".tex"
    plt.write_latex(df, output_file, header_dict=HEADER_DICTIONARY, template_name="eoc.tex")

    # transposed variant
    df2 = df.transpose()
    df2 = pandas.concat([df2["BC"], df2["VG"]], keys=["BC", "VG"])
    output_file = basename + "_transposed.tex"
    plt.write_latex(df2, output_file, header_dict=HEADER_DICTIONARY, template_name="eoc.tex")


if __name__ == "__main__":
    for f in ["2d_grid.csv"]:
        make_table(f)

    # run pdflatex
    os.chdir(examples_dir)
    subprocess.run("pdflatex main.tex", shell=True, check=True)

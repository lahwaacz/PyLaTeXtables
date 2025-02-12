#! /usr/bin/env python3

import os.path
import math
import subprocess

import PyLaTeXtables as plt

import pandas

examples_dir = os.path.join(os.path.dirname(__file__), "examples")

HEADER_DICTIONARY = {
        "h": r"$ h~[\textup{m}] $",
        "dt": r"$ \tau~[\textup{s}] $",
        "DOF": r"$ N_{dof} $",
        "EOC 1": r"$ eoc_{S_n,1} $",
        "EOC 2": r"$ eoc_{S_n,2} $",
        "L1": r"$ \lVert E_{h,S_n} \rVert_1 $",
        "L2": r"$ \lVert E_{h,S_n} \rVert_2 $",
        "BC": r"{\footnotesize Brooks \& Corey}",
        "VG": r"{\footnotesize van Genuchten}",
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
    df = pandas.concat(parts, axis=1).reindex(parts[0].index)

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
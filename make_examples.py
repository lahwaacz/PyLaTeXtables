#! /usr/bin/env python3

import os.path
import math

import PyLaTeXtables as plt

import pandas

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
    parts = []

    # load data frame
    for df in plt.load_dataframes(filename):
        df = plt.cleanup_dataframe(df, index_columns=3)

        if not df.empty:
            parts.append(df)

    # join the parts horizontally, use the same index
    df = pandas.concat(parts, axis=1, join_axes=[parts[0].index])

    # recalculate EOCs
    recalculate_eocs(df, ["S_L1", "S_L2"])

    # reorder BC and VG models below each other
    df = pandas.concat([df["BC"], df["VG"]], keys=["BC", "VG"])

    # output to LaTeX
    basename, ext = os.path.splitext(filename)
    output_file = basename + ".tex"
    plt.write_latex(df, output_file, header_dict=HEADER_DICTIONARY)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: {} file_1.ods [file_2.ods ...]".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    for f in sys.argv[1:]:
        df = make_table(f)

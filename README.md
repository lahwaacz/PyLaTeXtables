# PyLaTeXtables

PyLaTeXtables is a Python library designed to simplify the creation of LaTeX tables from CSV files or pandas DataFrames.
It provides tools to format, clean, and convert tabular data into LaTeX-compatible tables, supporting hierarchical headers, multi-indexing, and custom formatting.

## Features

- **CSV to LaTeX Conversion**: Convert CSV files directly into LaTeX tables.
- **Pandas Integration**: Seamlessly work with pandas DataFrames.
- **Hierarchical Headers**: Support for multi-level headers in LaTeX tables.
- **Custom Formatting**: Apply custom formatting to table headers, indices, and data.
- **Template-Based Rendering**: Use Jinja2 templates for flexible LaTeX table generation.

## Installation

You can clone the repository and install it manually:

```bash
git clone https://github.com/yourusername/PyLaTeXtables.git
cd PyLaTeXtables
pip install .
```

# Usage

## Basic Usage

To convert a CSV file into a LaTeX table, you can use the `make_table` function from the PyLaTeXtables module:

```python
from PyLaTeXtables import make_table
# Convert a CSV file to a LaTeX table
make_table("example.csv", index_columns=1, transpose=False)
```

## Advanced Usage

You can also work directly with pandas DataFrames and customize the table output:

```python
import pandas as pd
from PyLaTeXtables import make_table

# Create a pandas DataFrame
data = {
    "Column1": [1, 2, 3],
    "Column2": [4, 5, 6],
}
df = pd.DataFrame(data)

# Convert the DataFrame to a LaTeX table
make_table(df, index_columns=1, transpose=True, header_dict={"Column1": "Header 1", "Column2": "Header 2"})
```

## Custom Templates

PyLaTeXtables supports custom Jinja2 templates for LaTeX table generation.
You can modify the provided templates (`eoc.tex` and `general.tex`) or create your own.

```python
from PyLaTeXtables import make_table

# Use a custom template for LaTeX table generation
make_table("example.csv", template_name="custom_template.tex")
```

## Project Structure

- `PyLaTeXtables/`: The main package containing the core functionality.
  - `templates/`: Contains Jinja2 templates for LaTeX table generation.
    - `eoc.tex`: Template for tables with specific formatting (e.g., EOC tables).
    - `general.tex`: General-purpose LaTeX table template.
  - `__init__.py`: Main module for table generation.
  - `formatting.py`: Handles custom formatting for LaTeX tables.
  - `utils.py`: Utility functions for loading and cleaning data.
- `make_examples.py`: Example script demonstrating how to use PyLaTeXtables.

## Dependencies

- jinja2: For template-based LaTeX table generation.
- pandas: For data manipulation and handling.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on the GitHub repository.

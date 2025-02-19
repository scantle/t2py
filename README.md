# T2Py
## Description
T2Py is a Python library for reading and writing files used by Texture2Par. It is in the process of being converted for handling the new file structure of Texture2Par v2.
This code is under active development and subject to change.

## Installation Using pip
```bash
pip install git+https://github.com/scantle/t2py.git@main
```

## Texture2Par v2 Usage Example
Below is a brief example of how to use the `Dataset` class in T2Py to create a Texture2Par input file:
```python
import pandas as pd
import t2py

# Example input file containing well lithology data
litho_file = "my_litho_data.csv"

# Read in data
litho = pd.read_csv(litho_file)

# Process, subset data as needed (not shown)
...

# Create and populate the Dataset
log = t2py.Dataset(classes=['Coarse'])
log.add_wells_by_df(df=litho,
                    name_col='WELL_INFO_ID',
                    zland_col='GROUND_SURFACE_ELEVATION_m',
                    depth_col='LITH_BOT_DEPTH_m',
                    depth_top_col='LITH_TOP_DEPTH_m')

# Can use multiple calls of .add_wells_by_df to add data from different sources!

# Write out the Texture2Par dataset file
log.write_file('litholog_coarse.dat')
```

### Dataset Class Overview:
The Dataset class is designed to help format your data into the structure required by Texture2Par v2.
- Multiple texture classes can be initialized during the initial creation of the `t2py.Dataset` object.
- Distinct wells (the "Well ID" column) are automatically identified based on the Well Name, X, and Y columns
- When `n_col` is none (default), the depth interval index column ("n") is calculated using the Well IDs and sorted interval depths.
- Missing depth intervals can identified and marked as `NA` when `depth_top_col` is passed (and `fill_missing` is `True` (default))
- The add_wells_by_df method reads well data from a pandas DataFrame, assigns IDs, and populates the Dataset's internal table.
- The write_file method saves the resulting table in a format compatible with Texture2Par.
- See [the `Dataset` class code](./t2py/dataset.py) for more documentation.

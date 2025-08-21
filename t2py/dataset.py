import numpy as np
import pandas as pd

class Dataset(object):
    """
    A class for reading, storing, and writing Datasets in the format required by Texture2Par v2.

    This Dataset object maintains a DataFrame (`self.df`) with columns describing wells and
    their associated data. Optionally, hydrostratigraphic units (HSUs) can also be tracked.

    Attributes:
        classes (list): A list of "classes" (e.g., lithology types) to include in the dataset.
        columns (list): Column names used in the dataset's underlying DataFrame.
        df (pd.DataFrame): The in-memory data table containing well/lithology information.
        max_id (int): Tracks the highest numeric well ID that has been assigned so far.
        nlay (int): Number of layers if HSUs are enabled (0 if none).
        hsu_columns (list): List of strings like ['hsu_1', 'hsu_2', ...] if HSUs are present.
        has_var (bool): If True, per-class measurement error variance columns are tracked and written
            as 'var_<class>' immediately after the class columns and before any HSU columns.
    """
    
    def __init__(self, classes: list, hsus: bool = False, nlay: int = 0, filename: str = None,
                 dataframe: pd.DataFrame = None, variance_col = False,
                 **kwargs):
        """
        Initialize the Dataset.

        Args:
            classes (list):
                A list of strings representing classes (e.g., lithology types) to be included
                as columns in this dataset.
            hsus (bool, optional):
                Whether to include hydrostratigraphic units (HSUs). Defaults to False.
            nlay (int, optional):
                The number of layers for HSUs. Required only if hsus=True. Defaults to 0.
            filename (str, optional):
                Path to a file to read data from. If provided, this will be loaded into `self.df`.
            dataframe (pd.DataFrame, optional):
                A pandas DataFrame to initialize `self.df` with. If both filename and dataframe
                are provided, filename takes precedence.
            variance_col (bool, optional):
                Whether a measurement error variance column will be included and written with the data
            **kwargs:
                Additional keyword arguments passed through to `read_file()`, e.g. custom separators.

        Raises:
            ValueError: If `hsus` is True but `nlay` is not > 0, indicating invalid usage.
        """
        # File Output Lines
        self.columns = ['Location', 'ID', 'n', 'X', 'Y', 'Zland', 'Depth']
        self.columns.extend(classes)
        self.has_var = variance_col
        if variance_col:
            var_cols = [f"var_{c}" for c in classes]
            self.columns.extend(var_cols)
        self.classes = classes
        self.max_id = 0

        if hsus:
            if nlay == 0:
                raise ValueError('nlay must be passed and > 0 if hsus are present.')
            self.nlay = nlay
            self.hsu_columns = [f'hsu_{layer}' for layer in range(1, nlay + 1)]
            self.columns.extend(self.hsu_columns)
        else:
            self.nlay = 0
            self.hsu_columns = []

        if filename is not None:
            self.df = self.read_file(filename, columns=self.columns, **kwargs)
            self.max_id = self.df['ID'].max() if not self.df.empty else 0
        elif dataframe is not None:
            self.df = dataframe
            self.max_id = self.df['ID'].max() if not self.df.empty else 0
        else:
            self.df = pd.DataFrame(columns=self.columns)

    @staticmethod
    def read_file(filename: str, columns: list, sep: str = '\t', na_values: list = ['-99', '-999']) -> pd.DataFrame:
        """
        Read a dataset file into a pandas DataFrame.

        The file is assumed to have no header row (header=None), and the first row
        is skipped (skiprows=1). Additional columns beyond the expected ones are ignored. If variance columns are
        included, be sure to instantiate the Dataset with `variance_col=True`.

        Args:
            filename (str):
                Path to the file to read.
            columns (list):
                A list of column names for the output DataFrame.
            sep (str, optional):
                Field delimiter for the file. Defaults to tab ('\\t').
            na_values (list, optional):
                A list of string values to interpret as missing/NaN. Defaults to ['-99', '-999'].

        Returns:
            pd.DataFrame: DataFrame containing the file contents with the specified columns.
        """
        return pd.read_csv(filename,
                           header=None,
                           skiprows=1,
                           sep=sep,
                           names=columns,
                           na_values=na_values,
                           usecols=range(0, len(columns)))

    def write_file(self, filename: str, sep: str = '\t', na_rep='-999', float_format='%.5f', header=None):
        """
        Writes the dataset to a file in a format compatible with Texture2Par.

        By default, the first row of column names is written (header=True). For HSUs, the column
        headers in the output file are replaced by numeric layer indices ('1', '2', etc.) rather
        than "hsu_1", "hsu_2", etc.

        Args:
            filename (str):
                Path to the output file to write.
            sep (str, optional):
                Field delimiter. Defaults to '\\t'.
            na_rep (str, optional):
                Representation for missing values. Defaults to '-999'.
            float_format (str, optional):
                String format for floating-point fields. Defaults to '%.5f'.
            header (bool, optional):
                Whether to write column headers. If None, defaults to True.
        """
        if header is None:
            header = True
        columns_to_write = self.columns[:]
        for i, hsu_col in enumerate(self.hsu_columns):
            columns_to_write[columns_to_write.index(hsu_col)] = str(i + 1)
        self.df.to_csv(filename,
                       sep=sep,
                       na_rep=na_rep,
                       header=header,
                       index=False,
                       columns=columns_to_write,
                       float_format=float_format)

    @property
    def well_coords(self):
        """
        A property that returns a subset of the DataFrame with unique well coordinates.

        Returns:
            pd.DataFrame or None: A DataFrame with columns ['ID', 'X', 'Y'], dropping duplicates.
            Returns None if self.df is None (i.e., uninitialized dataset).
        """
        if self.df is None:
            return None
        else:
            return self.df[['ID', 'X', 'Y']].drop_duplicates()

    def add_wells_by_df(self, df, name_col='Location', x_col='X', y_col='Y', zland_col='Zland',
                        depth_col='Depth', n_col=None, data_class_cols: dict = None,
                        var_class_cols: dict = None,
                        depth_top_col=None, fill_missing=True):
        """
        Add well data from an external DataFrame into the Dataset.

        This method:
            1. Verifies that all required columns are present in `df`.
            2. Handles assignment of well IDs (numeric) by grouping on (name_col, x_col, y_col).
            3. Creates a "point" index column (n_col) if not provided.
            4. Optionally fills in any gaps in depth intervals if both `depth_top_col` and
               `fill_missing=True` are supplied.

        Args:
            df (pd.DataFrame):
                DataFrame containing well/log data.
            name_col (str, optional):
                Column in `df` containing well name or identifier. Defaults to 'Location'.
            x_col (str, optional):
                Column in `df` for the X coordinate. Defaults to 'X'.
            y_col (str, optional):
                Column in `df` for the Y coordinate. Defaults to 'Y'.
            zland_col (str, optional):
                Column in `df` for land-surface elevation. Defaults to 'Zland'.
            depth_col (str, optional):
                Column in `df` for the bottom depth of an interval. Defaults to 'Depth'.
            n_col (str, optional):
                Column in `df` used as the "point index" along the well log. If not provided,
                a new column 'n' is created. Defaults to None.
            data_class_cols (dict, optional):
                A mapping of {class_name: column_in_df} that indicates which column holds data
                for each class in `self.classes`. If not provided, defaults to
                {class_name: class_name}. The function checks that each column exists in `df`.
            var_class_cols (dict, optional):
                Mapping {class_name: variance_column_in_df}. Only used if `variance_col=True`.
                If not provided, defaults to var_[class_name]. The function checks that each column exists in `df`.
            depth_top_col (str, optional):
                Column name for the top depth of an interval. If provided, we can fill the
                data gaps between intervals (by adding rows) if `fill_missing=True`.
                Defaults to None.
            fill_missing (bool, optional):
                Whether to fill in missing depth intervals if `depth_top_col` is set.
                Defaults to True.

        Raises:
            ValueError:
                If required columns (name_col, x_col, y_col, zland_col, depth_col) are missing
                from `df`.
            ValueError:
                If data_class_cols includes a key not in `self.classes`, or references a column
                not found in `df`.
            ValueError:
                If variance columns are expected and Var_class_cols includes a key not in `self.classes`,
                or references a column not found in `df`.
            ValueError:
                If HSUs are enabled (`self.nlay > 0`) but the corresponding HSU columns
                are not in `df`.
        """

        # Work on a copy
        df = df.copy()

        if name_col not in df.columns or x_col not in df.columns or y_col not in df.columns or zland_col not in df.columns or depth_col not in df.columns:
            raise ValueError('Missing necessary columns in dataframe.')

        if data_class_cols is None:
            data_class_cols = {key: key for key in self.classes}

        for key, col_name in data_class_cols.items():
            if key not in self.classes:
                raise ValueError(f'Invalid class {key}')
            if col_name not in df.columns:
                raise ValueError(f'Missing column for class {key}')

        # Handle variance columns, if using
        if self.has_var and var_class_cols is None:
            var_class_cols = {key: f'var_{key}' for key in self.classes}

        if self.has_var:
            for key, col_name in var_class_cols.items():
                if key not in self.classes:
                    raise ValueError(f'Invalid class {key} in argument var_class_cols')
                if col_name not in df.columns:
                    raise ValueError(f'Missing column for class measurement error (variance) {key}')

        if self.nlay > 0:
            for i in range(1, self.nlay + 1):
                hsu_col = f'hsu_{i}'
                if hsu_col not in df.columns:
                    raise ValueError(f'Missing column for {hsu_col}')

        # Get well rolling count
        df['ID'] = (~df[[name_col, x_col, y_col]].duplicated()).cumsum()
        # Get "point" index for each log
        if n_col is None:
            n_col = 'n'
            # Sort first, just in case
            df.sort_values(by=['ID', depth_col], ascending=[True, True], inplace=True)
            df[n_col] = df.groupby('ID').cumcount() + 1
        print(f"Adding {df.shape[0]} entries from {df['ID'].max()} wells ({df[name_col].unique().shape[0]} unique names)")

        if depth_top_col is not None and fill_missing:
            print("Filling interval gaps...")
            # Store new rows in a list initially
            new_rows_list = []

            grouped = df.groupby('ID')
            for name, group in grouped:
                group = group.sort_values(by=depth_col)
                previous_depth = 0.0  # Start with ground surface

                for i in range(len(group)):
                    current_top = group.iloc[i][depth_top_col]

                    if current_top > previous_depth:
                        new_row = group.iloc[i].copy()
                        new_row[depth_col] = current_top
                        new_row[depth_top_col] = previous_depth
                        for key, col_name in data_class_cols.items():
                            new_row[col_name] = np.nan
                        new_rows_list.append(new_row)

                    previous_depth = group.iloc[i][depth_col]

            # Convert the list of new rows to a DataFrame and concatenate with original df
            if new_rows_list:
                new_rows_df = pd.DataFrame(new_rows_list)
                df = pd.concat([df, new_rows_df], ignore_index=True)

            # Fix n column
            df.sort_values(by=['ID', depth_col], ascending=[True, True], inplace=True)
            df[n_col] = df.groupby('ID').cumcount() + 1

        pdf = pd.DataFrame(
            {'Location': df[name_col],
             'ID': self.max_id + df['ID'],  # Add in current dataset max
             'n': df[n_col],
             'X': df[x_col],
             'Y': df[y_col],
             'Zland': df[zland_col],
             'Depth': df[depth_col]
             })

        for key, col_name in data_class_cols.items():
            pdf[key] = df[col_name]

        if self.has_var:
            for key, col_name in var_class_cols.items():
                pdf[f'var_{key}'] = df[col_name]

        if self.nlay > 0:
            for i in range(1, self.nlay + 1):
                hsu_col = f'hsu_{i}'
                pdf[hsu_col] = df[hsu_col]

        # Append
        oldmax = self.max_id
        self.df = pd.concat([self.df, pdf], axis=0, copy=False)
        self.max_id = self.df['ID'].max()  # Update the maximum ID used
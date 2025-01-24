import numpy as np
import pandas as pd

class Dataset(object):

    def __init__(self, classes: list, hsus: bool = False, nlay: int = 0, filename: str = None,
                 dataframe: pd.DataFrame = None,
                 **kwargs):
        # File Output Lines
        self.columns = ['Location', 'ID', 'n', 'X', 'Y', 'Zland', 'Depth']
        self.columns.extend(classes)
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
    def read_file(filename: str, columns: list, sep: str = '\t', na_values: list = ['-99', '-999']):
        return pd.read_csv(filename,
                           header=None,
                           skiprows=1,
                           sep=sep,
                           names=columns,
                           na_values=na_values,
                           usecols=range(0, len(columns)))

    def write_file(self, filename: str, sep: str = '\t', na_rep='-999', float_format='%.5f', header=None):
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
        if self.df is None:
            return None
        else:
            return self.df[['ID', 'X', 'Y']].drop_duplicates()

    def add_wells_by_df(self, df, name_col='Name', x_col='X', y_col='Y', zland_col='Zland',
                        depth_col='Depth', n_col=None, data_class_cols: dict = None,
                        depth_top_col=None, fill_missing=True):
        if name_col not in df.columns or x_col not in df.columns or y_col not in df.columns or zland_col not in df.columns or depth_col not in df.columns:
            raise ValueError('Missing necessary columns in dataframe.')

        if data_class_cols is None:
            data_class_cols = {key: key for key in self.classes}

        for key, col_name in data_class_cols.items():
            if key not in self.classes:
                raise ValueError(f'Invalid class {key}')
            if col_name not in df.columns:
                raise ValueError(f'Missing column for class {key}')

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

        if self.nlay > 0:
            for i in range(1, self.nlay + 1):
                hsu_col = f'hsu_{i}'
                pdf[hsu_col] = df[hsu_col]

        # Append
        oldmax = self.max_id
        self.df = pd.concat([self.df, pdf], axis=0, copy=False)
        self.max_id = self.df['ID'].max()  # Update the maximum ID used
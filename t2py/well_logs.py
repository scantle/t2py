import numpy as np
import pandas as pd

# TODO Implement Geozones

class WellLogFile(object):

    def __init__(self, geozones: bool = False, nlay: int = 0, filename: str = None, dataframe: pd.DataFrame = None,
                 **kwargs):
        # File Output Lines
        self.columns = ['WellName', 'Well', 'Point', 'PC', 'X', 'Y', 'Zland', 'Depth']

        if geozones:
            if nlay == 0:
                raise ValueError('nlay must be passed and > 0 if geozones are present.')
            self.columns.extend(range(1, nlay+1))

        if filename is not None:
            self.df = self.read_file(filename, columns=self.columns, **kwargs)
        elif dataframe is not None:
            self.df = dataframe
        else:
            self.df = pd.DataFrame(columns=['WellName', 'Well', 'Point', 'PC', 'X', 'Y', 'Zland', 'Depth'])

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
        self.df.to_csv(filename,
                       sep=sep,
                       na_rep=na_rep,
                       header=header,
                       index=False,
                       columns=self.columns,
                       float_format=float_format)

    @property
    def well_coords(self):
        if self.df is None:
            return None
        else:
            return self.df[['Well', 'X', 'Y']].drop_duplicates()

    def add_well(self, well_name: str, well_x: float, well_y: float, well_z: float, pc: list, depth: list,
                 geozones:list = None):
        # Error handling
        if len(pc) != len(depth):
            raise ValueError('PC and Depth lists must be the same length.')
        if (1 in self.columns) and geozones is None:
            raise ValueError('Geozones in file - must be included in ')

        lastwell = self.df.Well.max()
        if np.isnan(lastwell): lastwell = 0

        npoints = len(pc)
        well_df = pd.DataFrame(
                  {'WellName': [well_name] * npoints,
                   'Well': [lastwell + 1] * npoints,
                   'Point': np.arange(1, npoints + 1),
                   'PC': pc,
                   'X': [well_x] * npoints,
                   'Y': [well_y] * npoints,
                   'Zland': [well_z] * npoints,
                   'Depth': depth
                   })
        # Append
        self.df = pd.concat([self.df, well_df], axis=0, copy=False)

    def add_wells_by_df(self, df, name_col='Name', data_col='PC', x_col='X', y_col='Y', zland_col='Zland',
                        depth_col='Depth', point_col=None):
        # Get well rolling count
        df['ID'] = (~df[[name_col, x_col, y_col]].duplicated()).cumsum()
        # Get "point" index for each log
        if point_col is None:
            point_col = 'Point'
            # Sort first, just in case
            df.sort_values(by=['ID', depth_col], ascending=[True, True], inplace=True)
            df[point_col] = df.groupby('ID').cumcount() + 1
        well_df = pd.DataFrame(
                  {'WellName': df[name_col],
                   'Well': df['ID'],
                   'Point': df[point_col],
                   'PC': df[data_col],
                   'X': df[x_col],
                   'Y': df[y_col],
                   'Zland': df[zland_col],
                   'Depth': df[depth_col]
                   })
        # Append
        self.df = pd.concat([self.df, well_df], axis=0, copy=False)

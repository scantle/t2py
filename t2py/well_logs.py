import pandas
import pandas as pd

# TODO Implement Geozones

class WellLogFile(object):
    # File Output Lines
    columns = ['WellName', 'Well', 'Point', 'PC', 'X', 'Y', 'Zland', 'Depth']

    def __init__(self, geozones: bool = False, nlay: int = 0, filename: str = None, dataframe: pandas.DataFrame = None,
                 **kwargs):

        if geozones:
            raise NotImplementedError('Geologic Zones Unimplemented. Contact Developer: leland@scantle.com')

        if filename is not None:
            self.df = self.read_file(filename, **kwargs)
        elif dataframe is not None:
            self.df = dataframe
        else:
            self.df = None

    @staticmethod
    def read_file(filename: str, sep: str ='\t'):
        return pd.read_csv(filename, sep=sep)

    def write_file(self, filename: str, sep: str = '\t'):
        self.df.to_csv(filename, sep=sep, na_rep='-99', header=True, index=False, float_format='%.5s',
                       columns=self.columns)

    @property
    def well_coords(self):
        if self.df is None:
            return None
        else:
            return self.df[['Well', 'X', 'Y']].drop_duplicates()

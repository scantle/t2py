from .pilot_points import PilotPoint

class InputFile(object):
    # File Output Lines
    header_line = '*' + '=' * 79 + '\n'
    divider = '*' + '-' * 79 + '\n'
    header_text = 'Texture2Par Input File  |  Written by t2py'
    sections = ['Model Settings ({})', 'Program Settings (True/False)', 'Variogram Settings',
                'Global Settings',
                'Pilot Points - X  Y  KCMin  deltaKC  KFMin  deltaKF  SsC  SsF  SyC  SyF  AnisoC  AnisoF  Zone',
                'Aquitard Pilot Points - X  Y  KCMin  deltaKC  KFMin  deltaKF  AnisoC  AnisoF  Zone']

    def __init__(self, well_log_file, hydrogeo_unit_file,
                 sim_file=None, preproc_file=None,
                 template_file=None, pp_zone=None,
                 xoff=0.0, yoff=0.0, rotation=0.0,
                 full_output=False, variogram_type=1,
                 sill=1.0, range_max=1E7, range_min=1E7,
                 anistropy=0.0, nugget=0.0, nkrige_wells=16,
                 KCk=0.007, KFk=0.0099, KHp=0.93, KVp=-0.62, Syp=1.0,
                 verbose=True):
        self.well_log_file = well_log_file
        self.unit_file = hydrogeo_unit_file
        self.sim_file = sim_file
        self.preproc_file = preproc_file
        self.template_file = template_file
        self.pp_zone = pp_zone
        self.xoff = xoff
        self.yoff = yoff
        self.rotation = rotation
        self.full_output = full_output
        self.variogram_type = variogram_type
        self.sill = sill
        self.range_max = range_max
        self.range_min = range_min
        self.anistropy = anistropy
        self.nugget = nugget
        self.nkrige_wells = nkrige_wells
        self.KCk = KCk
        self.KFk = KFk
        self.KHp = KHp
        self.KVp = KVp
        self.Syp = Syp

        # TODO pass to pilot points, or equivalent (?)
        self.float_precision ='%.4f'
        self.sci_precision = '%.4e'

        # Detect model type
        if self.sim_file.split('.')[-1] == 'nam':
            self.modeltype = 'MODFLOW'
        else:
            self.modeltype = 'IWFM'
            if self.preproc_file is None:
                raise ValueError('Pre-processor file cannot be None for IWFM')
        if verbose:
            print(f'Detected Model Type is: {self.modeltype}')

        # Initialize
        self.aquifer_pp = []
        self.aquitard_pp = []

        self.parameters = ['sill', 'range_max', 'range_min', 'anisotropy', 'nugget', 'nkrige_wells',
                           'KCk', 'KFk', 'KHp', 'KVp', 'Syp']
        self.custom_parameter_names = self.parameters
        self.parameters_estimate = [False] * len(self.parameters)


    def add_pilot_point(self, x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        SsC, SsF,
                        SyC, SyF,
                        AnisoC, AnisoF,
                        Zone=1, aquitard=False):
        if not aquitard:
            self.aquifer_pp.append(PilotPoint(x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        SsC, SsF,
                        SyC, SyF,
                        AnisoC, AnisoF,
                        Zone))
        else:
            self.aquitard_pp.append(PilotPoint(x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        SsC=None, SsF=None,
                        SyC=None, SyF=None,
                        AnisoC=AnisoC, AnisoF=AnisoF,
                        Zone=Zone))

    def add_aquitard_pilot_point(self, x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        AnisoC, AnisoF,
                        Zone=1):
        self.add_pilot_point(x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        SsC=None, SsF=None,
                        SyC=None, SyF=None,
                        AnisoC=AnisoC, AnisoF=AnisoF,
                        Zone=Zone, aquitard=True)

    def _write_section_header(self, f, section_id, extra=None):
        f.write(self.divider)
        f.write('* ' + self.sections[section_id].format(extra) + '\n')
        f.write(self.divider)

    def _write_value(self, f, value, number_format='%s', description=None, name='',
                     template_file=False, p_delimiter='$'):
        # default
        line = ' ' + number_format % value
        # change if template file & parameter is ON
        if template_file:
            if self.parameters_estimate[self.parameters.index(name)]:
                use_name = self.custom_parameter_names[self.parameters.index(name)]
                line = f'{p_delimiter} {use_name:12s} {p_delimiter}'
        pad_len = 40 - len(line)  # TODO error handling
        line += ' ' * pad_len
        f.write(f'{line}/ {description}\n')

    @staticmethod
    def _write_string(f, string, description=None):
        line = ' ' + string
        pad_len = 40 - len(line)  # TODO error handling
        line += ' ' * pad_len
        f.write(f'{line}/ {description}\n')

    def get_pnames(self):
        print('Available Parameters:', ', '.join(self.parameters))

    def get_est_parameters(self):
        p_est_list = [self.parameters[i] for i in range(0, len(self.parameters)) if self.parameters_estimate[i]]
        print('Parameters set to estimation: ', ', '.join(p_est_list))

    def set_est_parameters(self, pnames):
        for name in pnames:
            self.parameters_estimate[self.parameters.index(name)] = True

    def set_pp_est_parameters(self, pnames, aquitard=False):
        if not aquitard:
            for pp in self.aquifer_pp:
                pp.set_est_parameters(pnames)
        elif aquitard:
            for pp in self.aquitard_pp:
                pp.set_est_parameters(pnames)

    @property
    def npilot_points(self):
        return len(self.aquifer_pp), len(self.aquitard_pp)

    def write_file(self, filename='Texture2Par.in', template_file=False, p_delimiter="$"):
        with open(filename, 'w') as f:
            if template_file:
                f.write(f'ptf {p_delimiter}\n')
            # Primary Settings
            f.write(self.header_line)
            f.write('* ' + self.header_text + '\n')
            f.write(self.header_line)
            self._write_string(f, self.modeltype, 'Model Type')
            self._write_string(f, self.well_log_file, 'Well Log File')
            self._write_string(f, self.unit_file, 'Hydrogeologic Units File')
            # Model settings
            self._write_section_header(f, 0, self.modeltype)
            if self.modeltype == 'IWFM':
                self._write_string(f, self.sim_file, 'Simulation File')
                self._write_string(f, self.preproc_file, 'Pre-processor File')
                self._write_string(f, self.template_file, 'GW Template File')
                self._write_string(f, self.pp_zone, 'Pilot Point Node Zones File')
                interp_point_string = 'Node'
            elif self.modeltype == 'MODFLOW':
                self._write_string(f, self.sim_file, 'Name File')
                self._write_string(f, self.template_file, 'Layer Parameter Template File')
                self._write_string(f, self.pp_zone, 'Pilot Point Node Zones File')
                self._write_value(f, self.xoff, self.float_precision, 'xOffset')
                self._write_value(f, self.yoff, self.float_precision, 'yOffset')
                self._write_value(f, self.rotation, self.float_precision, 'Rotation')
                interp_point_string = 'Cell'
            # Program Settings
            self._write_section_header(f, 1)
            self._write_string(f, str(self.full_output), f'Output {interp_point_string} Files')
            # Variogram Settings
            self._write_section_header(f, 2)
            self._write_value(f, self.variogram_type, description='Variogram Type (itype)')
            self._write_value(f, self.sill, self.float_precision, 'Sill', 'sill', template_file, p_delimiter)
            self._write_value(f, self.range_max, self.sci_precision, '[Maximum] Range',
                              'range_max', template_file, p_delimiter)
            self._write_value(f, self.range_min, self.sci_precision, 'Minimum Range',
                              'range_min', template_file, p_delimiter)
            self._write_value(f, self.anistropy, self.float_precision, 'Anisotropy Angle (from North)',
                              'anisotropy', template_file, p_delimiter)
            self._write_value(f, self.nugget, self.float_precision, 'Nugget', 'nugget', template_file, p_delimiter)
            self._write_value(f, self.nkrige_wells, '%d', '[Maximum] Wells used in kriging',
                              'nkrige_wells', template_file, p_delimiter)
            # Global Settings
            self._write_section_header(f, 3)
            # TODO How to handle PEST compatibility? Separate write functions? Currently: str format
            # Should these be more descriptive?
            self._write_value(f, self.KCk, self.float_precision, 'KCk', 'KCk', template_file, p_delimiter)
            self._write_value(f, self.KFk, self.float_precision, 'KFk', 'KFk', template_file, p_delimiter)
            self._write_value(f, self.KHp, self.float_precision, 'KHp', 'KHp', template_file, p_delimiter)
            self._write_value(f, self.KVp, self.float_precision, 'KVp', 'KVp', template_file, p_delimiter)
            self._write_value(f, self.Syp, self.float_precision, 'Syp', 'Syp', template_file, p_delimiter)
            # Aquifer Pilot Points
            self._write_section_header(f, 4)
            for i, pp in enumerate(self.aquifer_pp):
                if not template_file:
                    pp.write_line(f)
                elif template_file:
                    pp.write_template_line(f, index=i, p_delimiter=p_delimiter)
            # Aquitard Pilot Points
            self._write_section_header(f, 5)
            for pp in self.aquitard_pp:
                if not template_file:
                    pp.write_line(f)
                elif template_file:
                    pp.write_template_line(f, index=i, template_file=template_file, p_delimiter=p_delimiter)
            # EOF
            f.write(self.divider)
            f.write('* EOF\n')

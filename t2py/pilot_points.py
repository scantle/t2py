
class PilotPoint(object):

    float_format = '{:.2f}'
    sci_format = '{:.3e}'
    int_format = '{:d}'
    str_format = '{:16s}'


    def __init__(self, x, y,
                        KCMin, deltaKC,
                        KFMin, deltaKF,
                        SsC, SsF,
                        SyC, SyF,
                        AnisoC=10.0, AnisoF=10.0,
                        Zone=1):
        self.x = x
        self.y = y
        self.KCMin = KCMin
        self.deltaKC = deltaKC
        self.KFMin = KFMin
        self.deltaKF = deltaKF
        self.SsC = SsC
        self.SsF = SsF
        self.SyC = SyC
        self.SyF = SyF
        self.AnisoC = AnisoC
        self.AnisoF = AnisoF
        self.Zone = Zone

        # Initialize
        self.parameters = ['KCMin', 'deltaKC', 'KFMin', 'deltaKF', 'SsC', 'SsF', 'SyC', 'SyF', 'AnisoC', 'AnisoF']
        self.def_format = [self.float_format]*6 + [self.sci_format]*4 + [self.float_format]*2 + [self.int_format]
        self.custom_parameter_names = self.parameters
        self.parameters_estimate = [False] * len(self.parameters)
        self.values = [self.x, self.y, self.KCMin, self.deltaKC, self.KFMin, self.deltaKF, self.SsC,
                       self.SsF, self.SyC, self.SyF, self.AnisoC, self.AnisoF, self.Zone]

    def write_line(self, f):
        fmt_string = ' '.join(self.def_format) + '\n'

        f.write(fmt_string.format(*self.values))

    def write_template_line(self, f, index, index_fmt='%0.2d', p_delimiter="$"):
        fmt_string = self.def_format
        temp_values = self.values
        for i, p in enumerate(self.custom_parameter_names):
            if self.parameters_estimate[i]:
                fmt_string[3 + i] = '{:s}'
                pstring = f'{self.custom_parameter_names[i]}_{index_fmt % index}'
                temp_values[3+i] = f'{p_delimiter} {pstring:12s} {p_delimiter}'
        fmt_string = ' '.join(fmt_string) + '\n'
        f.write(fmt_string.format(*temp_values))

    def get_pnames(self):
        print('Available Parameters:', ', '.join(self.parameters))

    def get_est_parameters(self):
        p_est_list = [self.parameters[i] for i in range(0, len(self.parameters)) if self.parameters_estimate[i]]
        print('Parameters set to estimation: ', ', '.join(p_est_list))

    def set_est_parameters(self, pnames):
        for name in pnames:
            self.parameters_estimate[self.parameters.index(name)] = True


class AquitardPilotPoint(PilotPoint):
    def __init__(self, x, y, KCMin, deltaKC, KFMin, deltaKF,
                        AnisoC=10.0, AnisoF=10.0,
                        Zone=1):
        # No storage parameters for aquitard
        SsC = None
        SsF = None
        SyC = None
        SyF = None

        super().__init__(x, y, KCMin, deltaKC, KFMin, deltaKF, SsC, SsF, SyC, SyF,
                        AnisoC, AnisoF, Zone)

        # Initialize
        self.parameters = ['KCMin', 'deltaKC', 'KFMin', 'deltaKF', 'AnisoC', 'AnisoF']
        self.def_format = [self.float_format]*8 + [self.int_format]
        self.custom_parameter_names = self.parameters
        self.parameters_estimate = [False] * len(self.parameters)
        self.values = [self.x, self.y, self.KCMin, self.deltaKC, self.KFMin, self.deltaKF,
                       self.AnisoC, self.AnisoF, self.Zone]
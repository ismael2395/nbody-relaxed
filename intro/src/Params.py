import numpy as np


# functions to get derived quantities.
def get_phi_l(cat):
    return np.arccos(
        ((cat['A[x]'] * cat['Jx'] + cat['A[y]'] * cat['Jy'] + cat['A[z]'] * cat['Jz'])
         /
         (np.sqrt(cat['A[x]'] ** 2 + cat['A[y]'] ** 2 + cat['A[z]'] ** 2) * np.sqrt(
             cat['Jx'] ** 2 + cat['Jy'] ** 2 + cat['Jz'] ** 2))
         )
    )


# only includes params we actually care about and we include in our table.
info_params = {
    # fundamental quantities in the catalog.
    # The key is the actual way to access the catalog.
    'mvir': (None, 'Msun/h',  'h^{-1} \\, M_{\\odot}', 'M_{\\rm vir}'),
    'rvir': (None, 'kpc/h', 'h^{-1} \\, kpc', 'R_{\\rm vir}'),
    'rs': (None, 'kpc/h', 'h^{-1} \\, kpc', 'R_{\\rm vir}'),
    'Xoff': (None, 'kpc/h', 'h^{-1} \\, kpc', 'X_{\\rm off}'),
    'Voff': (None, 'km/s', 'km \\, s^{-1}', 'V_{\\rm off}'),
    'vrms': (None, 'km/s', 'km \\, s^{-1}', 'V_{\\rm rms}'),
    'Acc_Rate_1*Tdyn': (None, 'Msun/h/yr', 'h^{-1}\\, yr^{-1} \\, M_{\\odot}', '\\alpha_{\\tau_{\\rm dyn}}'),
    'Acc_Rate_Inst': (None, 'Msun/h/yr', 'h^{-1}\\, yr^{-1} \\, M_{\\odot}', '\\alpha_{\\rm inst}'),

    'T/|U|': (None, '', '', 'T/|U|'),
    'Spin': (None, '', '', '\\lambda'),
    'scale_of_last_MM': (None, '', '', '\\delta_{\\rm MM}'),

    # derived quantities.
    'tdyn': (lambda cat: np.sqrt(2) * cat['rvir'] / cat['vrms'], 'kpc/h / km/s', '', '\\tau_{\\rm dyn}'),  # see notesheet.
    'cvir': (lambda cat: cat['rvir'] / cat['rs'], '', '', 'c_{\\rm vir}'),
    'q': (lambda cat: (1/2)*(cat['b_to_a'] + cat['c_to_a']), '', '', 'q'),
    'phi_l': (get_phi_l, '', '', '\\Phi_{l}'),
    'xoff': (lambda cat: cat['Xoff']/cat['rvir'], '', '', 'x_{\\rm off}'),
    'voff': (lambda cat: cat['Voff']/cat['vrms'], '', '', 'v_{\\rm off}'),
}

# nicer format.
params_dict = {
    key: {'derive': value[0], 'units': value[1], 'latex_units': value[2], 'latex_param': value[3]}
    for (key, value) in info_params.items()
}


class Param(object):

    # ToDo: Add filters to select only a range of values to return.
    def __init__(self, key, log=False):
        """

        :param key: is the actual string used to access the corresponding parameter from the catalogue.
        :param log:
        """
        self.key = key
        self.latex_param = params_dict[key]['latex_param']
        self.latex_units = params_dict[key]['latex_units']
        self.units = params_dict[key]['units']
        self.derive = params_dict[key]['derive']
        self.log = log

        self.text = self.get_text()
        self.values = None

    def get_values(self, cat):
        if self.values is not None:
            return self.values

        # ToDo: add option to check whether catalog has that entry and just fetch from there
        #  (catalog will be a class with option to add new entries, and maybe rewrite to disk that new way)
        if self.derive is None:
            values = cat[self.key]
        else:
            values = self.derive(cat)

        if self.log:
            values = np.log(values)

        return values

    def set_values(self, cat):
        self.values = self.get_values(cat)

    def get_text(self):
        """
        Obtain the text that will be used in the produce_plots.
        :return:
        """
        template = '${}{}{}$'
        log_tex = ''

        units_tex = '\\; [{}]'.format(self.latex_units)
        if self.log:
            log_tex = '\\log_{10}'
            units_text = ''

        return template.format(log_tex, self.latex_param, units_tex)




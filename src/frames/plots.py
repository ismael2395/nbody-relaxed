"""
This file contains classes that represent the different plots that are produced. The purpose is to have more
reproducible plots and separate the plotting procedure from the images produced.
"""
import matplotlib.pyplot as plt
from src.utils import const
import numpy as np


class Plot(object):

    def __init__(self, params, nrows=1, ncols=1, figsize=(8, 8), title='', title_size=20, tick_size=24):
        """
        Represents a single plot to draw and produce. Each plot will be outputted in a single page of a pdf.

        * To overlay a different plot (say relaxed), just call self.run() again w/ the relaxed catalog and color!
        :param params: Represents a list of :class:`Param`:, could be tuples of params too depending on the plot_func.
        """

        self.title = title
        self.title_size = title_size
        self.tick_size = tick_size

        self.params = params
        self.fig, axs = plt.subplots(nrows, ncols, figsize=figsize)
        if nrows > 1 or ncols > 1:
            self.axes = axs.flatten()
        else:
            self.axes = [axs]

    def generate(self, *args, **kwargs):
        """
        Produce the plot and save into the axes objects.
        :return: None
        """
        self.preamble()
        self.run(*args, **kwargs)
        self.finale()

    def preamble(self):
        self.fig.suptitle(self.title, fontsize=self.title_size)
        plt.ioff()

    def finale(self):

        for ax in self.axes:
            ax.tick_params(axis='both', which='major', labelsize=self.tick_size)

        self.fig.tight_layout()

    def run(self, *args, **kwargs):
        pass

    def save(self, fname=None, pdf=None):
        plt.rc("text", usetex=True)

        if fname is not None:
            self.fig.savefig(const.figure_path.joinpath(fname))

        elif pdf is not None:
            pdf.savefig(self.fig)

        else:
            raise ValueError("Need to specify either a filename or a pdf")


# ToDo: Change to accommodate reading chunkified code.
class BiPlot(Plot):
    """
    Class that creates the standard x vs. y plots.
    """

    def __init__(self, plot_func, *args, **kwargs):
        self.plot_func = plot_func
        super(BiPlot, self).__init__(*args, **kwargs)

    def run(self, cat, **kwargs):
        for (ax, param_pair) in zip(self.axes, self.params):
            param1, param2 = param_pair
            self.plot_func(cat, param1, param2, ax, xlabel=param1.text, ylabel=param2.text,
                           **kwargs)


class UniPlot(Plot):
    """
    Creates plot that only depend on one variable at a time, like histograms.
    """

    def __init__(self, plot_func, *args, **kwargs):
        self.plot_func = plot_func
        super(UniPlot, self).__init__(*args, **kwargs)

    def run(self, cat, **kwargs):
        for (ax, param) in zip(self.axes, self.params):
            self.plot_func(cat, param, ax, xlabel=param.text,
                           **kwargs)


class MatrixPlot(Plot):

    def __init__(self, matrix_func, *args, symmetric=False, **kwargs):
        """

        :param matrix_func: A function that returns a matrix of shape len(self.params) x len(self.params).
        :param args:
        """
        self.matrix_func = matrix_func
        self.symmetric = symmetric
        super(MatrixPlot, self).__init__(*args, ncols=1, nrows=1, **kwargs)
        self.ax = self.axes[0]

    def run(self, label_size=16, **kwargs):
        matrix_values = self.matrix_func(self.params)
        mask = np.tri(matrix_values.shape[0], k=-1) if self.symmetric else None
        a = np.ma.array(matrix_values, mask=mask)
        im = self.ax.matshow(a, cmap='bwr', vmin=-1, vmax=1)
        plt.colorbar(im, ax=self.ax)

        latex_params = [param.latex_param for param in self.params]
        self.ax.set_xticklabels([''] + latex_params, size=label_size)
        self.ax.set_yticklabels([''] + latex_params, size=label_size)

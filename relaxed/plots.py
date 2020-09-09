"""This file contains classes that represent the different plots that are produced. The purpose
is to have more reproducible plots and separate the plotting procedure from the images produced.

The parent class 'Plot' only works on the 'high-level', never interacting with the axes objects
directly other than setting them up nad passing them along. The rest is up to plot_funcs.py

It also rounds up all parameter values to be plotted from multiple catalogs and their
corresponding labels.
"""
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np

from relaxed import utils
from . import plot_funcs


class Plot(ABC):
    def __init__(
        self,
        plot_func,
        hparams,
        colors=("r", "b", "g"),
        nrows=1,
        ncols=1,
        figsize=(8, 8),
        title="",
        title_size=20,
        grid_locs=None,
    ):
        """Represents a single plot to draw and produce. Each plot will be outputted
        in a single page of a pdf.

        hparams (list) : A list containing all (unique) halo params necessary for plotting.
        colors (list) : A list of colors to be used when plotting multiple catalogs.
        """

        self.title = title
        self.title_size = title_size
        self.colors = colors

        self.plot_func = plot_func
        self.hparams = hparams
        self.hparam_dict = {hparam.name: hparam for hparam in self.hparams}
        assert len(self.hparam_dict) == len(self.hparams)

        self.nrows = nrows
        self.ncols = ncols

        self.values = {}

        self._setup_fig_and_axes(grid_locs, figsize)

    def _setup_fig_and_axes(self, grid_locs, figsize):
        # mainly setup grids for plotting multiple axes.

        plt.ioff()

        if not grid_locs:
            # just plot sequentially if locations were not specified.
            self.grid_locs = [
                (i, j) for i in range(self.nrows) for j in range(self.ncols)
            ]
        self.fig, _ = plt.subplots(squeeze=False, figsize=figsize)
        self.axes = [
            plt.subplot2grid((self.nrows, self.ncols), param_loc, fig=self.fig)
            for param_loc in self.grid_locs
        ]

        self.fig.suptitle(self.title, fontsize=self.title_size)
        self.fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    def save(self, fname=None, pdf=None):
        assert fname or pdf, "one should be specified"
        plt.rc("text", usetex=True)

        if fname:
            self.fig.savefig(utils.figure_path.joinpath(fname))

        else:
            pdf.savefig(self.fig)

    def load(self, hcat):
        """Load the parameter values that will be used for plotting."""
        assert hcat.name not in self.values, "Cat already loaded."
        values_i = {}
        for hparam in self.hparams:
            values_i[hparam.name] = hparam.get_values(hcat.cat)
        self.values[hcat.name] = values_i

    @abstractmethod
    def generate(self, plot_params, **plot_kwargs):
        """
        Produce the plot and save into the axes objects. Uses the cached parameters from load
        method.
        :return: None
        """
        pass


class UniPlot(Plot):
    """Creates plot that only depend on one variable at a time, like histograms."""

    def generate(self, plot_params, **plot_kwargs):
        for cat_name in self.values:
            for (ax, param) in zip(self.axes, plot_params):
                hparam = self.hparam_dict[param]
                param_value = self.values[cat_name][param]
                ax_kwargs = {"xlabel": hparam.text, "legend_label": cat_name}
                self.plot_func(ax, param_value, ax_kwargs=ax_kwargs, **plot_kwargs)


class BiPlot(Plot):
    """Class that creates the standard x vs. y plots."""

    def generate(self, plot_params, **plot_kwargs):
        # plot_params = [(param11, param12), (param21,param22)...] (strings)
        for cat_name in self.values:
            for (ax, param_pair) in zip(self.axes, plot_params):
                param1, param2 = param_pair
                param1_values = self.values[cat_name][param1]
                param2_values = self.values[cat_name][param2]
                param1_text = self.hparam_dict[param1].text
                param2_text = self.hparam_dict[param2].text
                ax_kwargs = {
                    "xlabel": param1_text,
                    "ylabel": param2_text,
                    "legend_label": cat_name,
                }
                self.plot_func(
                    ax,
                    (param1_values, param2_values),
                    ax_kwargs=ax_kwargs,
                    **plot_kwargs
                )


class MatrixPlot(Plot):
    def __init__(self, matrix_func, hparams, symmetric=False, **kwargs):
        super().__init__(matrix_func, hparams, ncols=1, nrows=1, **kwargs)
        self.matrix_func = matrix_func
        self.symmetric = symmetric
        self.ax = self.axes[0]

    def generate(self, plot_params, **plot_kwargs):
        assert len(self.values) == 1
        cat_name, param_values = self.values.popitem()
        plot_values = [(param, param_values[param]) for param in plot_params]
        latex_params = [
            self.hparam_dict[param].get_text(only_param=True) for param in plot_params
        ]
        ax_kwargs = {
            "xticks": range(len(latex_params)),
            "yticks": range(len(latex_params)),
            "xtick_labels": latex_params,
            "ytick_labels": latex_params,
        }
        self.plot_func(self.ax, plot_values, ax_kwargs=ax_kwargs)


class Histogram(Plot):
    """Creates histogram and uses caching to set the bin sizes of
    all the catalogs plotted to be the same.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert type(self.plot_func) is plot_funcs.CreateHistogram
        self.create_histogram = self.plot_func
        self.n_bins = self.create_histogram.n_bins

    def run_histogram(
        self, cat_name, plot_params, color, bin_edges=None, **plot_kwargs
    ):
        for i, (ax, param) in enumerate(zip(self.axes, plot_params)):
            if bin_edges:
                bin_edge = bin_edges[i]
                plot_kwargs.update(dict(bins=bin_edge))

            param_value = self.values[cat_name][param]
            ax_kwargs = {"use_legend": True, "xlabel": param.text}
            self.create_histogram(
                param_value,
                ax,
                ax_kwargs=ax_kwargs,
                legend_label=cat_name,
                color=color,
                **plot_kwargs
            )

    def generate(self, plot_params, **plot_kwargs):
        bin_edges = []
        for param in plot_params:
            param_values = []
            for cat_name in self.values:
                param_value = self.values[cat_name][param]
                param_values.append(param_value)

            # get the bin edges
            bins = np.histogram(np.hstack(param_values), bins=self.n_bins)[1]
            bin_edges.append(bins)

        for cat_name, color in zip(self.values, self.colors):
            self.run_histogram(
                cat_name, plot_params, color, bin_edges=bin_edges, **plot_kwargs
            )


class StackedHistogram(Histogram):
    """
    Create a stacked histogram, this is specifically useful to reproduce plots like in Figure 3
    of https://arxiv.org/pdf/1404.4634.pdf, where the top histogram are all the individual plots
    and the bottom row shows the ratio of each with respect to the total.

    * Pass in n_row as if this wasn't stacked (just thinking of normal histogram.
    * Used:
    https://stackoverflow.com/questions/37737538/merge-matplotlib-subplots-with-shared-x-axis
    """

    # assume the first catalog given is the one we are taking rations with respect to.
    def __init__(self, *args, **kwargs):
        super(StackedHistogram, self).__init__(*args, **kwargs)
        self.main_catalog_idx = 0

    # def generate_from_cached(self):
    #     # first get bin edges.
    #     assert 'bins' in self.plot_kwargs
    #
    #     num_bins = self.plot_kwargs['bins']
    #     bin_edges = []
    #     main_cat = self.cached_args[self.main_catalog_idx][0]
    #
    #     for param in self.params:
    #
    #         # first do it normally.
    #         param_values = []
    #         for (cat, _) in self.cached_args:
    #             param_values.append(param.get_values(cat))
    #
    #         bins1 = np.histogram(np.hstack(param_values), bins=num_bins)[1]
    #
    #         # then the ratio ones.
    #         param_values = []
    #         for i, (cat, _) in enumerate(self.cached_args):
    #             if i != self.main_catalog_idx:
    #                 assert len(main_cat) >= len(cat)
    #                 param_values.append(param.get_values(cat) / param.get_values(main_cat))
    #         bins2 = np.histogram(np.hstack(param_values), bins=num_bins)[1]
    #
    #         bin_edges.append((bins1, bins2))
    #
    #     # then use the bin edges to plot.
    #     for (cat, kwargs) in self.cached_args:
    #         self.generate(cat, bin_edges=bin_edges, main_cat=main_cat, **kwargs)
    #
    # @staticmethod
    # def get_subplots_config(nrows, ncols, param_locs, figsize):
    #     fig = plt.figure(figsize=figsize)
    #     new_nrows = nrows*2
    #     grids = gridspec.GridSpec(new_nrows, ncols, height_ratios=[2, 1]*nrows)
    #     axes = [[] for _ in range(new_nrows)]
    #
    #     for i in range(new_nrows):
    #         for j in range(ncols):
    #             gs = grids[i, j]
    #             if i % 2 == 0:
    #                 ax = plt.subplot(gs)
    #             else:
    #                 ax_above = axes[i-1][j]
    #                 ax = plt.subplot(gs, sharex=ax_above)
    #             axes[i].append(ax)
    #     plt.subplots_adjust(hspace=.0)
    #     return fig, axes, param_locs
    #
    # def run(self, cat, bin_edges=None, main_cat=None, **kwargs):
    #     assert main_cat is not None
    #
    #     for i in range(self.nrows*2):
    #         param =
    #         for j in range(self.ncols):
    #             ax = self.axes[i][j]
    #             if bin_edges:
    #                 bin_edge = bin_edges[i][i % 2]
    #                 assert 'bins' in kwargs
    #                 kwargs.update(dict(bins=bin_edge1))
    #             if i % 2 == 0:
    #                 self.plot_func(cat, param, ax, xlabel=param.text, **kwargs)
    #
    #         if i % 2 == 0:
    #             self.plot_func(main_cat, param, )
    #
    #             else:
    #
    #
    #     for i, (ax, param) in enumerate(zip(self.axes, self.params)):
    #         if bin_edges:
    #             bin_edge1, bin_edge2 = bin_edges[i]

import numpy as np
from collections import OrderedDict

from relaxed import plots, plot_funcs
from relaxed.halo_parameters import get_hparam


def plot_mvir_histogram(hcats, pdf):
    """Basic plot showcasing features with a single histogram of Mvir, multiple catalogs may be
    used at once.

    NOTE: To be used for non-decade catalogs.

    Args:
        hcats (list): Already loaded, list of hcat objects.
        pdf: PDF object that can be used to save figures to.
    """
    names = [hcat.name for hcat in hcats]

    # (1) Start with plot_func creation, just using default values for everything.
    create_histogram = plot_funcs.CreateHistogram(xlabel_size=24)

    # (2) Create list of all unique halo_params that are necessary for plotting.
    hparams = [get_hparam("mvir", log=True)]

    # (3) Create Plot object.
    histogram_plot = plots.Histogram(create_histogram, hparams, nrows=1, ncols=1)

    # (4) Load corresponding values of hparams from hcats into plot object
    for hcat in hcats:
        histogram_plot.load(hcat)

    # (5) Create a list of names of which order you want to plot your hparams
    plot_params = OrderedDict({"mvir": {*names}})

    # (6) Generate figure
    histogram_plot.generate(plot_params)

    # (7) Save the figure.
    histogram_plot.save(pdf=pdf)


def plot_scatter_relaxed_and_mass(hcats, pdf):
    """Obtain some of the basic plots where multiple catalogs might be overlaid. Plot mass vs
    identified relaxedness parameters.

    NOTE: To be used for non-decade catalogs.

    This one uses the ScatterBinning class.
    """
    names = [hcat.name for hcat in hcats]
    bin_bds = np.arange(11, 14.5, 0.5)

    # prepare halo_params
    params = ["eta", "x0", "v0", "xoff", "voff", "q", "cvir", "a2"]
    _params = ["mvir", *params]
    hparams = [get_hparam(param, log=True) for param in _params]
    hparams.append(get_hparam("f_sub", log=False))

    # prepare the plot_func
    scatter_binning = plot_funcs.ScatterBinning(
        bin_bds=bin_bds, show_bands=True, xlabel_size=24, ylabel_size=24
    )

    # setup plotting
    plot = plots.BiPlot(scatter_binning, hparams, nrows=3, ncols=3, figsize=(18, 22))

    # load catalogs
    for hcat in hcats:
        plot.load(hcat)

    # now specify which parameters we want to plot where.
    plot_params = OrderedDict({("mvir", param): {*names} for param in params})

    # generate and save.
    plot.generate(plot_params)
    plot.save(pdf=pdf)


def plot_correlation_matrix_basic(hcats, pdf=None):
    """
    Create a visualization fo the matrix of correlation separate for each of the catalogs in hcats.

    Should only be used on catalogs that are binned in narrow mass ranges.
    """

    names = [hcat.name for hcat in hcats]
    assert names == ["M11", "M12", "M13"]

    # round up params.
    params = [
        "mvir",
        "eta",
        "x0",
        "v0",
        "xoff",
        "voff",
        "q",
        "cvir",
        "a2",
        "phi_l",
    ]
    hparams = [get_hparam(param, log=True) for param in params]
    hparams.append(get_hparam("f_sub", log=False))

    scatter_binning = plot_funcs.MatrixValues(xlabel_size=24, ylabel_size=24)
    plot = plots.MatrixPlot(
        scatter_binning, hparams, nrows=1, ncols=3, figsize=(30, 10)
    )

    # load catalogs
    for hcat in hcats:
        plot.load(hcat)

    plot_params = OrderedDict({param: {*names} for param in params})
    plot.generate(plot_params)
    plot.save(pdf=pdf)


def plot_mean_centered_hists(hcats, pdf):
    names = [hcat.name for hcat in hcats]
    mean_center = [lambda x: (x - np.mean(x)) / np.std(x)]
    params = ["cvir", "eta", "x0", "v0", "spin", "q", "phi_l"]
    hparams = [get_hparam(param, log=True, modifiers=mean_center) for param in params]
    create_histogram = plot_funcs.CreateHistogram(
        xlabel_size=24, vline="median", log_y=True
    )
    plot_params = OrderedDict({param: {*names} for param in params})
    plot = plots.Histogram(
        create_histogram,
        hparams,
        ncols=2,
        nrows=4,
        figsize=(12, 20),
    )

    for hcat in hcats:
        plot.load(hcat)

    plot.generate(plot_params)
    plot.save(pdf=pdf)


# def plot_decades_basic(hcats, pdf, colors):
#     """Produce all the basic plots that require decade separation"""
#
#     general_kwargs = dict(xlabel_size=28, ylabel_size=28)
#     binning_kwargs = dict(n_xbins=8, show_bands=False, **general_kwargs)
#
#     figsize = (24, 24)
#     uplots = []
#     hplots = [[] for _ in hcats]
#
#     # Plot 5: Correlation between all pairs of different relaxedness parameters as a function
#     # of mass half decades.
#     # params to include:  't/|u|', 'x0', 'v0', 'xoff', 'Voff', 'q', 'cvir'
#     params = [
#         (HaloParam("t/|u|", log=True), HaloParam("x0", log=True)),
#         (HaloParam("t/|u|", log=True), HaloParam("v0", log=True)),
#         (HaloParam("t/|u|", log=True), HaloParam("q", log=True)),
#         (HaloParam("t/|u|", log=True), HaloParam("cvir", log=True)),
#         (HaloParam("x0", log=True), HaloParam("v0", log=True)),
#         (HaloParam("x0", log=True), HaloParam("q", log=True)),
#         (HaloParam("x0", log=True), HaloParam("cvir", log=True)),
#         (HaloParam("v0", log=True), HaloParam("q", log=True)),
#         (HaloParam("v0", log=True), HaloParam("cvir", log=True)),
#         (HaloParam("q", log=True), HaloParam("cvir", log=True)),
#     ]  # total = 10
#     param_locs = []  # triangular pattern, user defined param_locs.
#     for i in range(4):
#         for j in range(4 - i):
#             param_locs.append((j, i))
#
#     plot1 = plots.BiPlot(
#         plot_funcs.scatter_binning,
#         params,
#         nrows=4,
#         ncols=4,
#         figsize=figsize,
#         param_locs=param_locs,
#         plot_kwargs=binning_kwargs,
#         title_size=40,
#     )
#
#     uplots.append(plot1)
#     for hplot in hplots:
#         hplot.append(plot1)
#
#     generate_and_save(pdf, hcats, hplots, uplots, colors=colors, cached=False)

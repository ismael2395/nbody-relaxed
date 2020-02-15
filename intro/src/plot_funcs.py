"""
Plotting functions that are useful for visualizing things like correlations.
"""

import numpy as np
import matplotlib.pyplot as plt


def binning3d_mass(cat, ax, param1, param2, mods=[], plot_kwargs={}, legend_size=18):
    """
    * plot_kwargs are additional keyword arguments to pass into the plotting_func
    * mods: lambda functions that modify plotting arrays, e.g. lambda x: np.log10(x)
    """
    mass_bins =[(12, 13), (13, 14), (14, 15)] # decades
    colors = ['b', 'r', 'g'] 
    for mass_bin, color in zip(mass_bins, colors): 
        log_mvir = np.log10(cat['mvir'])
        mmask = (log_mvir > mass_bin[0]) & (log_mvir < mass_bin[1])
        mcat = cat[mmask]
        label = "$" + str(mass_bin[0]) + "< M_{\\rm vir} <" + str(mass_bin[1]) + "$"
        scatter_binning(mods[0](mcat[param1]), 
                        mods[1](mcat[param2]), 
                        color=color, legend_label=label, ax=ax, **plot_kwargs)
    
    ax.legend(prop={"size":legend_size}, loc='best')


def scatter_binning(x, y, ax, nxbins=10, title=None, xlabel=None, ylabel=None, color='r', legend_label=None,
                   tick_size=14, xlabel_size=18, ylabel_size=18, no_bars=False, show_lines=False, show_bands=False,
                   legend_size=18):
    xs = np.linspace(np.min(x), np.max(x), nxbins)
    xbbins = [(xs[i], xs[i+1]) for i in range(len(xs)-1)]

    masks = [((xbbin[0] < x) & ( x < xbbin[1])) for xbbin in xbbins]
    binned_x = [x[mask] for mask in masks]
    binned_y = [y[mask] for mask in masks]

    xmeds = [np.median(xbin) for xbin in binned_x]
    ymeds = [np.median(ybin) for ybin in binned_y]

    xqs = np.array([[xmed - np.quantile(xbin, 0.25), np.quantile(xbin,0.75) - xmed] for (xmed,xbin) in zip(xmeds,binned_x)]).T
    yqs = np.array([[ymed - np.quantile(ybin, 0.25), np.quantile(ybin,0.75) - ymed] for (ymed,ybin) in zip(ymeds,binned_y)]).T

    if not no_bars:
        ax.errorbar(xmeds, ymeds, xerr=xqs, yerr=yqs, fmt='o--', capsize=10, color=color, label=legend_label)
    else:
        ax.errorbar(xmeds, ymeds, xerr=xqs, fmt='o-', color=color, label=legend_label, capsize=10)

    y1 = np.array([np.quantile(ybin, 0.25) for ybin in binned_y])
    y2 = np.array([np.quantile(ybin, 0.75) for ybin in binned_y])

    if show_lines:
        ax.plot(xmeds, y1, '--', color=color)
        ax.plot(xmeds, y2, '--', color=color)

    if show_bands:
        ax.fill_between(xmeds, y1, y2, alpha=0.2, linewidth=0.001, color=color)

    if title is not None:
        ax.set_title(title)
    if xlabel is not None and ylabel is not None:
        ax.set_xlabel(xlabel, size=xlabel_size)
        ax.set_ylabel(ylabel, size=ylabel_size)

    ax.tick_params(axis='both', which='major', labelsize=tick_size)

    if legend_label:
        ax.legend(loc='best', prop={'size':legend_size})

def cov_plot(ax):
    mask = np.tri(corrs.shape[0], k=-1)
    A = np.ma.array(corrs, mask=mask)
    im = ax.matshow(A, cmap='bwr', vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax)
    ax.set_xticklabels([''] + latex_params, size=16);
    ax.set_yticklabels([''] + latex_params, size=16);

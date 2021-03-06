"""
Manages the interface for returning filters that can be used in catalogs.
A filter is always a dictionary of keys which are catalog parameters and values of lambda functions,
check `get_default_base_filters` below for an example.
"""
import warnings
from copy import deepcopy

import numpy as np

from . import halo_parameters


def intersect(ids1, ids2):
    """Intersect two np.array IDs.

    Args:
        Both inputs should be np.arrays.

    Returns:
        An boolean array `indx_ok` corresponding to `ids1` s.t. `indx_ok[i]` is true iff
        `ids1[i]` is contained in `ids2`.

    Notes:
        - Full intersection by repeating operation but switching order.
    """
    assert type(ids1) == type(ids2) == np.ndarray
    assert np.all(np.sort(ids1) == ids1)
    assert np.all(np.sort(ids2) == ids2)
    indx = np.searchsorted(ids2, ids1)
    indx_ok = indx < len(ids2)
    indx_ok[indx_ok] &= ids2[indx[indx_ok]] == ids1[indx_ok]

    return indx_ok


def get_id_filter(ids):
    assert type(ids) is np.ndarray or type(ids) is list
    ids = np.array(ids)
    return {"id": lambda x: intersect(np.array(x), ids)}


def get_bound_filter(param, low=-np.inf, high=np.inf, modifier=lambda x: x):
    return {param: lambda x: (modifier(x) > low) & (modifier(x) < high)}


def particle_mass_filter(particle_mass, subhalos):
    """
    We introduce two default cuts on mass:
        * The first part is to account for having too few particles (<1000).

    Args:
        particle_mass: The mass of each particle in the halo catalog.
        subhalos:
    """

    if subhalos:
        warnings.warn("Making same cut in subhalos as in host halos")

    return {"mvir": lambda mvirs: (np.log10(mvirs) > np.log10(particle_mass * 1e3))}


def catalog_mass_filter(catalog_name):
    """
    * The cuts on mvir are based on Phil's comment that Bolshoi/BolshoiP only give reasonable
    results up to log10(Mvir) ~ 13.5 - 13.75. Larger masses are undersampled in Bolshoi/BolshoiP
    :return:
    """

    if catalog_name == "Bolshoi" or catalog_name == "BolshoiP":

        def myfilter(mvirs):
            return np.log10(mvirs) < 13.75

    else:
        raise NotImplementedError("Implemented other catalogs yet.")

    return {"mvir": myfilter}


def get_relaxed_filters(relaxed_name):
    """
    For now only relaxed criteria is (cat['xoff'] < 0.04), according to Power 2011
    :return:
    """

    if relaxed_name == "power2011":
        return {
            "x0": lambda x: x < 0.04,
        }

    if relaxed_name == "neto2007":
        return {
            "f_sub": lambda x: x < 0.1,
            "x0": lambda x: x < 0.07,
            "eta": lambda x: x < 1.35,
        }

    else:
        raise NotImplementedError("The required relaxed name has not been implemented.")


def get_default_filters(particle_mass, subhalos):
    """
    NOTE: Always assume that the values of the catalog are returned without log10ing first.

    * x in the lambda functions represents the values of the keys.

    * upid >=0 indicates a subhalo, upid=-1 indicates a distinct halo. Phil's comment: "This is -1
    for distinct halos and a halo ID for subhalos."

    >> cat_distinct = cat[cat['upid'] == -1]
    >> cat_sub = cat[cat['upid'] >= 0]
    """
    return {
        **particle_mass_filter(particle_mass, subhalos),
        "upid": lambda x: (x == -1 if not subhalos else x >= 0),
    }


class HaloFilter:
    def __init__(self, filters, name="filtered_cat"):
        self.filters = filters
        self.name = name

    def filter_cat(self, cat):
        # Always do filtering in real space NOT log space.
        for param, ft in self.filters.items():
            hparam = halo_parameters.get_hparam(param, log=False)
            cat = cat[ft(hparam.get_values(cat))]
        return cat

    def __call__(self, hcat, copy=True):
        if not copy:
            raise NotImplementedError

        # creates a new copy of hcat
        new_hcat = deepcopy(hcat)
        new_cat = self.filter_cat(new_hcat.cat)
        new_hcat.cat = new_cat
        new_hcat.name = self.name
        return new_hcat

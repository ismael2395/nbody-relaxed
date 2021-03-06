import numpy as np
from astropy.table import Table
from pminh import minh

from relaxed.halo_filters import intersect
from relaxed.subhaloes import quantities


def create_subhalo_cat(host_ids, minh_file):
    # mcat is complete and must be read by blocks.
    # host_ids correspond only host haloes w/ upid == -1
    # now we also want to add subhalo fraction and we follow Phil's lead

    assert isinstance(host_ids, np.ndarray)
    assert np.all(np.sort(host_ids) == host_ids)

    # will fill out as we read the blocks.
    f_sub = np.zeros(len(host_ids))
    host_mvir = np.zeros(len(host_ids))
    fnames = ["id", "mvir", "f_sub"]
    fdata = [host_ids, host_mvir, f_sub]
    subcat = Table(names=fnames, data=fdata)
    subcat.sort("id")

    with minh.open(minh_file) as mcat:
        for b in range(mcat.blocks):
            names = ["id", "upid", "mvir"]
            ids, upid, mvir = mcat.block(b, names)
            table = Table(names=names, data=[ids, upid, mvir])
            table.sort("id")

            # first we calculate host_mvir
            keep = intersect(np.array(table["id"]), host_ids)
            indx_ok = intersect(host_ids, np.array(table[keep]["id"]))
            subcat["mvir"][indx_ok] = table[keep]["mvir"]

            # need to contain only ids of host_ids for it to work.
            sub_pids = upid[upid != -1]
            sub_mvir = mvir[upid != -1]
            subcat["f_sub"] += quantities.m_sub(host_ids, sub_pids, sub_mvir)

    assert np.all(subcat["mvir"] > 0)
    subcat["f_sub"] = subcat["f_sub"] / subcat["mvir"]
    return subcat

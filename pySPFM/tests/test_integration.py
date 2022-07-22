"""
Integration tests for "real" data
"""

import glob
import os
import re
import shutil
import tarfile
from gzip import GzipFile
from io import BytesIO

import pytest
import requests
from pkg_resources import resource_filename

from pySPFM.workflows import pySPFM as pySPFM_cli


def download_test_data(osf, outpath):
    """
    Downloads tar.gz data stored at `osf` and unpacks into `outpath` (taken from tedana)
    Parameters
    ----------
    osf : str
        URL to OSF file that contains data to be downloaded
    outpath : str
        Path to directory where OSF data should be extracted
    """

    req = requests.get(osf)
    req.raise_for_status()
    t = tarfile.open(fileobj=GzipFile(fileobj=BytesIO(req.content)))
    os.makedirs(outpath, exist_ok=True)
    t.extractall(outpath)


def check_integration_outputs(fname, outpath):
    """
    Checks outputs of integration tests (taken from tedana)
    Parameters
    ----------
    fname : str
        Path to file with expected outputs
    outpath : str
        Path to output directory generated from integration tests
    """

    # Gets filepaths generated by integration test
    existing = [
        os.path.relpath(f, outpath)
        for f in glob.glob(os.path.join(outpath, "**"), recursive=True)[1:]
    ]

    # Checks for log file
    log_regex = "^pySPFM_[12][0-9]{3}-[0-9]{2}-[0-9]{2}T[0-9]{2}[0-9]{2}[0-9]{2}.tsv$"
    logfiles = [out for out in existing if re.match(log_regex, out)]
    assert len(logfiles) == 1

    # Removes logfile from list of existing files
    existing.remove(logfiles[0])

    # Compares remaining files with those expected
    with open(fname, "r") as f:
        tocheck = f.read().splitlines()
    tocheck = [os.path.normpath(path) for path in tocheck]
    assert sorted(tocheck) == sorted(existing)


def test_integration_five_echo(skip_integration, mask_five_echo):
    """Integration test of the full pySPFM workflow using five-echo test data."""

    if skip_integration:
        pytest.skip("Skipping five-echo integration test")

    out_dir = "/tmp/data/five-echo/pySPFM.five-echo"

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)

    # download data and run the test
    download_test_data("https://osf.io/vg4wy/download", os.path.dirname(out_dir))
    prepend = "/tmp/data/five-echo/p06.SBJ01_S09_Task11_e"
    suffix = ".psc.nii.gz"
    datalist = [prepend + str(i + 1) + suffix for i in range(5)]
    echo_times = [15.4, 29.7, 44.0, 58.3, 72.6]

    # CLI args
    args = (
        ["-i"]
        + datalist
        + ["-te"]
        + [str(te) for te in echo_times]
        + ["-m"]
        + [mask_five_echo]
        + ["-o"]
        + ["test-me"]
        + ["-tr"]
        + ["2"]
        + ["-d"]
        + [out_dir]
        + ["-crit"]
        + ["factor"]
        + ["-factor"]
        + ["10"]
        + ["--max_iter_fista"]
        + ["50"]
        + ["-jobs"]
        + ["1"]
        + [
            "--debug",
            "--debias",
            "--block",
            "--bids",
        ]
    )
    pySPFM_cli._main(args)

    # compare the generated output files
    fn = resource_filename("pySPFM", "tests/data/nih_five_echo_outputs_verbose.txt")
    check_integration_outputs(fn, out_dir)


def test_integration_lars(skip_integration, mask_five_echo):
    """Integration test of the full pySPFM workflow using five-echo test data."""

    if skip_integration:
        pytest.skip("Skipping five-echo integration test")

    out_dir = "/tmp/data/five-echo/pySPFM.five-echo"

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)

    # download data and run the test using the second echo time
    download_test_data("https://osf.io/vg4wy/download", os.path.dirname(out_dir))
    prepend = "/tmp/data/five-echo/p06.SBJ01_S09_Task11_e"
    suffix = ".psc.nii.gz"
    data = f"{prepend}2{suffix}"

    # CLI args
    args = (
        ["-i"]
        + [data]
        + ["-m"]
        + [mask_five_echo]
        + ["-o"]
        + ["test_lars"]
        + ["-tr"]
        + ["2"]
        + ["-d"]
        + [out_dir]
        + ["-crit"]
        + ["bic"]
        + ["--max_iter_factor"]
        + ["0.3"]
        + ["-jobs"]
        + ["1"]
        + [
            "--debug",
            "--debias",
        ]
    )
    pySPFM_cli._main(args)

    # compare the generated output files
    fn = resource_filename("pySPFM", "tests/data/lars_integration_outputs.txt")
    check_integration_outputs(fn, out_dir)

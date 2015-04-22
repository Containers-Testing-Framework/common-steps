# -*- coding: UTF-8 -*-

# Some useful functions for your environment.py
import subprocess
import os
import logging


def run(command):
    """Run a command locally, print output and throw exception if exit code is not 0"""
    try:
        logging.info("Running '%s'" % command)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        logging.debug("Return code: 0, output:\n%s" % output)
        return output
    except subprocess.CalledProcessError as e:
        logging.warn("Return code: %d, output:\n%s" % (e.returncode, e.output))
        raise e


def docker_cleanup(context):
    """Stop, kill and remove running docker container
    ID is read from context var cid_file"""

    # Read container cid (if available)
    if not os.path.exists(context.cid_file):
        return

    cid = None
    with open(context.cid_file, "r") as f:
        cid = f.read().strip()

    try:
        # Cleanup previous container
        run("docker stop %s" % cid)
        run("docker kill %s" % cid)
        run("docker rm %s" % cid)
    finally:
        os.remove(context.cid_file)

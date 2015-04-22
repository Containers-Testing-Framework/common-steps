# -*- coding: UTF-8 -*-

# Some useful functions for your environment.py
import subprocess
import os


def run(command, print_output=True):
    """Run a command locally, print output and throw exception if exit code is not 0"""
    try:
        print("Running '%s'" % command)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        if print_output:
            print("Return code: 0, output:\n%s" % output)
        return output
    except subprocess.CalledProcessError as e:
        print("Return code: %d, output:\n%s" % (e.returncode, e.output))
        raise e


def docker_cleanup(context, print_output=True):
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
        run("docker stop %s" % cid, print_output=print_output)
        run("docker kill %s" % cid, print_output=print_output)
        run("docker rm %s" % cid, print_output=print_output)
    finally:
        os.remove(context.cid_file)

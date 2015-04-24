# -*- coding: UTF-8 -*-

# Some useful functions for your environment.py
import tempfile
import shutil
import ansible.runner
import logging
import re
import os
import glob
import stat

def before_all(context):
    try:
        ansible_cfg = context.config.userdata['ANSIBLE']
        inventory = ansible.inventory.Inventory(ansible_cfg)
    except KeyError:
        raise Exception("-D ANSIBLE missing")
    remote_dir = '/var/tmp/dkrfile'

    def open_file(path):
        context.temp_dir = tempfile.mkdtemp()
        ret = ansible.runner.Runner(
            module_name='fetch',
            inventory=inventory,
            module_args='src={0} dest={1}'.format(
                path, context.temp_dir)).run()
        for host, value in ret['contacted'].iteritems():
            try:
                ret_file = open(value['dest'])
                return ret_file
            except KeyError:
                print ("ansible output: {0}".format(ret))
                raise Exception(value['msg'])
    context.open_file = open_file

    def run(command):
        logging.debug("Running '%s'" % command)
        context.result = ansible.runner.Runner(
            module_name='command',
            inventory=inventory,
            module_args="{0} chdir={1}".format(command, remote_dir)
        ).run()
        passed = True
        # dark means not responding
        if context.result['dark']:
            passed = False
            print("dark")
            print(context.result)
        if not context.result['contacted']:
            passed = False
            print ("no contacted hosts")
        for host, values in context.result['contacted'].iteritems():
            if values['rc'] != 0:
                print("On {0} returned {1}".format(host, values['rc']))
                print("stderr: {0}".format(values['stderr']))
                assert False
            return values['stdout']
    context.run = run

    # copy dockerfile
    dockerfile = context.config.userdata['DOCKERFILE']
    dockerfile_dir = os.path.dirname(dockerfile)
    # create remote directory
    ansible.runner.Runner(
        module_name='file',
        inventory=inventory,
        module_args='dest={0} state=directory'.format(remote_dir)
        ).run()
    # copy dockerfile
    ansible.runner.Runner(
        module_name='copy',
        inventory=inventory,
        module_args='src={0} dest={1}'.format(dockerfile, remote_dir)
        ).run()
    # copy files from dockerfile
    f_in = open(dockerfile)
    for path in re.findall('(?:ADD|COPY) ([^ ]+) ', f_in.read()):
        for glob_path in glob.glob(os.path.join(dockerfile_dir,path)):
            # TODO Is there a nicer way to keep permissions?
            ansible.runner.Runner(
                module_name='copy',
                inventory=inventory,
                module_args='src={0} dest={1} directory_mode mode={2}'.format(glob_path, remote_dir,
                    oct(stat.S_IMODE(os.stat(glob_path).st_mode)))
            ).run()

    # build image if not exist
    try:
        context.image = context.config.userdata['IMAGE']
        run('docker pull {0}'.format(context.image))
    except KeyError:
        context.image = 'ctf'
        run('docker build -t {0} .'.format(context.image))

    cid_file_name = re.sub(r'\W+', '', context.image)
    context.cid_file = "/tmp/%s.cid" % cid_file_name


def before_scenario(context, scenario):
    if hasattr(context, 'cid'):
        context.run("docker stop %s" % context.cid)
        context.run("docker kill %s" % context.cid)
        context.run("docker rm %s" % context.cid)
        del context.cid
        context.run('rm {0}'.format(context.cid_file))


def after_all(context):
    if hasattr(context, 'temp_dir'):
        shutil.rmtree(context.temp_dir) #FIXME catch exception

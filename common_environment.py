# Some useful functions for your environment.py
import tempfile
import shutil
import logging
import re
import os
import glob
import stat

from ansible_runner import Runner


def sample_before_all(context):
    docker_setup(context)
    context.build_or_pull_image(skip_pull=True, skip_build=True)


def sample_after_scenario(context, scenario):
    if context.config.userdata['KEEP_CONTAINER_AFTER_TEST']:
        return
    context.remove_container()


def sample_after_all(context):
    if hasattr(context, 'temp_dir'):
        shutil.rmtree(context.temp_dir)  # FIXME catch exception


def docker_setup(context):
    # Set a remote dir for commands
    context.remote_dir = '/tmp/'

    # Read ansible inventory from config
    ansible_cfg = None

    logging.info("Reading ansible config")
    try:
        ansible_cfg = context.config.userdata['ANSIBLE']
    except KeyError:
        raise Exception("-D ANSIBLE missing")

    def open_file(path):
        context.temp_dir = tempfile.mkdtemp()
        ret = Runner(
            module_name='fetch',
            inventory_file=ansible_cfg,
            module_args='src={0} dest={1}'.format(
                path, context.temp_dir)).run()
        for _, value in ret['contacted'].iteritems():
            try:
                ret_file = open(value['dest'])
                return ret_file
            except KeyError:
                print("ansible output: {0}".format(ret))
                raise Exception(value['msg'])
    context.open_file = open_file

    def run(command):
        if '{{' in command:
            command = command.replace("{{", "{{ '{{").replace("}}", "}}' }}")
        if '=' in command:
            command = command.replace('=', '\=')
        logging.info("Running '%s'", command)
        context.result = Runner(
            module_name="shell",
            inventory_file=ansible_cfg,
            module_args="{0} chdir={1}".format(command, context.remote_dir)
        ).run()

        # dark means not responding
        if 'dark' in context.result:
            print(context.result)
        for host, values in context.result['contacted'].iteritems():
            retvalue = values.get('rc')
            logging.info("On {0} returned {1}".format(host, retvalue))

            if 'cmd' in values:
                logging.info("cmd: {0}".format(values['cmd']))
            if 'stderr' in values:
                logging.info('stderr:%s', values['stderr'])

            result = ''
            if 'msg' in values:
                logging.info('msg:%s', values['msg'])
                result = values['msg']
            if 'stdout' in values:
                logging.info('stdout:%s', values['stdout'])
                result = values['stdout']

            if 'failed' in values:
                assert False
            return result
    context.run = run

    def copy_dockerfile():
        try:
            # copy dockerfile
            dockerfile = context.config.userdata['DOCKERFILE']
            dockerfile_dir = os.path.dirname(dockerfile)
            # create remote directory
            Runner(
                inventory_file=ansible_cfg,
                module_name='file',
                module_args='dest={0} state=directory'.format(context.remote_dir)
                ).run()
            # copy dockerfile
            Runner(
                inventory_file=ansible_cfg,
                module_name='copy',
                module_args='src={0} dest={1}'.format(dockerfile, context.remote_dir)
                ).run()
            # copy files from dockerfile
            f_in = open(dockerfile)
            for path in re.findall('(?:ADD|COPY) ([^ ]+) ', f_in.read()):
                for glob_path in glob.glob(os.path.join(dockerfile_dir, path)):
                    # TODO Is there a nicer way to keep permissions?
                    Runner(
                        inventory_file=ansible_cfg,
                        module_name='copy',
                        module_args='src={0} dest={1} directory_mode mode={2}'.format(
                            glob_path, context.remote_dir,
                            oct(stat.S_IMODE(os.stat(glob_path).st_mode)))
                    ).run()
        except Exception as e:
            logging.warning("copy_dockerfile:%s", e)
    context.copy_dockerfile_to_remote_machine = copy_dockerfile

    def build_or_pull_image(skip_build=False, skip_pull=False):
        # build image if not exist
        try:
            context.image = context.config.userdata['IMAGE']
            if not skip_pull:
                run('docker pull {0}'.format(context.image))
        except AssertionError:
            pass
        except KeyError:
            context.image = 'ctf'
            if not skip_build:
                try:
                    run('docker build -t {0} .'.format(context.image))
                except AssertionError:
                    pass
        context.cid_file = "/tmp/%s.cid" % re.sub(r'\W+', '', context.image)
    context.build_or_pull_image = build_or_pull_image

    def get_current_cid():
        try:
            return context.run('cat %s' % context.cid_file)
        except AssertionError as e:
            logging.info("remove_container: %s", str(e))
            return
    context.get_current_cid = get_current_cid

    def remove_container(show_logs=True, kill=True, rm=True):
        cid = context.get_current_cid()
        if cid:
            if show_logs:
                context.run("docker logs %s" % cid)
            try:
                context.run("docker stop %s" % cid)
            except AssertionError:
                if kill:
                    context.run("docker kill %s" % cid)
            finally:
                if rm:
                    context.run("docker rm -f %s" % cid)

            if hasattr(context, 'cid'):
                del context.cid
            context.run('rm {0}'.format(context.cid_file))
    context.remove_container = remove_container

    logging.info("Docker setup finished\n")

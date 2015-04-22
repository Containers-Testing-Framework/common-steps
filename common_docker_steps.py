# -*- coding: UTF-8 -*-

# Some useful functions for your docker container steps
from behave import step
from common_environment import run


@step(u'Docker container is started')
@step(u'Docker container is started with params "{params}"')
def container_started(context, params=''):
    # TODO: allow tables here
    # A nice candidate for common steps
    context.job = run('docker run -d --cidfile %s %s %s' % (context.cid_file, params, context.image))
    context.cid = open(context.cid_file).read().strip()

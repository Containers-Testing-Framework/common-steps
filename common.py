""" Common docker stuff """
from behave import *

@given(u'Dockerfile')
def step_impl(context):
#FIXME copy whole directory
    try:
        dockerfile_path = context.config.userdata['DOCKERFILE']
    except KeyError:
        raise RuntimeError("Undefined DOCKERFILE envar")
    ret = context.remote_cmd(
            'copy',
            module_args="src={0} dest=~".format(dockerfile_path))
    if not ret:
        raise RuntimeError("Failed to copy {0}".format(dockerfile_path))

@when(u'Generic Dockerlint is run')
def step_impl(context):
#FIXME how/where is dockerlint?
    raise NotImplementedError(u'STEP: When Generic Dockerlint is run')

@then(u'it passes')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then it passes')

@when(u'Generic image is build from Dockerfile')
def step_impl(context):
    context.remote_cmd(
        'command',
        module_args="docker build ."
    )
    raise NotImplementedError(u'STEP: When Generic image is build from Dockerfile')

@then(u'it satisfies best practices')
def step_impl(context):
#FIXME common tests on top of fresh image
    raise NotImplementedError(u'STEP: Then it satisfies best practices')

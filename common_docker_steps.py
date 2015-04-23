# -*- coding: UTF-8 -*-

# Some useful functions for your docker container steps
from behave import step, given
from common_environment import run
import os


@given(u'the project contains Dockerfile')
@given(u'the project contains docker file in "{filename}"')
def project_has_dockerfile(context, filename=''):
    if not filename:
        filename = 'Dockerfile'

    abs_path = os.path.abspath(filename)
    if not os.path.exists(abs_path):
        context.scenario.skip(reason='File %s not found' % abs_path)

    context.dockerfile = abs_path


@step(u'First dockerfile instruction is FROM')
def first_instruction_is_from(context):
    with open(context.dockerfile, "r") as f:
        first_line = f.readline()
        # Skip blank lines and comments
        while len(first_line.strip()) == 0 or first_line.strip()[0] == '#':
            first_line = f.readline()
        assert first_line.split(' ')[0] == 'FROM',\
            "Expected first line to be FROM, but was '%s'" % first_line


@step(u"dockerfile doesn't contain unknown instructions")
def check_for_unknown_instructions(context):
    valid_instructions = set([
        'FROM', 'MAINTAINER', 'RUN', 'CMD', 'LABEL', 'EXPOSE', 'ENV', 'ADD', 'COPY',
        'ENTRYPOINT', 'VOLUME', 'USER', 'WORKDIR', 'ONBUILD'])

    lines = []
    instructions = []
    last_instruction = ''
    with open(context.dockerfile, "r") as f:
        lines = f.readlines()

    line_continuation = False
    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            # Skip comment lines
            continue

        # Set line continuation var
        if not line_continuation:
            last_instruction = line.split(' ')[0]
            instructions.append(last_instruction)

        if last_instruction == 'RUN' and line[-1] == '\\':
            line_continuation = True
        else:
            line_continuation = False

    # Find the diff between two sets
    instructions_set = set(instructions)
    list_diff = list(instructions_set - valid_instructions)
    assert list_diff == [], "Unknown instructions: %s" % list_diff


@step(u'Docker container is started')
@step(u'Docker container is started with params "{params}"')
def container_started(context, params=''):
    # TODO: allow tables here
    # A nice candidate for common steps
    context.job = run('docker run -d --cidfile %s %s %s' % (context.cid_file, params, context.image))
    context.cid = open(context.cid_file).read().strip()

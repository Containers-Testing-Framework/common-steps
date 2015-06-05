# -*- coding: UTF-8 -*-

# Some useful functions for your connection tests
from behave import step
from time import sleep


@step(u'port {port:d} is open')
@step(u'port {port:d} is {negative:w} open')
def port_open(context, port, negative=False):
    # Get container IP
    context.ip = context.run("docker inspect --format='{{.NetworkSettings.IPAddress}}' %s" % context.cid).strip()

    for attempts in xrange(0, 5):
        try:
            context.run('nc -w5 %s %s < /dev/null' % (context.ip, port))
            return
        except AssertionError:
            # If  negative part was set, then we expect a bad code
            # This enables steps like "can not be established"
            if negative:
                return
            sleep(5)
    raise Exception("Can't connect to port %s" % port)

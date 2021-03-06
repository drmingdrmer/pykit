#!/usr/bin/env python2
# coding: utf-8

import errno
import logging
import os

import subprocess32

logger = logging.getLogger(__name__)


class ProcError(Exception):

    def __init__(self, returncode, out, err, cmd, arguments, options):

        super(ProcError, self).__init__(returncode,
                                        out,
                                        err,
                                        cmd,
                                        arguments,
                                        options)

        self.returncode = returncode
        self.out = out
        self.err = err
        self.command = cmd
        self.arguments = arguments
        self.options = options


def command(cmd, *arguments, **options):

    close_fds = options.get('close_fds', True)
    cwd = options.get('cwd', None)
    shell = options.get('shell', False)
    env = options.get('env', None)
    if env is not None:
        env = dict(os.environ, **env)
    stdin = options.get('stdin', None)

    subproc = subprocess32.Popen([cmd] + list(arguments),
                                 close_fds=close_fds,
                                 shell=shell,
                                 cwd=cwd,
                                 env=env,
                                 stdin=subprocess32.PIPE,
                                 stdout=subprocess32.PIPE,
                                 stderr=subprocess32.PIPE, )

    out, err = subproc.communicate(input=stdin)

    subproc.wait()

    return (subproc.returncode, out, err)


def command_ex(cmd, *arguments, **options):
    returncode, out, err = command(cmd, *arguments, **options)
    if returncode != 0:
        raise ProcError(returncode, out, err, cmd, arguments, options)

    return returncode, out, err


def shell_script(script_str, **options):
    options['stdin'] = script_str
    return command('sh', **options)


def _waitpid(pid):
    while True:
        try:
            os.waitpid(pid, 0)
            break
        except OSError as e:
            # In case we encountered an OSError due to EINTR (which is
            # caused by a SIGINT or SIGTERM signal during
            # os.waitpid()), we simply ignore it and enter the next
            # iteration of the loop, waiting for the child to end.  In
            # any other case, this is some other unexpected OS error,
            # which we don't want to catch, so we re-raise those ones.
            if e.errno != errno.EINTR:
                raise


def _close_fds():
    try:
        max_fd = os.sysconf("SC_OPEN_MAX")
    except ValueError:
        max_fd = 65536

    for i in range(max_fd):
        try:
            os.close(i)
        except OSError:
            pass


def start_process(cmd, target, env, *args):

    try:
        pid = os.fork()
    except OSError as e:
        logger.error(repr(e) + ' while fork')
        raise

    if pid == 0:
        _close_fds()
        args = list(args)
        env = dict(os.environ, **env)
        args.append(env)
        try:
            os.execlpe(cmd, cmd, target, *args)
        except Exception:
            # we can do nothing when error in execlpe
            # don't logger here, logger need get GIL lock
            # children process may dead lock
            pass
    else:
        _waitpid(pid)

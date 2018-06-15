import hashlib
import logging
import os
import threading
import time
import types
import uuid
from collections import namedtuple

from kazoo import security
from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError

from pykit import config
from pykit import net
from pykit import utfjson

from .exceptions import ZKWaitTimeout

logger = logging.getLogger(__name__)

PERM_TO_LONG = {
    'c': 'create',
    'd': 'delete',
    'r': 'read',
    'w': 'write',
    'a': 'admin',
}

PERM_TO_SHORT = {
    'create': 'c',
    'delete': 'd',
    'read': 'r',
    'write': 'w',
    'admin': 'a',
}

# We assumes that ip does not change during process running.
# Display intra ip if presents, or display pub ip.
host_ip4 = net.ips_prefer(net.get_host_ip4(), net.INN)


class PermTypeError(Exception):
    pass


def lock_data(node_id=None):
    # deprecated
    return lock_id(node_id=node_id)


def lock_id(node_id=None):
    """
    Embed lock holder information into the zk node data for the lock.

    `node_id` is a user defined identifier of a host.
    """

    if node_id is None:
        node_id = config.zk_node_id

    ip = (host_ip4 + ['unknownip'])[0]

    seq = [node_id, ip, str(os.getpid()), str(uuid.uuid4()).replace('-', '')]

    return '-'.join(seq)


def parse_lock_data(data_str):
    # deprecated
    return parse_lock_id(data_str)


def parse_lock_id(data_str):
    """
    Parse string generated by lock_id()
    """

    node_id, ip, process_id, _uuid = (data_str.split('-', 3) + ([None] * 4))[:4]

    if type(process_id) in types.StringTypes and process_id.isdigit():
        process_id = int(process_id)
    else:
        process_id = None

    rst = {
        'node_id': node_id,
        'ip': ip,
        'process_id': process_id,
        'uuid': _uuid,
        'txid': None
    }

    if node_id.startswith('txid:'):
        rst['txid'] = node_id.split(':', 1)[1]

    return rst


def make_digest(acc):
    # acc = "username:password"

    digest = hashlib.sha1(acc).digest().encode('base64').strip()
    return digest


def make_acl_entry(username, password, permissions):

    perms = ''
    for c in permissions:
        if c not in PERM_TO_LONG:
            raise PermTypeError(c)
        perms += c

    return "digest:{username}:{digest}:{permissions}".format(
        username=username,
        digest=make_digest(username + ":" + password),
        permissions=perms)


def perm_to_long(short, lower=True):

    rst = []

    for c in short:
        c = c.lower()
        if c not in PERM_TO_LONG:
            raise PermTypeError(c)

        rst.append(PERM_TO_LONG[c])

    if not lower:
        rst = [x.upper() for x in rst]

    return rst


def perm_to_short(lst, lower=True):

    rst = ''

    for p in lst:
        p = p.lower()
        if p not in PERM_TO_SHORT:
            raise PermTypeError(p)

        rst += PERM_TO_SHORT[p]

    if not lower:
        rst = rst.upper()

    return rst


def make_kazoo_digest_acl(acl):

    # acl = (('xp', '123', 'cdrwa'),
    #        ('foo', 'passw', 'rw'),
    # )

    if acl is None:
        return None

    rst = []
    for name, passw, perms in acl:
        perm_dict = {p: True
                     for p in perm_to_long(perms)}
        acl_entry = security.make_digest_acl(name, passw, **perm_dict)
        rst.append(acl_entry)

    return rst


def parse_kazoo_acl(acls):

    # acls = [ACL(perms=31,
    #            acl_list=['ALL'],
    #            id=Id(scheme='digest', id=u'user:+Ir5sN1lGJEEs8xBZhZXK='))]

    rst = []
    for acl in acls:
        if 'ALL' in acl.acl_list:
            acl_list = 'cdrwa'
        else:
            acl_list = perm_to_short(acl.acl_list)

        rst.append((acl.id.scheme, acl.id.id.split(':')[0], acl_list))

    return rst


def is_backward_locking(locked_keys, key):

    locked_keys = sorted(locked_keys)
    assert key not in locked_keys, 'must not re-lock a key'

    if len(locked_keys) == 0:
        is_backward = False
    else:
        is_backward = key < locked_keys[-1]

    return is_backward


def _init_node(zkcli, parent_path, node, val, acl, users):

    path = parent_path + '/' + node

    if acl is None:
        acls = zkcli.get_acls(parent_path)[0]
    else:
        acls = [(user, users[user], perms) for user, perms in acl.items()]
        acls = make_kazoo_digest_acl(acls)

    if zkcli.exists(path) is None:
        zkcli.create(path, value=val, acl=acls)
    else:
        zkcli.set_acls(path, acls)

    return path


def init_hierarchy(hosts, hierarchy, users, auth):

    zkcli = KazooClient(hosts)
    zkcli.start()

    scheme, name, passw = auth
    zkcli.add_auth(scheme, name + ':' + passw)

    def _init_hierarchy(hierarchy, parent_path):

        if len(hierarchy) == 0:
            return

        for node, attr_children in hierarchy.items():
            val = attr_children.get('__val__', {})
            val = utfjson.dump(val)
            acl = attr_children.get('__acl__')

            path = _init_node(zkcli, parent_path, node, val, acl, users)
            children = {k: v
                        for k, v in attr_children.items()
                        if k not in ('__val__', '__acl__')
                        }

            _init_hierarchy(children, path)

    _init_hierarchy(hierarchy, '/')
    zkcli.stop()


NeedWait = namedtuple('NeedWait', [])


def _conditioned_get_loop(zkclient, path, conditioned_get, timeout=None, **kwargs):

    if timeout is None:
        timeout = 86400 * 365

    expire_at = time.time() + timeout
    lck = threading.RLock()
    maybe_available = threading.Event()
    maybe_available.clear()

    def set_available():
        with lck:
            maybe_available.set()

    def on_connection_change(state):
        # notify it to re-get, then raise Connection related error
        logger.info('connection state change: {0}'.format(state))
        set_available()

    zkclient.add_listener(on_connection_change)

    try:
        while True:

            with lck:
                it = conditioned_get(zkclient, path, **kwargs)
                it.next()
                rst = it.send((NeedWait, set_available))

                if rst is NeedWait:
                    maybe_available.clear()
                else:
                    return rst

            if maybe_available.wait(expire_at - time.time()):
                continue

            raise ZKWaitTimeout("timeout({timeout} sec)"
                                " waiting for {path} to satisfy: {cond}".format(
                                    timeout=timeout,
                                    path=path,
                                    cond=str(kwargs)))
    finally:
        try:
            zkclient.remove_listener(on_connection_change)
        except Exception as e:
            logger.info(repr(e) + ' while removing on_connection_change')


def make_conditioned_getter(conditioned_get):

    def _wrap(zkclient, path, timeout=None, **kwargs):
        return _conditioned_get_loop(zkclient, path, conditioned_get, timeout=timeout, **kwargs)

    _wrap.__name__ = conditioned_get.__name__

    return _wrap


@make_conditioned_getter
def get_next(zkclient, path, version=-1):

    NeedWait, set_available = yield

    val, zstat = zkclient.get(path, watch=lambda watchevent: set_available())
    if zstat.version > version:
        yield val, zstat

    yield NeedWait


@make_conditioned_getter
def wait_absent(zkclient, path):

    NeedWait, set_available = yield

    try:
        zkclient.get(path, watch=lambda watchevent: set_available())
    except NoNodeError as e:
        logger.info(repr(e) + ' found, return')
        yield None

    yield NeedWait

#!/usr/bin/env python2
# coding: utf-8

import urlparse
from pykit import net

checksum_algorithms = {
        'md5': {'len': 32},
        'sha1': {'len': 40},
        'sha256': {'len': 64},
}

def _url(s):
    pass



def _checksum(s=None):

    if s is None:
        return None

    algo, chksum = s.split(':', 1)

    if algo not in checksum_algorithms:
        raise ValueError('invalid checksum algorithm: {a} accepts: {aa}'.format(
                a=algo, aa=checksum_algorithms))

    if len(chksum) != checksum_algorithms[algo]:
        raise ValueError('invalid checksum length: {l} expected {exp} for {algo}'.format(
                l=len(chksum),
                exp=checksum_algorithms[algo],
                algo=algo))

    return {'algo': algo, 'actual': chksum}

class ListItem(FixedKeysDict):

    keys_default = dict(
            filename=str,       # "mysql-5.7.13-linux-glibc2.5-x86_64.tar.gz"
            url=_url,           # "http://{{ package_host }}/{{ package_bucket }}/mysql-5.7.13-linux-glibc2.5-x86_64.tar.gz"
            checksum=_checksum, # "sha1:4345267d081f2a74a30dc96bc310fa74d9a396c9"
    )

    ident_keys = ('filename', )


def sync_down(lst, target_dir='.'):
    for it in lst:
        path = os.path.join(target_dir, it['filename'])
        if not os.path.exists(path):
            # TODO https

            src = urlparse.urlparse(it['url'])
            if net.is_ip4(src.hostname):
                ip = src.hostname
            else:
                rst = socket.gethostbyname_ex(src.hostname)
                # ('u100.v.qingcdn.com',
                #  ['s2.i.qingcdn.com', 's2.i.qingcdn.com.qingcdn.com'],
                #  ['115.238.170.171',
                #  ...
                #   '115.238.170.169',
                #   '115.238.170.170']
                # )

                ips = rst[3]
                ip = ips[0]

            h = http.Client(ip, src.port or 80)
            status, headers = h.request(src.uri + '?' + src.query)


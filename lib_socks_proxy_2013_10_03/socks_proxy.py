# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2013, 2014, 2015 Andrej Antonov <polymorphm@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

assert str is not bytes

import weakref
import struct
import socket
from . import core_monkey_patch

DEFAULT_PROXY_TIMEOUT = 60.0

_real_dest_address_map = weakref.WeakKeyDictionary()

class SocksProxyError(Exception):
    pass

class RecvError(SocksProxyError):
    pass

class ArgSocksProxyError(SocksProxyError):
    pass

class FormatSocksProxyError(SocksProxyError):
    pass

class AuthSocksProxyError(SocksProxyError):
    pass

class ConnectSocksProxyError(SocksProxyError):
    pass

def recv_all_into(sock, buf):
    buf = memoryview(buf)
    recv_res = 0
    
    while recv_res < len(buf):
        if recv_res > 0:
            buf = buf[recv_res:]
        recv_res = sock.recv_into(buf)
        if not recv_res:
            raise RecvError('SOCKS-proxy socket is unexpectedly closed')

def get_real_dest_address(sock):
    return _real_dest_address_map.get(sock)

def socks_proxy_create_connection(
        address,
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
        source_address=None,
        **kwargs):
    core_monkey_patch.assert_patched()
    
    proxy_address = kwargs['proxy_address']
    proxy_timeout = kwargs.get('proxy_timeout')
    proxy_source_address = kwargs.get('proxy_source_address')
    
    assert proxy_address is not None
    
    if not isinstance(address, (tuple, list)) or \
            len(address) != 2 or \
            not isinstance(address[0], str) or \
            not isinstance(address[1], int):
        raise ArgSocksProxyError(
                'address of connection must be tuple: hostname (str) and port (int)'
                )
    
    hostname, port = address
    proxy_kwargs = {}
    
    if proxy_timeout is not None:
        proxy_kwargs['timeout'] = proxy_timeout
    else:
        proxy_kwargs['timeout'] = DEFAULT_PROXY_TIMEOUT
    
    if proxy_source_address is not None:
        proxy_kwargs['source_address'] = proxy_source_address
    
    sock = core_monkey_patch.original_create_connection(proxy_address, **proxy_kwargs)
    
    # SOCKS5: greeting phase
    
    sock.sendall(struct.pack(
            '!BBB',
            0x05, # SOCKS version number (must be 0x05 for this version)
            0x01, # number of authentication methods supported
            0x00, # authentication methods: no authentication
            ))
    
    recv_data = bytearray(2)
    recv_all_into(sock, recv_data)
    recv_data = struct.unpack('!BB', recv_data)
    
    if (recv_data[0] != 0x05):
        raise FormatSocksProxyError('invalid SOCKS-proxy format (SOCKS5: greeting phase)')
    
    if (recv_data[1] != 0x00):
        raise AuthSocksProxyError('invalid SOCKS-proxy authorization (SOCKS5: greeting phase)')
    
    # SOCKS5: command phase
    
    sock.sendall(
            struct.pack(
                    '!BBB',
                    0x05, # SOCKS version number (must be 0x05 for this version)
                    0x01, # establish a TCP/IP stream connection
                    0x00, # reserved, must be 0x00
                    ),
            )
    
    assert len(address) == 2
    assert isinstance(address[0], str)
    assert isinstance(address[1], int)
    
    try:
        host_ipv6 = socket.inet_pton(socket.AF_INET6, address[0])
    except OSError:
        host_ipv6 = None
    try:
        host_ipv4 = socket.inet_pton(socket.AF_INET, address[0])
    except OSError:
        host_ipv4 = None
    
    if host_ipv6 is not None:
        # IPv6
        
        assert len(host_ipv6) == 16
        
        sock.sendall(
                struct.pack(
                        '!B',
                        0x04, # address type: IPv6 address
                        )
                +
                host_ipv6
                )
    elif host_ipv4 is not None:
        # IPv4
        
        assert len(host_ipv4) == 4
        
        sock.sendall(
                struct.pack(
                        '!B',
                        0x01, # address type: IPv4 address
                        )
                +
                host_ipv4
                )
    else:
        # Domain name
        
        host_bytes = address[0].encode()
        sock.sendall(
                struct.pack(
                        '!BB',
                        0x03, # address type: Domain name
                        len(host_bytes), # Domain name length
                        )
                +
                host_bytes
                )
    
    sock.sendall(
            struct.pack(
                    '!H',
                    address[1], # port number
                    )
            )
    
    recv_data = bytearray(2)
    recv_all_into(sock, recv_data)
    recv_data = struct.unpack('!BB', recv_data)
    
    if (recv_data[0] != 0x05):
        raise FormatSocksProxyError('invalid SOCKS-proxy format (SOCKS5: command phase)')
    
    if (recv_data[1] != 0x00):
        error_descr = recv_data[1]
        
        if recv_data[1] == 0x01:
            error_descr = 'general failure'
        elif recv_data[1] == 0x02:
            error_descr = 'connection not allowed by ruleset'
        elif recv_data[1] == 0x03:
            error_descr = 'network unreachable'
        elif recv_data[1] == 0x04:
            error_descr = 'host unreachable'
        elif recv_data[1] == 0x05:
            error_descr = 'connection refused by destination host'
        elif recv_data[1] == 0x06:
            error_descr = 'TTL expired'
        elif recv_data[1] == 0x07:
            error_descr = 'command not supported / protocol error'
        elif recv_data[1] == 0x08:
            error_descr = 'address type not supported'
        else:
            error_descr = hex(recv_data[1])
        
        raise ConnectSocksProxyError(
                'SOCKS-proxy can not create connection: {!r} (SOCKS5: command phase)'.format(
                        error_descr,
                        ))
    
    recv_data = bytearray(2)
    recv_all_into(sock, recv_data)
    recv_data = struct.unpack('!BB', recv_data)
    
    if recv_data[1] == 0x01:
        host_recv_type = 'ipv4'
        host_recv_data = bytearray(4)
        recv_all_into(sock, host_recv_data)
    elif recv_data[1] == 0x03:
        host_recv_type = 'domain'
        
        host_len_recv_data = bytearray(1)
        recv_all_into(sock, host_len_recv_data)
        host_len_recv_data = struct.unpack('!B', host_len_recv_data)
        
        host_recv_data = bytearray(host_len_recv_data[0])
        recv_all_into(sock, host_recv_data)
    elif recv_data[1] == 0x04:
        host_recv_type = 'ipv6'
        host_recv_data = bytearray(16)
        recv_all_into(sock, host_recv_data)
    else:
        raise FormatSocksProxyError('invalid SOCKS-proxy format (SOCKS5: command phase)')
    
    port_recv_data = bytearray(2)
    recv_all_into(sock, port_recv_data)
    port_recv_data = struct.unpack('!H', port_recv_data)
    
    _real_dest_address_map[sock] = \
            host_recv_type, bytes(host_recv_data), port_recv_data[0]
    
    # SOCKS5: end phase. connection is complete. tuning socket and return it
    
    if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
        sock.settimeout(timeout)
    else:
        sock.settimeout(socket.getdefaulttimeout())
    
    return sock

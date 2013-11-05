# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2013 Andrej Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

assert str is not bytes

import threading
import contextlib
from . import monkey_patch
from . import socks_proxy

_thread_local = threading.local()

def get_socks_proxy_context_stack():
    try:
        socks_proxy_context_stack = _thread_local.socks_proxy_context_stack
    except AttributeError:
        socks_proxy_context_stack = _thread_local.socks_proxy_context_stack = []
    
    return socks_proxy_context_stack

def context_create_connection(*args, **kwargs):
    monkey_patch.assert_patched()
    
    socks_proxy_context_stack = get_socks_proxy_context_stack()
    
    if not socks_proxy_context_stack:
        return monkey_patch.original_create_connection(*args, **kwargs)
    
    socks_proxy_info = socks_proxy_context_stack[len(socks_proxy_context_stack) - 1]
    
    if socks_proxy_info is None:
        return monkey_patch.original_create_connection(*args, **kwargs)
    
    kwargs.update(socks_proxy_info)
    
    return socks_proxy.socks_proxy_create_connection(*args, **kwargs)

@contextlib.contextmanager
def socks_proxy_context(**kwargs):
    monkey_patch.assert_patched()
    
    socks_proxy_context_stack = get_socks_proxy_context_stack()
    
    if kwargs:
        socks_proxy_context_stack.append(kwargs)
    else:
        socks_proxy_context_stack.append(None)
    try:
        yield
    finally:
        socks_proxy_context_stack.pop()

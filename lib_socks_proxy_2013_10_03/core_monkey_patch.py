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

# XXX nothing import when initialising this module! it is important!

original_create_connection = None

def assert_patched():
    assert original_create_connection is not None, \
            'socket.create_connection not patched yet'

def patched_create_connection(*args, **kwargs):
    assert_patched()
    
    from . import socks_proxy_context
    from . import socks_proxy
    
    socks_proxy_context_stack = socks_proxy_context.get_socks_proxy_context_stack()
    
    if not socks_proxy_context_stack:
        return monkey_patch.original_create_connection(*args, **kwargs)
    
    socks_proxy_info = socks_proxy_context_stack[len(socks_proxy_context_stack) - 1]
    
    if socks_proxy_info is None:
        return monkey_patch.original_create_connection(*args, **kwargs)
    
    kwargs.update(socks_proxy_info)
    
    return socks_proxy.socks_proxy_create_connection(*args, **kwargs)

def core_monkey_patch():
    # XXX careful import. nothing extra!
    
    import socket
    
    global original_create_connection
    
    if original_create_connection is not None:
        return
    
    original_create_connection = socket.create_connection
    socket.create_connection = patched_create_connection

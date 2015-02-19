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

import threading
import contextlib
from . import core_monkey_patch

_thread_local = threading.local()

def get_socks_proxy_context_stack():
    try:
        socks_proxy_context_stack = _thread_local.socks_proxy_context_stack
    except AttributeError:
        socks_proxy_context_stack = _thread_local.socks_proxy_context_stack = []
    
    return socks_proxy_context_stack

@contextlib.contextmanager
def socks_proxy_context(**kwargs):
    core_monkey_patch.assert_patched()
    
    socks_proxy_context_stack = get_socks_proxy_context_stack()
    
    if kwargs:
        socks_proxy_context_stack.append(kwargs)
    else:
        socks_proxy_context_stack.append(None)
    try:
        yield
    finally:
        socks_proxy_context_stack.pop()

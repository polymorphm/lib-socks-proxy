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

# XXX nothing import when initialising this module! it is important!

original_create_connection = None

def assert_patched():
    assert original_create_connection is not None, \
            'socket.create_connection not patched yet'

def patched_create_connection(*args, **kwargs):
    from . import socks_proxy_context
    
    return context_create_connection.context_create_connection(*args, **kwargs)

def monkey_patch():
    # XXX careful import. nothing extra!
    
    import socket
    
    global original_create_connection
    
    if original_create_connection is not None:
        return
    
    original_create_connection = socket.create_connection
    socket.create_connection = patched_create_connection

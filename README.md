lib-socks-proxy
===============

`lib-socks-proxy` -- it is a Python (Python-3.X) library for connection via SOCKS5-proxy.

It is very small (poor) library, but it has next features:

*   Certain сompatibility with other modules (including standard module ``urllib.request``).

*   Not used any global settings.

*   Used context settings (Python keyword ``with``).

*   Safe for multithreading.

*   No stupid problem with ``IPv6`` or ``timeout``.

*   No DNS-Leak when using Tor Project (or problems with ``.onion`` DNS-Zone).

Status
------

Version for developer.

Using
-----

Simple example of using:

    $ cat EXAMPLE-1
    #!/usr/bin/env python3
    # -*- mode: python; coding: utf-8 -*-
    
    assert str is not bytes
    
    from lib_socks_proxy_2013_10_03 import monkey_patch as socks_proxy_monkey_patch
    
    # XXX ``monkey_patch()`` must be run before other imports
    socks_proxy_monkey_patch.monkey_patch()
    
    from urllib import request as url_request
    from lib_socks_proxy_2013_10_03 import socks_proxy_context
    
    if __name__ == '__main__':
        opener = url_request.build_opener()
        
        with socks_proxy_context.socks_proxy_context(proxy_address=('127.0.0.1', 9050)):
            res = opener.open('https://internet.yandex.com/get_full_info/', timeout=20.0)
        
        data = res.read(10000).decode()
        
        print(data)

Result:

    $ ./EXAMPLE-1

    -------------------------------------------------------
    Yandex internet.yandex.ru
    -------------------------------------------------------
    11.11.2013   03:45

    #  Congratulations, you're online!  #

    ip: 85.10.211.53
    ipv6: -
    This is Moscow


    browser              : Unknown Unknown 
    operating system     : Unknown Unknown 

    cookies              : no

Example of using with threads:

    $ cat EXAMPLE-2
    #!/usr/bin/env python3
    # -*- mode: python; coding: utf-8 -*-
    
    assert str is not bytes
    
    from lib_socks_proxy_2013_10_03 import monkey_patch as socks_proxy_monkey_patch
    
    # XXX ``monkey_patch()`` must be run before other imports
    socks_proxy_monkey_patch.monkey_patch()
    
    import threading
    from urllib import request as url_request
    from lib_socks_proxy_2013_10_03 import socks_proxy_context
    
    def proxy_thread(ui_lock, proxy_address, url):
        # make request with using SOCKS proxy
        
        opener = url_request.build_opener()
        with socks_proxy_context.socks_proxy_context(proxy_address=proxy_address):
            res = opener.open(url, timeout=20.0)
        data = res.read(10000).decode()
        
        with ui_lock:
            print('*** BEGIN result of proxy_thread() ***')
            print(data)
            print('*** END result of proxy_thread() ***')
    
    def non_proxy_thread(ui_lock, url):
        # make request without proxy
        
        opener = url_request.build_opener()
        res = opener.open(url, timeout=20.0)
        data = res.read(10000).decode()
        
        with ui_lock:
            print('*** BEGIN result of non_proxy_thread() ***')
            print(data)
            print('*** END result of non_proxy_thread() ***')
    
    if __name__ == '__main__':
        ui_lock = threading.RLock()
        
        proxy_thr = threading.Thread(
                target=lambda: proxy_thread(
                        ui_lock,
                        ('127.0.0.1', 9050),
                        'https://internet.yandex.com/get_full_info/',
                        ),
                )
        non_proxy_thr = threading.Thread(
                target=lambda: non_proxy_thread(
                        ui_lock,
                        'https://internet.yandex.com/get_full_info/',
                        ),
                )
        
        proxy_thr.start()
        non_proxy_thr.start()
        
        proxy_thr.join()
        non_proxy_thr.join()

Result:

    $ ./EXAMPLE-2
    *** BEGIN result of non_proxy_thread() ***

    -------------------------------------------------------
    Yandex internet.yandex.ru
    -------------------------------------------------------
    11.11.2013   01:38

    #  Congratulations, you're online!  #

    ip: 94.181.132.16
    ipv6: -
    This is Penza


    browser              : Unknown Unknown 
    operating system     : Unknown Unknown 

    cookies              : no

    *** END result of non_proxy_thread() ***
    *** BEGIN result of proxy_thread() ***

    -------------------------------------------------------
    Yandex internet.yandex.ru
    -------------------------------------------------------
    11.11.2013   01:38

    #  Congratulations, you're online!  #

    ip: 204.124.83.130
    ipv6: -
    This is Moscow


    browser              : Unknown Unknown 
    operating system     : Unknown Unknown 

    cookies              : no

    *** END result of proxy_thread() ***

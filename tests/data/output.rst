===============================
Comparing test1.tar & test2.tar
===============================

---------
file list
---------

::

    @@ -1,4 +1,4 @@
    -drwxr-xr-x   0 lunar     (1000) lunar     (1000)        0 2015-06-29 15:49:09.000000 dir/
    --rw-r--r--   0 lunar     (1000) lunar     (1000)      446 2015-06-29 15:49:09.000000 dir/text
    -crw-r--r--   0 root         (0) root         (0)    1,  3 2015-06-29 15:49:09.000000 dir/null
    -lrwxrwxrwx   0 lunar     (1000) lunar     (1000)        0 2015-06-29 15:49:09.000000 dir/link -> broken
    +drwxr-xr-x   0 lunar     (1000) lunar     (1000)        0 2015-06-29 15:49:41.000000 dir/
    +-rw-r--r--   0 lunar     (1000) lunar     (1000)      671 2015-06-29 15:49:41.000000 dir/text
    +crw-r--r--   0 root         (0) root         (0)    1,  3 2015-06-29 15:49:41.000000 dir/null
    +lrwxrwxrwx   0 lunar     (1000) lunar     (1000)        0 2015-06-29 15:49:41.000000 dir/link -> really-broken

--------
dir/text
--------

::

    @@ -1,6 +1,12 @@
    +A common form of lorem ipsum reads:
    +
     Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
     incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
     nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
     Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
     fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
     culpa qui officia deserunt mollit anim id est laborum.
    +
    +"Lorem ipsum" text is derived from sections 1.10.32--3 of Cicero's De finibus
    +bonorum et malorum (On the Ends of Goods and Evils, or alternatively [About]
    +The Purposes of Good and Evil).

--------
dir/link
--------


symlink
::

    @@ -1 +1 @@
    -destination: broken
    +destination: really-broken


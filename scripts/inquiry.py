#!/usr/bin/python
# -*- coding: utf-8 -*-

# file: inquiry.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: performs a simple device inquiry followed by a remote name request of
#       each discovered device
# $Id: inquiry.py 401 2006-05-05 19:07:48Z albert $
#

import bluetooth
import time

i = 0
while True:

  i = i + 1

  print("performing inquiry...(%d)" % i)

  nearby_devices = bluetooth.discover_devices(
        duration=3, lookup_names=True, flush_cache=True)
        # duration=8, lookup_names=True, flush_cache=True)

  print("found %d devices" % len(nearby_devices))

  for addr, name in nearby_devices:
    try:
      print("  %s - %s" % (addr, name))
    except UnicodeEncodeError:
      print("  %s - %s" % (addr, name.encode('utf-8', 'replace')))

  time.sleep(3)

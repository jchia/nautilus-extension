#!/usr/bin/python

import gobject 
import gst
from gst.extend import discoverer
import os
import sys

gobject.threads_init()
main_loop = gobject.MainLoop() 

def human_readable_size(size):
    if size == 0:
        return '0B'
    assert size >= 1
    good = (pair for pair in human_readable_size.denominations if size >= pair[0])
    while True:
        try:
            selected = good.next()
        except StopIteration:
            break
    return '{:.1f}{}'.format(float(size) / selected[0], selected[1])

human_readable_size.denominations = [(1, 'B'), (1 << 10, 'kB'), (1 << 20, 'MB'), (1 << 30, 'GB')]

def on_discovered(discoverer, is_media, size):
    if discoverer.is_video:
        seconds = discoverer.videolength / gst.SECOND
        print 'V {}x{} {}s {}/s'.format(discoverer.videowidth, discoverer.videoheight, seconds, human_readable_size(size / seconds))
    elif discoverer.is_audio:
        seconds = discoverer.audiolength / gst.SECOND
        print 'A {}s {}/s'.format(seconds, human_readable_size(size / seconds))
    main_loop.quit()

d = discoverer.Discoverer(sys.argv[1])
d.connect('discovered', on_discovered, os.stat(sys.argv[1]).st_size)
gobject.idle_add(d.discover) 
main_loop.run()

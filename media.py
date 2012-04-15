import gobject
import gst
from gst.extend import discoverer
import os
import urllib

from gi.repository import GObject, Nautilus

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

def on_discovered(discoverer, is_media, extension, size):
    if discoverer.is_video:
        seconds = discoverer.videolength / gst.SECOND
        extension.complete(seconds, human_readable_size(size / seconds), discoverer.videowidth, discoverer.videoheight)
    elif discoverer.is_audio:
        seconds = discoverer.audiolength / gst.SECOND
        extension.complete(seconds, human_readable_size(size / seconds))

class MediaExtension(GObject.GObject, Nautilus.ColumnProvider, Nautilus.InfoProvider):
    def __init__(self):
        pass

    def get_columns(self):
        return [Nautilus.Column(name="NautilusPython::duration",
                                attribute="duration",
                                label="Duration",
                                description="Get the video/audio duration"),
                Nautilus.Column(name="NautilusPython::byte_rate",
                                attribute="byte_rate",
                                label="Duration",
                                description="Get the video/audio bytes per second"),
                Nautilus.Column(name="NautilusPython::resolution",
                                attribute="resolution",
                                label="Resolution",
                                description="Get the video resolution")]

    def complete(duration, byte_rate, width=None, height=None):
        self._duration = duration
        self._byte_rate = byte_rate
        self._width = width
        self._height = height

        self._cv.acquire()
        self._complete = True;
        self._cv.notify()
        _needed -=1
        if _needed == 0:
            main_loop.quit()

    _needed = 0;
    # TODO: use mimetype instead?
    _accepted_extensions = set(('avi', 'wmv', 'mkv', 'mp4', 'mov', 'm3'))
    def update_file_info(self, file):
        if file.get_uri_scheme() != 'file':
            return
        filename = urllib.unquote(file.get_uri()[7:])
        parts = filename.split('.')
        if len(parts) < 2:
            return
        if str.lower(parts[-1]) not in _accepted_extensions:
            return
        d = discoverer.Discoverer(filename)
        self._cv = threading.Condition()
        self._complete = False
        d.connect('discovered', on_discovered, self, os.stat(sys.argv[1]).st_size)
        gobject.idle_add(d.discover) 
        _needed += 1
        if _needed == 1:
            main_loop.run()
        self._cv.acquire()
        self._cv.wait()
        while not self._complete:
            self._cv.wait()
        self._cv.release()
        file.add_string_attribute('duration', self._duration)
        file.add_string_attribute('byte rate', self._byte_rate)
        if self._width:
            file.add_string_attribute('resolution', '{}x{}'.format(self._width, self._height))

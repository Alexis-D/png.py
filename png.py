#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""This module contains only one important class: PNG which
may be used to encode image into a PNG bytestring.

Assuming that you have a variable data which is a 2-dimension
list containing tuples, e.g:
>>> import png
>>> data = [[(0xff, 0x00, 0xff), (0x00, 0xff, 0xff)]]
>>> writer = png.PNG(width=2, height=1)
>>> writer.bit_depth = 8
>>> with open('out.png', 'wb') as f:
...     f.write(writer.bytes(data))
... 
70
>>> 

Produce a 2x1 PNG in out.png with the left most pixel 0xff00ff and
the rightmost one 0x00ffff.
"""

import io
import struct
import zlib

__all__ = ['PNGException', 'PNG']
__author__ = 'Alexis Daboville'

def paeth(a, b, c):
    """Simple implementation of http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth

    (nearly c/p the pseudo-code)

    """
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)

    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    return c


class PNGException(Exception):
    pass


class PNG(object):
    """This class is used to encode an image into a PNG.

    Implements:
    * True colours
    * w/ or w/o alpha channel
    * 8 or 16 bits depth
    * Different filter types (none, sub, up, avg, paeth)

    Maybe:
    * Interlacing
    * Split compressed in multiple IDAT chunks, easy to do, but useful?
      Waste of space?

    Won't be implemented:
    * B&W images
    * Indexed colours (PLTE chunk)
    * Optionnal headers (e.g. tEXt)

    http://www.w3.org/TR/PNG/

    """

    # network byte order (big endian)
    # http://www.w3.org/TR/PNG/#7Integers-and-byte-order

    def __init__(self,
                 width=None,
                 height=None,
                 alpha=False,
                 bit_depth=8,
                 compression_level=7,
                 filter_type=4):
        """Initialize the PNG writer.

        Each argument corresponds to its property. So look
        at the properties documentation.

        """
        self._w = width
        self._h = height
        self.alpha = alpha
        self.bit_depth = bit_depth
        self.compression_level = compression_level
        self.filter_type = filter_type

        # not customizable for now
        self._interlace = 0 # none

        # the standard doesn't define other methods
        self._compression = 0
        self._filter = 0

    def _get_chunk(self, type, data):
        """Return a complete chunk with of type type and with data data.

        A complete chunk is made of:
        length (data field) -> type -> data -> crc (data field)

        type: should be a four-bytes bytestring, e.g. b'IHDR'
        data: should be a bytestring

        cf. http://www.w3.org/TR/PNG/#5Chunk-layout

        """
        if len(type) != 4:
            raise PNGException('Type of a chunk should be of 4 bytes wide.')

        length = struct.pack('!I', len(data))

        typedata = type + data

        # http://www.w3.org/TR/PNG/#5CRC-algorithm
        crc = zlib.crc32(typedata)
        crc = struct.pack('!I', crc)

        return b''.join((length, typedata, crc))

    def _get_ihdr(self):
        """Return the IHDR chunk.

        cf. http://www.w3.org/TR/PNG/#11IHDR

        """
        ihdr_data = struct.pack(
            '!2I5B', self.width, self.height, self.bit_depth,
            self._colour_type, self._compression, self._filter,
            self._interlace)
        return self._get_chunk(b'IHDR', ihdr_data)

    def _data_to_bytes(self, data):
        """Convert the raw image data to a list of bytestrings (scanlines)."""
        _data = []
        fmt = '!%d%s' % (self._channels, self._channel_fmt)

        for row in data:
            if(any(len(color) != self._channels for color in row)):
                raise PNGException("Some pixels in data doesn't use %d "
                                   "channels. " % self._channels)

            _data.append(b''.join(struct.pack(fmt, *color) for color in row))

        return _data

    def _apply_filter(self, type, data, fn):
        """Apply the filter fn of type type to data.

        fn is a callable which takes four args: fn(x, a, b, c)
        where x, a, b, c are defined by the standard:
        http://www.w3.org/TR/PNG/#9Filter-types

        """
        # if we need it it should be full of 0's
        upper = b'\x00' * self._bytes_per_pixel * self.width

        with io.BytesIO() as filtered:
            for scanline in data:
                filtered.write(type)

                with io.BytesIO(scanline) as buffer,\
                     io.BytesIO(upper) as upper_buffer:
                    a = [0x00,] * self._bytes_per_pixel
                    c = [0x00,] * self._bytes_per_pixel

                    while True:
                        # for each pixel (and each pixel in the upper row)
                        current = buffer.read(self._bytes_per_pixel)
                        upper_current = upper_buffer.read(self._bytes_per_pixel)

                        # EOF
                        if not current:
                            break

                        for i, x in enumerate(current):
                            b = upper_current[i]
                            filt_x = fn(x, a[i], b, c[i]) & 0xff
                            filtered.write(struct.pack('B', filt_x))

                            # a & c are "previous"/left value so the next
                            # a & c correspond to the current x & b
                            a[i] = x
                            c[i] = b

                upper = scanline

            return filtered.getvalue()

    def _filter_and_compress(self, data):
        """Filter and compress data (bytestring)."""
        if self._filter == 0:
            # http://www.w3.org/TR/PNG/#9-table91
            if self._filter_type == 0:
                # no filter
                filtered = self._apply_filter(
                    b'\x00', data, lambda x, a, _, __: x)

            elif self._filter_type == 1:
                # sub
                filtered = self._apply_filter(
                    b'\x01', data, lambda x, a, _, __: x - a)

            elif self._filter_type == 2:
                # up
                filtered = self._apply_filter(
                    b'\x02', data, lambda x, _, b, __: x - b)

            elif self._filter_type == 3:
                # average
                filtered = self._apply_filter(
                    b'\x03', data, lambda x, a, b, __: x - (a + b) // 2)

            elif self._filter_type == 4:
                # paeth
                filtered = self._apply_filter(
                    b'\x04', data, lambda x, a, b, c: x - paeth(a, b, c))

        else:
            raise PNGException('Unsupported filter method.')

        # http://www.w3.org/TR/PNG/#10Compression
        if self._compression == 0:
            compressed = zlib.compress(filtered, self.compression_level)
        else:
            raise PNGException('Unsupported compression method.')

        return compressed

    def bytes(self, data):
        """Return the image represented by data as a PNG byte string.

        data: two dimensional array (height, width) where each item is a tuple
              representing the color of the pixel like that:
              (r, g, b) is alpha isn't used
              (r, g, b, a) otherwise.
              r, g, b & a should be >= 0 and < 2 ** bit_depth

        """
        # Notes:
        # * there's no way to implement the buffer interface in plain Python :(

        if any(len(scanline) != self.width for scanline in data):
            raise PNGException('Width is inconsistent.')

        if self.height != len(data):
            raise PNGException('Height is inconsistent.')

        with io.BytesIO() as buffer:
            # PNG magic numbers/header
            # http://www.w3.org/TR/PNG/#5PNG-file-signature
            buffer.write(b'\x89PNG\r\n\x1a\n')
            buffer.write(self._get_ihdr())

            # http://www.w3.org/TR/PNG/#11IDAT
            compressed = self._filter_and_compress(self._data_to_bytes(data))
            buffer.write(self._get_chunk(b'IDAT', compressed))

            # http://www.w3.org/TR/PNG/#11IEND
            buffer.write(self._get_chunk(b'IEND', b''))

            return buffer.getvalue()

    @property
    def width(self):
        """Width of the image to encode. Positive integer."""
        if self._w is not None:
            return self._w

        raise PNGException("Width hadn't been set.")

    @width.setter
    def width(self, new_width):
        if new_width <= 0:
            raise PNGException('Width should be positive.')

        self._w = new_width

    @property
    def height(self):
        """Height of the image to encode. Positive integer."""
        if self._h is not None:
            return self._h

        raise PNGException("Height hadn't been set.")


    @height.setter
    def height(self, new_height):
        if new_height <= 0:
            raise PNGException('Height should be positive.')

        self._h = new_height

    alpha = property(lambda self: self._alpha,
                     doc='True if the image use the alpha channel. Boolean.')
    bit_depth = property(lambda self: self._bit_depth,
                         doc='Number of bits per channel per pixel. 8 or 16.')
    compression_level = property(lambda self: self._compression_level,
                                 doc='Compression level of deflate '
                                     'algorithm. Integer between 1 and 9 '
                                     '(both included).')
    filter_type = property(lambda self: self._filter_type,
                           doc='The filter type to use with method 0:\n'
                               '0: no filter\n'
                               '1: sub\n'
                               '2: sup\n'
                               '3: average\n'
                               '4: paeth')

    @alpha.setter
    def alpha(self, new_alpha):
        self._alpha = new_alpha
        self._channels = 4 if self.alpha else 3
        self._colour_type = 6 if self.alpha else 2 # true colours +/- alpha

    @bit_depth.setter
    def bit_depth(self, new_bit_depth):
        if new_bit_depth not in (8, 16):
            raise PNGException('Bit depth should be either 8 or 16.')

        # bit per pixel/channel (not indexed palette)
        self._bit_depth = new_bit_depth
        self._bytes_per_channel = 1 if self.bit_depth == 8 else 2
        self._channel_fmt = 'B' if self.bit_depth == 8 else 'H'

    @compression_level.setter
    def compression_level(self, new_compression_level):
        if not (1 <= new_compression_level <= 9):
            raise PNGException('Compression level should be '
                               'within the range [1, 9].')

        self._compression_level = new_compression_level

    @filter_type.setter
    def filter_type(self, new_filter_type):
        if not (0 <= new_filter_type <= 4):
            raise PNGException('Filter type should be '
                               'within the range [0, 4].')

        self._filter_type = new_filter_type

    _bytes_per_pixel = property(lambda self:
                                self._channels * self._bytes_per_channel)


if __name__ == '__main__':
    w, h = 256, 256
    png = PNG(w, h)
    png.alpha = True
    png.bit_depth = 8
    png.filter_type = 4

    data = []

    for a in range(h):
        row = []
        for b in range(w):
            r = ~(a & b) & 0xff
            g = (a | ~b) & 0xff
            b = (~a & b) & 0xff
            c = (a ^ b) & 0xff
            row.append((r, g, b, c))

        data.append(row)

    with open('hello.png', 'wb') as f:
        f.write(png.bytes(data))


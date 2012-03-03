# png.py - PNG Encoder

## Example :)

This image was encoded with png.py.

![Encoded with png.py](hello.png)

## Features

* True colours
* 8/16 bits depth
* w/ or w/o alpha channel
* Several filter types:
    0. none
    1. sub
    2. up
    3. avg
    4. paeth
* Works with **Python 3** (untested with Python 2, so you can probably use the PIL or pypng).

It doesn't aim to implement the full standard. The goal is rather to have a simple/quick/handy png module to output images. _(That's something I never really understood, despite having an awseome standard library, Python doesn't provide anything to produce images.)_

## Dependencies

None, everything is done using the standard library (thanks to the `io`, `struct` & `zlib` modules).

## How to use?

See the output of `pydoc png`:

    Help on module png:
    
    NAME
        png
    
    DESCRIPTION
        This module contains only one important class: PNG which
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
    
    CLASSES
        builtins.Exception(builtins.BaseException)
            PNGException
        builtins.object
            PNG
        
        class PNG(builtins.object)
         |  This class is used to encode an image into a PNG.
         |  
         |  Implements:
         |  * True colours
         |  * w/ or w/o alpha channel
         |  * 8 or 16 bits depth
         |  * Different filter types (none, sub, up, avg, paeth)
         |  
         |  Maybe:
         |  * Interlacing
         |  * Split compressed in multiple IDAT chunks, easy to do, but useful?
         |    Waste of space?
         |  
         |  Won't be implemented:
         |  * B&W images
         |  * Indexed colours (PLTE chunk)
         |  * Optionnal headers (e.g. tEXt)
         |  
         |  http://www.w3.org/TR/PNG/
         |  
         |  Methods defined here:
         |  
         |  __init__(self, width=None, height=None, alpha=False, bit_depth=8, compression_level=7, filter_type=4)
         |      Initialize the PNG writer.
         |      
         |      Each argument corresponds to its property. So look
         |      at the properties documentation.
         |  
         |  bytes(self, data)
         |      Return the image represented by data as a PNG byte string.
         |      
         |      data: two dimensional array (height, width) where each item is a tuple
         |            representing the color of the pixel like that:
         |            (r, g, b) is alpha isn't used
         |            (r, g, b, a) otherwise.
         |            r, g, b & a should be >= 0 and < 2 ** bit_depth
         |  
         |  ----------------------------------------------------------------------
         |  Data descriptors defined here:
         |  
         |  __dict__
         |      dictionary for instance variables (if defined)
         |  
         |  __weakref__
         |      list of weak references to the object (if defined)
         |  
         |  alpha
         |      True if the image use the alpha channel. Boolean.
         |  
         |  bit_depth
         |      Number of bits per channel per pixel. 8 or 16.
         |  
         |  compression_level
         |      Compression level of deflate algorithm. Integer between 1 and 9 (both included).
         |  
         |  filter_type
         |      The filter type to use with method 0:
         |      0: no filter
         |      1: sub
         |      2: sup
         |      3: average
         |      4: paeth
         |  
         |  height
         |      Height of the image to encode. Positive integer.
         |  
         |  width
         |      Width of the image to encode. Positive integer.
        
        class PNGException(builtins.Exception)
         |  Method resolution order:
         |      PNGException
         |      builtins.Exception
         |      builtins.BaseException
         |      builtins.object
         |  
         |  Data descriptors defined here:
         |  
         |  __weakref__
         |      list of weak references to the object (if defined)
         |  
         |  ----------------------------------------------------------------------
         |  Methods inherited from builtins.Exception:
         |  
         |  __init__(...)
         |      x.__init__(...) initializes x; see help(type(x)) for signature
         |  
         |  ----------------------------------------------------------------------
         |  Data and other attributes inherited from builtins.Exception:
         |  
         |  __new__ = <built-in method __new__ of type object>
         |      T.__new__(S, ...) -> a new object with type S, a subtype of T
         |  
         |  ----------------------------------------------------------------------
         |  Methods inherited from builtins.BaseException:
         |  
         |  __delattr__(...)
         |      x.__delattr__('name') <==> del x.name
         |  
         |  __getattribute__(...)
         |      x.__getattribute__('name') <==> x.name
         |  
         |  __reduce__(...)
         |  
         |  __repr__(...)
         |      x.__repr__() <==> repr(x)
         |  
         |  __setattr__(...)
         |      x.__setattr__('name', value) <==> x.name = value
         |  
         |  __setstate__(...)
         |  
         |  __str__(...)
         |      x.__str__() <==> str(x)
         |  
         |  with_traceback(...)
         |      Exception.with_traceback(tb) --
         |      set self.__traceback__ to tb and return self.
         |  
         |  ----------------------------------------------------------------------
         |  Data descriptors inherited from builtins.BaseException:
         |  
         |  __cause__
         |      exception cause
         |  
         |  __context__
         |      exception context
         |  
         |  __dict__
         |  
         |  __traceback__
         |  
         |  args
    
    DATA
        __all__ = ['PNGException', 'PNG']
    
    AUTHOR
        Alexis Daboville
    
    FILE
        /home/alexis/stuff/png/png.py
    

Or the simple example in png.py:

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
    

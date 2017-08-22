#encoding:gb2312

import os
import pylzma
import sys
import struct
import zlib
import ntpath

def validate(condition, msg, errorCode = 0):
    if not condition:
        stderr("ERROR#" + str(errorCode) + ":", msg)
        sys.exit(errorCode)

def kilo(value):
    return '{0:,}'.format(value)
        
def stderr(*argv):
    print >> sys.stderr, ' '.join(str(x) for x in argv)

def compress(infile, outfile):
    fi = open(infile, "rb")
    swf_size = os.path.getsize(infile)
    swf_data = fi.read()
    fi.close()

    validate((swf_data[1] == 'W') and (swf_data[2] == 'S'), "not a SWF file", 112)
    
    if swf_data[0] == 'Z':
        print "LZMA", outfile
        sys.exit(0)

    dfilesize = struct.unpack("<I", swf_data[4:8])[0] - 8
    
    if swf_data[0] == 'C':
        # compressed SWF
        ddata = zlib.decompress(swf_data[8:])
    else:
        # uncompressed SWF
        validate((swf_data[0] == 'F'), "not a SWF file", 113)
        ddata = swf_data[8:]

    validate((dfilesize == len(ddata)), 'decompression failure', 114)

    zdata = pylzma.compress(ddata, eos=1)
    
    # 5 accounts for lzma props
    zsize = len(zdata) - 5

    zheader = list(struct.unpack("<12B", swf_data[0:12]))
    zheader[0] = ord('Z')
    zheader[3] = ord(swf_data[3])
    zheader[8]  = (zsize)       & 0xFF
    zheader[9]  = (zsize >> 8)  & 0xFF
    zheader[10] = (zsize >> 16) & 0xFF
    zheader[11] = (zsize >> 24) & 0xFF

    fo = open(outfile, 'wb')
    fo.write(struct.pack("<12B", *zheader))
    fo.write(zdata)
    fo.close()

    opt_size = os.path.getsize(outfile)
    print "%6.2f%% %7.7sB  " % (100 - (100.0 * opt_size / swf_size), kilo(swf_size - opt_size)) + outfile + ": ", kilo(swf_size) + " -> " + kilo(opt_size)


# Format of SWF when LZMA is used:
# 
# | 4 bytes       | 4 bytes    | 4 bytes       | 5 bytes    | n bytes    | 6 bytes         |
# | 'ZWS'+version | scriptLen  | compressedLen | LZMA props | LZMA data  | LZMA end marker |
# 
# scriptLen is the uncompressed length of the SWF data. Includes 4 bytes SWF header and
# 4 bytes for scriptLen it
# 
# compressedLen does not include header (4+4+4 bytes) or lzma props (5 bytes)
# compressedLen does include LZMA end marker (6 bytes)
if __name__ == "__main__":
    #print 'arguments:', sys.argv, "\n"
        
    num = len(sys.argv)        
    validate( 2 <= num <= 3, 'usage: swf2lzma swf-path [output-swf-path]', 110)
    
    infile = sys.argv[1]
    validate((infile[-4:].lower() == '.swf'), 'input file must be of type .swf', 111)
    validate(os.path.exists(infile), infile + ' doesn\'t exist!!', 404)
    
    if num == 2:
        outfile = infile
    else:
        outfile = sys.argv[2]
        if outfile[-4:].lower() != '.swf':
            if not os.path.exists(outfile):
                os.mkdir(outfile)
            outfile = outfile + "\\" + ntpath.basename(infile)

    compress(infile, outfile)
    sys.exit(0)



import struct
import logging

X = 0
Y = 1

def row_to_int( row, size, bpp, endian ):

    logger = logging.getLogger( 'formats.row_to_int' )

    bits_out = 0
    bits_out_total = 0
    int_out = 0
    bits = size[X] * bpp
    for px in row:
        if 1 == bpp:
            int_out <<= 1
            if 0 < px:
                int_out |= 1
            else:
                int_out |= 0
        elif 2 == bpp:
            int_out <<= 1
            if 3 == px or 2 == px:
                int_out |= 1
            int_out <<= 1
            if 3 == px or 1 == px:
                int_out |= 1
        bits_out += bpp
        bits_out_total += bpp
        if bits <= bits_out:
            if 'l' == endian:
                int_out = switch_endian( int_out, size, bpp )
            yield int_out
            bits_out = 0
            int_out = 0

    logger.debug( 'bits out: %d (should be %d)', bits_out_total,
        size[X] * bpp )
    assert( bits_out_total == size[X] * bpp )

def row_from_int( row_hex_int, size, bpp, endian ):

    logger = logging.getLogger( 'formats.row_from_int' )

    new_row = []

    bpp_mask = 0x1
    if 2 == bpp:
        bpp_mask = 0x3

    # Internal state is always big endian.
    if 'l' == endian:
        row_hex_int = switch_endian( row_hex_int, size, bpp )

    for bit_idx in range( 0, size[X] ):
        # Grab each pixel from each bit(s).
        int_px = 0
        int_px |= row_hex_int & bpp_mask
        row_hex_int >>= bpp
        logger.debug( 'bit_idx %d: int_px: %d', bit_idx, int_px )
        logger.debug( 'adding pixel: %d', int_px )
        new_row.insert( 0, int_px )

    # Padding if size_out bigger than size_in happens in load routine.

    return new_row

def switch_endian( int_out, size, bpp ):
    if 8 == size[X] * bpp:
        int_out = struct.unpack(
            "<B", struct.pack( ">B", int_out ) )[0]
    elif 16 == size[X] * bpp:
        int_out = struct.unpack(
            "<H", struct.pack( ">H", int_out ) )[0]
    elif 32 == size[X] * bpp:
        int_out = struct.unpack(
            "<I", struct.pack( ">I", int_out ) )[0]
    elif 64 == size[X] * bpp:
        int_out = struct.unpack(
            "<Q", struct.pack( ">Q", int_out ) )[0]
    else:
        raise Exception( 'unpackable size specified' )
    return int_out


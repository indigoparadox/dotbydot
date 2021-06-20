
import os
import logging

from . import row_from_int, row_to_int

X = 0
Y = 1

def read_file( filename_in, size, bpp, endian ):

    logger = logging.getLogger( 'formats.header.read' )

    grid = []

    it = 0
    if os.path.exists( filename_in ):
        with open( filename_in, 'r' ) as file_in:
            # Grab the text representation of the numbers from the file.
            hexline = file_in.readline()
            hexes = hexline.split( ', ' )

            for y_grid in range( 0, size[Y] ):
                logger.debug( 'reading row %d of %d', y_grid, size[Y] )
                # Create a new empty row.
                row_hex_int = int( hexes[0], 16 )
                hexes.pop( 0 )
                logger.debug( 'read row_hex_int: %d', row_hex_int )
                new_row = row_from_int( row_hex_int, size, bpp, endian )

                logger.debug( 'row is %d (Y) (should be %d)',
                    len( new_row ), size[X] )
                assert( size[X] == len( new_row ) )

                grid.append( new_row )

        logger.debug( 'grid is %d (Y) (should be %d)', len( grid ), size[Y] )
        assert( size[Y] == len( grid ) )

    else:
        for x_grid in range( 0, size[X] ):
            grid.append( [] )
            for y_grid in range( 0, size[Y] ):
                grid[x_grid].append( 0 )
    
    return grid

def write_file( \
filename_out, grid, size, bpp, endian, interlace=False, vertical=False ):
    
    with open( filename_out, 'w' ) as grid_h:
        if vertical:
            for col_idx in range( 0, len( grid[X] ) ):
                col = []
                for row in grid:
                    col.append( row[col_idx] )
                for col_int in \
                row_to_int( col, size, bpp, endian ):
                    grid_h.write( "0x%x, " % col_int )
        else:
            if interlace:
                for row_idx in range( 0, len( grid ), 2 ):
                    for row_int in \
                    row_to_int( grid[row_idx], size, bpp, endian ):
                        grid_h.write( "0x%x, " % row_int )
                for row_idx in range( 1, len( grid ), 2 ):
                    for row_int in \
                    row_to_int( grid[row_idx], size, bpp, endian ):
                        grid_h.write( "0x%x, " % row_int )
            else:
                # Just go row by row.
                for row in grid:
                    for row_int in \
                    row_to_int( row, size, bpp, endian ):
                        grid_h.write( "0x%x, " % row_int )


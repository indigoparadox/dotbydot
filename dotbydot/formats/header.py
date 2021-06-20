
import os
import logging

from . import row_from_int

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

                # Pad row if size_out is bigger than size_in.
                # TODO
                #for pad_idx in \
                #range( 0, self.size_out[X] - self.size_in[X] ):
                #    self.logger.debug( 'padding idx (X): %d', pad_idx )
                #    new_row.append( 0 )

                #self.logger.debug( 'row padded to %d (X) (should be %d)',
                #    len( new_row ), self.size_out[X] )
                #assert( self.size_out[X] == len( new_row ) )

                grid.append( new_row )

        logger.debug( 'grid is %d (Y) (should be %d)', len( grid ), size[Y] )
        assert( size[Y] == len( grid ) )

        # Pad columns if size_out is bigger than size_in.
        # TODO
        #for pad_idx in range( 0, self.size_out[Y] - self.size_in[Y] ):
        #    new_row = []
        #    for pad_idx_x in range( 0, self.size_out[X] ):
        #        new_row.append( 0 )
        #    self.grid.append( new_row )

        #self.logger.debug( 'grid padded to %d (Y) (should be %d)',
        #    len( self.grid ), self.size_out[Y] )
        #assert( self.size_out[Y] == len( self.grid ) )

    else:
        for x_grid in range( 0, size[X] ):
            grid.append( [] )
            for y_grid in range( 0, size[Y] ):
                grid[x_grid].append( 0 )
    
    return grid

def write_file( path, grid, bpp, endian ):
    pass


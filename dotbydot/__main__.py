#!/usr/bin/env python

import pygame
import argparse
import os
import logging
from pygame.time import get_ticks

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240

X = 0
Y = 1

class DotByDot( object ):

    def __init__( self, size, bpp, zoom, filename=None, vertical=False ):
        self.zoom = int( zoom )
        self.size = size
        self.filename = filename
        self.vertical = vertical
        self.bpp = bpp
        self.last_click = get_ticks()
        self.last_coords = (0, 0)

        self.logger = logging.getLogger( 'dotbydot' )

        bpp_mask = 0x1
        if 2 == bpp:
            bpp_mask = 0x3

        self.grid = []
        it = 0
        if os.path.exists( filename ):
            with open( filename, 'r' ) as file_in:
                # Grab the text representation of the numbers from the file.
                hexline = file_in.readline()
                hexes = hexline.split( ', ' )
                assert( len( hexes ) == self.size[Y] +  1 )
                print( hexes )

                for y_grid in range( 0, self.size[Y] ):
                    self.logger.debug( 'reading row %d of %d', y_grid, self.size[Y] )
                    # Create a new empty row.
                    new_row = []
                    row_hex_int = int( hexes[0], 16 )
                    hexes.pop( 0 )
                    self.logger.debug( 'read row_hex_int: %d', row_hex_int )
                    for bit_idx in range( 0, self.size[X] ):
                        # Grab each pixel from each bit(s).
                        int_px = 0
                        int_px |= row_hex_int & bpp_mask
                        row_hex_int >>= self.bpp
                        self.logger.debug(
                            'bit_idx %d: int_px: %d', bit_idx, int_px )
                        self.logger.debug( 'adding pixel: %d', int_px )
                        new_row.insert( 0, int_px )
                    self.grid.append( new_row )

                    assert( self.size[X] == len( new_row ) )
                        
                print( self.grid )
            assert( self.size[Y] == len( self.grid ) )
        else:
            for x_grid in range( 0, self.size[X] ):
                self.grid.append( [] )
                for y_grid in range( 0, self.size[Y] ):
                    self.grid[x_grid].append( 0 )

    def draw_gridlines( self ):

        for x_grid in range( 0, self.size[X] ):
            pygame.draw.line( self.canvas, (0, 0, 0), \
                (x_grid * self.zoom, 0), \
                (x_grid * self.zoom, self.canvas.get_height()), 2 )

        for y_grid in range( 0, self.size[Y] ):
            pygame.draw.line( self.canvas, (0, 0, 0), \
                (0, y_grid * self.zoom), \
                (self.canvas.get_width(), y_grid * self.zoom), 2 )

    def toggle_px( self, px ):
        if 0 == self.grid[int( px[Y] )][int( px[X] )]:
            self.grid[int( px[Y] )][int( px[X] )] = 1
        elif 1 == self.grid[int( px[Y] )][int( px[X] )]:
            if 1 == self.bpp:
                self.grid[int( px[Y] )][int( px[X] )] = 0
            elif 2 == self.bpp:
                self.grid[int( px[Y] )][int( px[X] )] = 2
        elif 2 == self.grid[int( px[Y] )][int( px[X] )]:
            self.grid[int( px[Y] )][int( px[X] )] = 3
        elif 3 == self.grid[int( px[Y] )][int( px[X] )]:
            self.grid[int( px[Y] )][int( px[X] )] = 0

    #def draw_px( self, px ):
    #    if 0 == self.grid[int( px[Y] )][int( px[X] )]:
    #        self.grid[int( px[Y] )][int( px[X] )] = 1

    def erase_px( self, px ):
        if 1 == self.grid[int( px[Y] )][int( px[X] )]:
            self.grid[int( px[Y] )][int( px[X] )] = 0

    def row_to_int( self, row, bits ):
        bits_out = 0
        bits_out_total = 0
        int_out = 0
        for px in row:
            if 1 == self.bpp:
                int_out <<= 1
                if 1 == px:
                    int_out |= 1
                else:
                    int_out |= 0
            elif 2 == self.bpp:
                int_out <<= 1
                if 3 == px or 2 == px:
                    int_out |= 1
                int_out <<= 1
                if 3 == px or 1 == px:
                    int_out |= 1
            bits_out += self.bpp
            bits_out_total += self.bpp
            if bits <= bits_out:
                yield int_out
                bits_out = 0
                int_out = 0

        self.logger.debug( 'bits out: %d (should be %d)', bits_out_total,
            bits )
        assert( bits_out_total == bits )

    def save_grid( self, path ):

        with open( path, 'w' ) as grid_h:
            if self.vertical:
                for col_idx in range( 0, len( self.grid[0] ) ):
                    col = []
                    for row in self.grid:
                        col.append( row[col_idx] )
                    for col_int in self.row_to_int( col, self.bpp * 8 ):
                        grid_h.write( "0x%x, " % col_int )
            else:
                for row in self.grid:
                    for row_int in self.row_to_int( row, self.bpp * 8 ):
                        grid_h.write( "0x%x, " % row_int )

    def color_from_px( self, px ):
        color_draw = (0, 0, 0)
        if 1 == px:
            if 2 == self.bpp:
                color_draw = (0, 255, 255)
            else:
                color_draw = (255, 255, 255)
        elif 2 == px:
            color_draw = (255, 0, 255)
        elif 3 == px:
            color_draw = (255, 255, 255)
        return color_draw

    def show( self ):
        self.canvas = pygame.display.set_mode( \
            (self.size[X] * self.zoom, self.size[Y] * self.zoom) )

        self.running = True
        while self.running:

            # Get input state to apply below.
            for event in pygame.event.get():

                if pygame.QUIT == event.type:
                    self.running = False
                elif pygame.KEYDOWN == event.type:
                    if pygame.K_ESCAPE == event.key:
                        self.running = False
                    elif pygame.K_s == event.key:
                        self.save_grid( self.filename )
                    elif pygame.K_q == event.key:
                        self.running = False
                elif pygame.MOUSEBUTTONDOWN == event.type or \
                pygame.MOUSEMOTION == event.type:
                    draw_px = (pygame.mouse.get_pos()[X] / self.zoom, \
                        pygame.mouse.get_pos()[Y] / self.zoom)
                    if (1, 0, 0) == pygame.mouse.get_pressed() and \
                    get_ticks() > self.last_click + 50 and \
                    draw_px[X] != self.last_coords[X] and \
                    draw_px[Y] != self.last_coords[Y]:
                        self.last_click = get_ticks()
                        self.logger.debug( 'px toggle at %d, %d (last %d, %d)',
                            draw_px[X], draw_px[Y],
                            self.last_coords[X], self.last_coords[Y] )
                        self.last_coords = (draw_px[X], draw_px[Y])
                        self.toggle_px( draw_px )
                    elif (0, 0, 1) == pygame.mouse.get_pressed():
                        self.logger.debug( 'px erase at %d, %d',
                            draw_px[X], draw_px[Y] )
                        self.last_coords = draw_px
                        self.erase_px( draw_px )

            # Draw the current grid on the canvas.
            self.canvas.fill( (255, 255, 255) )
            for y_grid in range( 0, self.size[Y] ):
                for x_grid in range( 0, self.size[X] ):
                    color_draw = self.color_from_px( self.grid[y_grid][x_grid] )
                    pygame.draw.rect( self.canvas, color_draw, \
                        pygame.Rect( x_grid * self.zoom, y_grid * self.zoom, \
                            self.zoom, self.zoom ) )
            self.draw_gridlines()

            # Draw preview.
            pzoom = 4
            p_x = self.canvas.get_width() - (pzoom * self.size[X]) - 10
            p_y = self.canvas.get_height() - (pzoom * self.size[Y]) - 10
            pygame.draw.rect( self.canvas, (255, 255, 255), \
                pygame.Rect( p_x - pzoom, p_y - pzoom, \
                    (pzoom * self.size[X]) + (2 * pzoom), \
                    (pzoom * self.size[Y]) + (2 * pzoom) ) )
            pygame.draw.rect( self.canvas, (0, 0, 0), \
                pygame.Rect( p_x - pzoom, p_y - pzoom, \
                    (pzoom * self.size[X]) + (2 * pzoom), \
                    (pzoom * self.size[Y]) + (2 * pzoom) ), pzoom )
            for y_grid in range( 0, self.size[Y] ):
                for x_grid in range( 0, self.size[X] ):
                    color_draw = self.color_from_px( self.grid[y_grid][x_grid] )
                    pygame.draw.rect( self.canvas, color_draw, \
                        pygame.Rect( \
                            p_x + (x_grid * pzoom), \
                            p_y + (y_grid * pzoom), \
                            pzoom, pzoom ) )

            pygame.display.flip()

if '__main__' == __name__:

    parser = argparse.ArgumentParser()

    parser.add_argument( '-z', '--zoom', type=float )
    parser.add_argument( '-s', '--size', nargs="+", type=int )
    parser.add_argument( '-f', '--file', type=str )
    parser.add_argument( '-v', '--vertical', action='store_true' )
    parser.add_argument( '-b', '--bpp', type=int, default=1 )

    args = parser.parse_args()

    logging.basicConfig( level=logging.DEBUG )

    size = None
    if None == args.size:
        size = (8, 8)
    else:
        size = tuple( args.size )

    zoom = None
    if None == args.zoom:
        if DEFAULT_WIDTH / size[X] > DEFAULT_HEIGHT / size[Y]:
            zoom = DEFAULT_WIDTH / size[X]
        else:
            zoom = DEFAULT_HEIGHT / size[Y]

    pygame.init()
    dbd = DotByDot( size, args.bpp, zoom, args.file, vertical=args.vertical )
    dbd.show()


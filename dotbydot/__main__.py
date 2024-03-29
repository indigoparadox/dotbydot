#!/usr/bin/env python

import pygame
import argparse
import os
import logging
import struct
from pygame.time import get_ticks

from .formats import header

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240

X = 0
Y = 1

COLOR_BLACK = (0, 0, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_MAGENTA = (255, 0, 255)
COLOR_WHITE = (255, 255, 255)

IDX_BLACK = 0
IDX_CYAN = 1
IDX_MAGENTA = 2
IDX_WHITE = 3

class DotByDot( object ):

    def __init__(
        self, size_in, size_out, bpp_in, bpp_out,
        endian_in, endian_out, zoom, pzoom, interlace_in, interlace_out,
        filename_in=None, filename_out=None, vertical=False
    ):
        self.move_base_coords = None
        self.grid_undo = None
        self.grid_redo = None
        self.zoom = int( zoom )
        self.preview_zoom = int( pzoom )
        self.size_in = size_in
        # This is handled in main if size_out is None.
        self.size_out = size_out
        self.endian_in = endian_in
        self.endian_out = endian_out
        if 'l' == endian_in:
            self.little_endian_in = True
        elif 'b' == endian_in:
            self.little_endian_in = False
        else:
            raise Exception( 'invalid endianness specified' )
        if endian_out:
            if 'l' == endian_out:
                self.little_endian_out = True
            elif 'b' == endian_out:
                self.little_endian_out = False
            else:
                raise Exception( 'invalid endianness specified' )
        else:
            self.little_endian_out = self.little_endian_in
        self.filename_in = filename_in
        if filename_out:
            self.filename_out = filename_out
        else:
            self.filename_out = filename_in
        self.vertical = vertical
        self.interlace_in = True if 'y' == interlace_in.lower() or \
            '1' == interlace_in.lower() or 't' == interlace_in.lower() else \
            False
        if interlace_out:
            self.interlace_out = True if 'y' == interlace_out.lower() or \
                '1' == interlace_out.lower() or \
                't' == interlace_out.lower() else \
                False
        else:
            self.interlace_out = self.interlace_in
        self.bpp_in = bpp_in
        if bpp_out:
            self.bpp_out = bpp_out
        else:
            self.bpp_out = self.bpp_in
        self.last_click = get_ticks()
        self.last_coords = (0, 0)
        self.last_px = 0

        self.logger = logging.getLogger( 'dotbydot' )

        if filename_in:
            # Open specified file.
            self.grid = header.read_file(
                filename_in, size_in, bpp_in, endian_in )

        else:
            # Create an empty grid.
            self.grid = [
                [0 for x in range( 0, self.size_out[X] )]
                for y in range( 0, self.size_out[Y] )]

        # Pad rows if size_out is bigger than size_in.
        for row_idx in range( self.size_in[Y] ):
            for pad_idx in \
            range( 0, self.size_out[X] - self.size_in[X] ):
                self.logger.debug( 'padding idx (X): %d', pad_idx )
                self.grid[row_idx].append( 0 )

            self.logger.debug( 'row %d padded to %d (X) (should be %d)',
                row_idx, len( self.grid[row_idx] ), self.size_out[X] )
            assert( self.size_out[X] == len( self.grid[row_idx] ) )

        # Pad columns if size_out is bigger than size_in.
        for pad_idx in range( 0, self.size_out[Y] - self.size_in[Y] ):
            new_row = []
            for pad_idx_x in range( 0, self.size_out[X] ):
                new_row.append( 0 )
            self.grid.append( new_row )
        assert( self.size_out[Y] == len( self.grid ) )

    def draw_gridlines( self ):

        for x_grid in range( 0, self.size_out[X] ):
            pygame.draw.line( self.canvas, (128, 128, 128), \
                (x_grid * self.zoom, 0), \
                (x_grid * self.zoom, self.canvas.get_height()), 2 )

        for y_grid in range( 0, self.size_out[Y] ):
            pygame.draw.line( self.canvas, (128, 128, 128), \
                (0, y_grid * self.zoom), \
                (self.canvas.get_width(), y_grid * self.zoom), 2 )

    def set_px( self, px_coords, new_px ):
        if px_coords[X] < self.size_out[X] and \
        px_coords[Y] < self.size_out[Y]:
            self.grid[int( px_coords[Y] )][int( px_coords[X] )] = new_px

    def toggle_px( self, px_coords ):
        new_px = None

        if px_coords[X] >= self.size_out[X] or \
        px_coords[Y] >= self.size_out[Y]:
            return

        self.logger.debug( 'px toggle at %d, %d (last %d, %d)',
            px_coords[X], px_coords[Y],
            self.last_coords[X], self.last_coords[Y] )

        if 0 == self.grid[int( px_coords[Y] )][int( px_coords[X] )]:
            new_px = 1
        elif 1 == self.grid[int( px_coords[Y] )][int( px_coords[X] )]:
            if 1 == self.bpp_out:
                new_px = 0
            elif 2 == self.bpp_out:
                new_px = 2
        elif 2 == self.grid[int( px_coords[Y] )][int( px_coords[X] )]:
            new_px = 3
        elif 3 == self.grid[int( px_coords[Y] )][int( px_coords[X] )]:
            new_px = 0

        return new_px

    #def draw_px( self, px ):
    #    if 0 == self.grid[int( px[Y] )][int( px[X] )]:
    #        self.grid[int( px[Y] )][int( px[X] )] = 1

    def erase_px( self, px ):

        if px[X] >= self.size_out[X] or \
        px[Y] >= self.size_out[Y]:
            return

        if 0 != self.grid[int( px[Y] )][int( px[X] )]:
            self.grid[int( px[Y] )][int( px[X] )] = 0


    def save_undo( self ):
        self.logger.debug( 'saving state for undo...' )
        self.grid_undo = []
        for row in self.grid:
            self.grid_undo.append( row.copy() )

    def undo_grid( self ):
        if self.grid_undo:
            self.logger.debug( 'undoing changes...' )
            self.grid_redo = self.grid
            self.grid = self.grid_undo
            self.grid_undo = None
        else:
            self.logger.warning( 'no undo buffer present' )
        
    def redo_grid( self ):
        if self.grid_redo:
            self.logger.debug( 'redoing changes...' )
            self.grid_undo = self.grid
            self.grid = self.grid_redo
            self.grid_redo = None
        else:
            self.logger.warning( 'no redo buffer present' )

    def save_grid( self, path ):
        # TODO: Select output format.
        header.write_file( self.filename_out, self.grid,
            self.size_out, self.bpp_out, self.endian_out )

    def color_from_px( self, px ):
        color_draw = (0, 0, 0)
        if 1 == px and 1 < self.bpp_out:
            color_draw = COLOR_CYAN
        elif 2 == px and 1 < self.bpp_out:
            color_draw = COLOR_MAGENTA
        elif 3 == px and 1 < self.bpp_out:
            color_draw = COLOR_WHITE
        elif 0 == px:
            color_draw = COLOR_BLACK
        else:
            color_draw = COLOR_WHITE
        return color_draw

    def shift_image( self, x_offset, y_offset ):

        if x_offset > 0:
            for row_idx in range( 0, self.size_out[Y] ):
                for px_idx in range( 0, self.size_out[X] ):
                    if row_idx + 1 < 0 or row_idx + 1 >= self.size_out[Y]:
                        continue
                    elif px_idx + 1 < 0 or px_idx + 1 >= self.size_out[X]:
                        continue

                    self.grid[row_idx][px_idx] = \
                        self.grid[row_idx][px_idx + 1]

        if x_offset < 0:
            for row_idx in reversed( range( 0, self.size_out[Y] ) ):
                for px_idx in reversed( range( 0, self.size_out[X] ) ):
                    if row_idx - 1 < 0 or row_idx - 1 >= self.size_out[Y]:
                        continue
                    elif px_idx - 1 < 0 or px_idx - 1 >= self.size_out[X]:
                        continue

                    self.grid[row_idx][px_idx] = \
                        self.grid[row_idx][px_idx - 1]

        if y_offset > 0:
            for row_idx in range( 0, self.size_out[Y] ):
                for px_idx in range( 0, self.size_out[X] ):
                    if row_idx + 1 < 0 or row_idx + 1 >= self.size_out[Y]:
                        continue
                    elif px_idx + 1 < 0 or px_idx + 1 >= self.size_out[X]:
                        continue

                    self.grid[row_idx][px_idx] = \
                        self.grid[row_idx + 1][px_idx]

        if y_offset < 0:
            for row_idx in reversed( range( 0, self.size_out[Y] ) ):
                for px_idx in reversed( range( 0, self.size_out[X] ) ):
                    if row_idx - 1 < 0 or row_idx - 1 >= self.size_out[Y]:
                        continue
                    elif px_idx - 1 < 0 or px_idx - 1 >= self.size_out[X]:
                        continue

                    self.grid[row_idx][px_idx] = \
                        self.grid[row_idx - 1][px_idx]

        self.redraw_canvas()
        pygame.display.flip()

    def show( self ):
        canvas_zoom_area_sz = (2 * self.size_out[X]) * self.preview_zoom
        self.canvas = pygame.display.set_mode(
            ((self.size_out[X] * self.zoom) + canvas_zoom_area_sz,
            (self.size_out[Y] * self.zoom)) )

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
                        self.save_grid( self.filename_out )
                    elif pygame.K_u == event.key:
                        self.undo_grid()
                    elif pygame.K_r == event.key:
                        self.redo_grid()
                    elif pygame.K_q == event.key:
                        self.running = False
                elif pygame.MOUSEBUTTONDOWN == event.type or \
                pygame.MOUSEMOTION == event.type:

                    # Save undo for whatever comes next.
                    if pygame.MOUSEBUTTONDOWN == event.type:
                        self.save_undo()

                    # Figure out which pixel was clicked.
                    px_coords = (pygame.mouse.get_pos()[X] / self.zoom, \
                        pygame.mouse.get_pos()[Y] / self.zoom)

                    # Left Button, After Delay, New Pixel or Motion
                    if (1, 0, 0) == pygame.mouse.get_pressed() and \
                    get_ticks() > self.last_click + 50 and \
                    (
                        pygame.MOUSEBUTTONDOWN == event.type or \
                        (
                            
                            pygame.MOUSEMOTION == event.type and \
                            px_coords[X] != self.last_coords[X] and \
                            px_coords[Y] != self.last_coords[Y]
                        )
                    ):
                        self.last_click = get_ticks()
                        self.last_coords = (px_coords[X], px_coords[Y])
                        if pygame.MOUSEBUTTONDOWN == event.type:
                            # Only choose a new color if we're clicking.
                            if pygame.key.get_pressed()[pygame.K_1]:
                                self.last_px = IDX_CYAN
                            elif pygame.key.get_pressed()[pygame.K_2]:
                                self.last_px = IDX_MAGENTA
                            elif pygame.key.get_pressed()[pygame.K_3]:
                                self.last_px = IDX_WHITE
                            else:
                                self.last_px = self.toggle_px( px_coords )
                        self.set_px( px_coords, self.last_px )

                    # Right Button
                    elif (0, 0, 1) == pygame.mouse.get_pressed():
                        self.logger.debug( 'px erase at %d, %d',
                            px_coords[X], px_coords[Y] )
                        self.last_coords = px_coords
                        self.erase_px( px_coords )

                    elif (0, 1, 0) == pygame.mouse.get_pressed():
                        if pygame.MOUSEBUTTONDOWN == event.type:
                            # Set base pixel to judge movement from.
                            self.move_base_coords = px_coords

                        elif pygame.MOUSEMOTION == event.type:
                            # Move pixels based on mouse movement.
                            if None != px_coords and \
                            None != self.move_base_coords and \
                            (int( px_coords[X] ) != \
                                int( self.move_base_coords[X] ) or \
                            int( px_coords[Y] ) != \
                                int( self.move_base_coords[Y]) ):
                                self.logger.debug( 'moving %d %d',
                                    px_coords[X] - self.move_base_coords[X],
                                    px_coords[Y] - self.move_base_coords[Y] )
                                self.shift_image(
                                    int( self.move_base_coords[X] - \
                                        px_coords[X] ),
                                    int( self.move_base_coords[Y] - \
                                        px_coords[Y]) )
                                self.move_base_coords = px_coords
            
            self.redraw_canvas()

            # Draw preview.
            p_w = self.preview_zoom * self.size_out[Y]
            p_h = self.preview_zoom * self.size_out[X]
            p_x = self.canvas.get_width() - \
                (1.5 * p_h)
            p_y = int( (self.size_out[Y] * self.preview_zoom) / 2 )

            self.show_preview( p_x, p_y,
                0, 0, self.size_out[X], self.size_out[Y] )

            # Tile right.
            self.show_preview( p_x + p_w, p_y,
                0, 0, int( self.size_out[X] / 2), self.size_out[Y] )

            # Tile left.
            self.show_preview( 
                p_x=p_x - int( p_w / 2 ),
                p_y=p_y,
                start_x=int( self.size_out[X] / 2 ),
                start_y=0,
                width=int( self.size_out[X] / 2 ),
                height=self.size_out[Y] )

            # Tile top.
            self.show_preview(
                p_x=p_x,
                p_y=0,
                start_x=0,
                start_y=int( self.size_out[Y] / 2 ),
                width=self.size_out[X],
                height=int( self.size_out[Y] / 2 ) )

            # Tile bottom.
            self.show_preview(
                p_x=p_x,
                p_y=p_y + (self.size_out[Y] * self.preview_zoom),
                start_x=0,
                start_y=0,
                width=self.size_out[X],
                height=int( self.size_out[Y] / 2 ) )

            pygame.display.flip()

    def redraw_canvas( self ):
        # Draw the current grid on the canvas.
        self.canvas.fill( (255, 255, 255) )
        for y_grid in range( 0, self.size_out[Y] ):
            for x_grid in range( 0, self.size_out[X] ):
                color_draw = self.color_from_px( self.grid[y_grid][x_grid] )
                pygame.draw.rect( self.canvas, color_draw, \
                    pygame.Rect( x_grid * self.zoom, y_grid * self.zoom, \
                        self.zoom, self.zoom ) )
        self.draw_gridlines()

    def show_preview( self, p_x, p_y, start_x, start_y, width, height ):
        # Iterate from source coords.
        for y_grid in range( start_y, start_y + height ):
            for x_grid in range( start_x, start_x + width ):
                color_draw = self.color_from_px( self.grid[y_grid][x_grid] )
                
                # Draw the individual pixel at this coordinate.
                pygame.draw.rect( self.canvas, color_draw, \
                    pygame.Rect( \
                        p_x + ((x_grid - start_x) * self.preview_zoom), \
                        p_y + ((y_grid - start_y) * self.preview_zoom), \
                        self.preview_zoom, self.preview_zoom ) )

if '__main__' == __name__:

    parser = argparse.ArgumentParser()

    parser.add_argument( '-of', '--outfile', type=str, required=True,
        help='Specify path of output file to write.' )
    parser.add_argument( '-if', '--infile', type=str,
        help='Specify path of input file to read.' )
    parser.add_argument( '-z', '--zoom', type=int,
        help='Zoom pixels in editor area.' )
    parser.add_argument( '-pz', '--pzoom', type=int, default=4,
        help='Zoom pixels in preview area.' )
    parser.add_argument( '-is', '--insize', nargs="+", type=int,
        help='Comma-separated input dimensions (e.g. 8, 8 for 8x8 pixels.' + \
            'Defaults to trying to determine from infile.' )
    parser.add_argument( '-os', '--outsize', nargs="+", type=int,
        help='Comma-separated output dimensions (e.g. 8, 8 for 8x8 pixels.' + \
            'Defaults to 8x8.' )
    parser.add_argument( '-v', '--vertical', action='store_true',
        help='Write output as columns of rows, rather than rows of columns.' )
    parser.add_argument( '-ib', '--inbpp', type=int, default=1,
        help='Output BPP. Defaults to trying to determine from infile.' )
    parser.add_argument( '-ob', '--outbpp', type=int,
        help='Output BPP. Defaults to 1 (monochrome).' )
    parser.add_argument( '-ie', '--inendian', type=str, default='b',
        help='Assume LSB-first format in input file.' )
    parser.add_argument( '-oe', '--outendian', type=str,
        help='Write MSB-first format in output file.' )
    parser.add_argument( '-ii', '--ininterlace', type=str, default='f',
        help='Assume even lines in top half and odd lines in the bottom ' + \
            'in input files.' )
    parser.add_argument( '-oi', '--outinterlace', type=str,
        help='Place even lines in top half and odd lines in the bottom ' +
            'in output files.' )

    args = parser.parse_args()

    logging.basicConfig( level=logging.DEBUG )

    isize = None
    if None == args.insize:
        isize = (8, 8)
    else:
        isize = tuple( args.insize )
    osize = None
    if None == args.outsize:
        osize = isize
    else:
        osize = tuple( args.outsize )

    assert( osize >= isize )

    zoom = None
    if None == args.zoom:
        if DEFAULT_WIDTH / isize[X] > DEFAULT_HEIGHT / isize[Y]:
            zoom = DEFAULT_WIDTH / isize[X]
        else:
            zoom = DEFAULT_HEIGHT / isize[Y]

    pygame.init()
    dbd = DotByDot( isize, osize, args.inbpp, args.outbpp, args.inendian,
        args.outendian, zoom, args.pzoom, args.ininterlace, args.outinterlace,
        args.infile, args.outfile, vertical=args.vertical )
    dbd.show()


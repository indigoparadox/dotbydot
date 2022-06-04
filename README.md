
# dotbydot

A simple low-resolution pixel font editor for creating fonts to be used in retro applications, microcontrollers, and other low-resource environments.

A pretty roughly put-together tool of convenience at the moment.

## Dependencies

- python3
- pygame

## Supported Formats

There is a framework to adapt the internal grid format to various input/output formats if modules are written for them. Currently supported are:

- C header file constants

## Usage

Currently, options are only available on the command line:

`python -m dotbydot -of OUTFILE [-if INFILE] [-z ZOOM] [-pz PZOOM]
   [-is INSIZE [INSIZE ...]] [-os OUTSIZE [OUTSIZE ...]] [-v]
   [-ib INBPP] [-ob OUTBPP] [-ie INENDIAN] [-oe OUTENDIAN]
   [-ii ININTERLACE] [-oi OUTINTERLACE]`

- `-of OUTFILE`, `--outfile OUTFILE`
  - Specify path of output file to write.
- `-if INFILE`, `--infile INFILE`
  - Specify path of input file to read.
- `-z ZOOM`, `--zoom ZOOM`
  - Zoom pixels in editor area.
- `-pz PZOOM`, `--pzoom PZOOM`
  - Zoom pixels in preview area.
- `-is INSIZE [INSIZE ...]`, `--insize INSIZE [INSIZE ...]`
  - Comma-separated input dimensions (e.g. 8, 8 for 8x8 pixels.Defaults to trying to determine from infile.
- `-os OUTSIZE [OUTSIZE ...]`, `--outsize OUTSIZE [OUTSIZE ...]`
  - Comma-separated output dimensions (e.g. 8, 8 for 8x8 pixels.Defaults to 8x8.
- `-v`, `--vertical`
  - Write output as columns of rows, rather than rows of columns.
- `-ib INBPP`, `--inbpp INBPP`
  - Output BPP. Defaults to trying to determine from infile.
- `-ob OUTBPP`, `--outbpp OUTBPP`
  - Output BPP. Defaults to 1 (monochrome).
- `-ie INENDIAN`, `--inendian INENDIAN`
  - Assume LSB-first format in input file.
- `-oe OUTENDIAN`, `--outendian OUTENDIAN`
  - Write MSB-first format in output file.
- `-ii ININTERLACE`, `--ininterlace ININTERLACE`
  - Assume even lines in top half and odd lines in the bottom in input files.
- `-oi OUTINTERLACE`, `--outinterlace OUTINTERLACE`
  - Place even lines in top half and odd lines in the bottom in output files.


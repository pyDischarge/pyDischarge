#!/usr/bin/env python

"""GWpy Example: plotting a spectrogram

Problem
-------

I would like to study the gravitational wave strain spectrogram around the time of an interesting simulated signal during the last science run (S6). I have access to the frame files on the LIGO Data Grid machine `ldas-pcdev2.ligo-wa.caltech.edu` and so can read them directly.
"""

from gwpy.time import Time
from gwpy.timeseries import TimeSeries

from gwpy import version
__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__version__ = version.version


# set the times
start = Time('2010-09-16 06:42:00', format='iso', scale='utc')
end = Time('2010-09-16 06:43:00', format='iso', scale='utc')

# find the data using NDS
data = TimeSeries.fetch('H1:LDAS-STRAIN', start.gps, end.gps, verbose=True)

# calculate spectrogram
specgram = data.spectrogram(1)
specgram **= 1/2.

# plot
plot = specgram.plot()
plot.logy = True
plot.ylim = [40, 4096]
plot.add_colorbar(log=True, clim=[1e-23, 1e-20],
                  label='Amplitude spectral density '
                        '[strain $/\\sqrt{\\mathrm{Hz}}$]')
plot.ylabel = 'Frequency [Hz]'
plot.ylim = [40, 4000]

if __name__ == '__main__':
    try:
        outfile = __file__.replace('.py', '.png')
    except NameError:
        pass
    else:
        plot.save(outfile)
        print("Example output saved as\n%s" % outfile)

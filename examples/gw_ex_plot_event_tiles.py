#!/usr/bin/env python

# Copyright (C) Duncan Macleod (2014)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""GWpy Example: plotting a table of event triggers

Problem
-------

I would like to study the event triggers generated by the `ExcessPower <link>`_
gravitational-wave burst detection algorithm, over a small stretch of data.

The data from which these events were generated are a simulation of Gaussian noise
with the Advanced LIGO design spectrum, and so don't actually contain any real
gravitational waves, but will help tune the algorithm to improve detection of
future, real signals.
"""

from gwpy import version
__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__version__ = version.version

from urllib2 import urlopen

from numpy import asarray

from gwpy.table.lsctables import SnglBurstTable

# read triggers
events = SnglBurstTable.read('../gwpy/tests/data/'
                             'H1-LDAS_STRAIN-968654552-10.xml.gz')

# make a plot
plot2 = events.plot('time', 'central_freq', 'duration', 'bandwidth', color='snr', epoch=968654552)
plot2.set_xlim(968654552, 968654552+10)
plot2.set_ylabel('Frequency [Hz]')
plot2.set_yscale('log')
plot2.set_title('LIGO Hanford Observatory event triggers for GW100916')
plot2.add_colorbar(clim=[1, 5], label='Signal-to-noise ratio')

if __name__ == '__main__':
    try:
        outfile = __file__.replace('.py', '.png')
    except NameError:
        pass
    else:
        plot2.save(outfile)
        print("Example output saved as\n%s" % outfile)
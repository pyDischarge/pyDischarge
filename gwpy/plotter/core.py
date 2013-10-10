
"""Extension of the basic matplotlib Figure for GWpy
"""

import numpy

from matplotlib import (axes, figure, pyplot, colors as mcolors,
                        ticker as mticker)
try:
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except ImportError:
    from mpl_toolkits.axes_grid import make_axes_locatable

from . import tex, axes
from .decorators import (auto_refresh, axes_method)


class Plot(figure.Figure):
    """An extension of the matplotib :class:`~matplotlib.figure.Figure`
    object for GWpy
    """
    def __new__(cls, *args, **kwargs):
        """Construct a new `Plot`

        This constructor will use the ``pyplot`` covenience method
        :meth:`~matplotlib.pyplot.figure` to generate a new figure
        """
        called_from_pyplot = kwargs.pop('called_from_pyplot', False)
        if called_from_pyplot:
            return super(Plot, cls).__new__(cls)
            #new.__init__(**kwargs)
        else:
            kwargs.setdefault('FigureClass', cls)
            kwargs.setdefault('called_from_pyplot', True)
            return pyplot.figure(**kwargs)

    def __init__(self, auto_refresh=False, **kwargs):
        if kwargs.pop('called_from_pyplot', False):
            super(Plot, self).__init__(**kwargs)
        self._auto_refresh = auto_refresh
        self.coloraxes = []

    # -----------------------------------------------
    # core plot operations

    def refresh(self):
        """Refresh the current figure
        """
        self.canvas.draw()

    def show(self):
        """Display the current figure
        """
        self.patch.set_alpha(0.0)
        super(Plot, self).show()

    def save(self, *args, **kwargs):
        """Save the figure to disk.

        All `args` and `kwargs` are passed directly to the savefig
        method of the underlying `matplotlib.figure.Figure`
        self.fig.savefig(*args, **kwargs)
        """
        self.savefig(*args, **kwargs)

    def close(self):
        """Close the plot and release its memory.
        """
        pyplot.close(self)

    # -----------------------------------------------
    # colour-bar

    @auto_refresh
    def add_colorbar(self, mappable=None, ax=None, location='right',
                     width=0.2, pad=0.1, log=None, label="", clim=None,
                     clip=None, visible=True, axes_class=axes.Axes, **kwargs):
        """Add a colorbar to the current `Axes`

        Parameters
        ----------
        mappable : matplotlib data collection
            collection against which to map the colouring
        ax : :class:`~matplotlib.axes.Axes`
            axes from which to steal space for the colour-bar
        location : `str`, optional, default: 'right'
            position of the colorbar
        width : `float`, optional default: 0.2
            width of the colorbar as a fraction of the axes
        pad : `float`, optional, default: 0.1
            gap between the axes and the colorbar as a fraction of the axes
        log : `bool`, optional, default: `False`
            display the colorbar with a logarithmic scale
        label : `str`, optional, default: '' (no label)
            label for the colorbar
        clim : pair of floats, optional
            (lower, upper) limits for the colorbar scale, values outside
            of these limits will be clipped to the edges
        visible : `bool`, optional, default: `True`
            make the colobar visible on the figure, this is useful to
            make two plots, each with and without a colorbar, but
            guarantee that the axes will be the same size
        **kwargs
            other keyword arguments to be passed to the
            :meth:`~matplotlib.figure.Figure.colorbar` generator

        Returns
        -------
        Colorbar
            the :class:`~matplotlib.colorbar.Colorbar` added to this plot
        """
        # find default layer
        if mappable is None and ax is not None and len(ax.collections):
            mappable = ax.collections[-1]
        elif mappable is None and ax is None:
            for ax in self.axes[::-1]:
                if hasattr(ax, 'collections') and len(ax.collections):
                    mappable = ax.collections[-1]
                    break
                elif hasattr(ax, 'images') and len(ax.images):
                    mappable = ax.images[-1]
                    break
        if not mappable:
            raise ValueError("Cannot determine mappable layer for this "
                             "colorbar")

        # find default axes
        if not ax:
            ax = mappable.axes

        # get new colour axis
        divider = make_axes_locatable(ax)
        if location == 'right':
            cax = divider.new_horizontal(size=width, pad=pad,
                                         axes_class=axes_class)
        elif location == 'top':
            cax = divider.new_vertical(size=width, pad=pad,
                                       axes_class=axes_class)
        else:
            raise ValueError("'left' and 'bottom' colorbars have not "
                             "been implemented")
        if visible:
            divider._fig.add_axes(cax)
        else:
            return

        # set limits
        if not clim:
            clim = mappable.get_clim()
        if log is None:
            log = isinstance(mappable, mcolors.LogNorm)
        if log and clim[0] <= 0.0:
            cdata = mappable.get_array()
            try:
                clim = (cdata[cdata>0.0].min(), clim[1])
            except ValueError:
                pass
        mappable.set_clim(clim)

        # set tick format (including sub-ticks for log scales)
        if pyplot.rcParams["text.usetex"]:
            if log and abs(float.__sub__(*numpy.log10(clim))) >= 2:
                func = lambda x,pos: (mticker.is_decade(x) and
                                  '$%s$' % tex.float_to_latex(x, '%.4g') or ' ')
            else:
                func = lambda x,pos: '$%s$' % tex.float_to_latex(x, '% .4g')
            kwargs.setdefault('format', mticker.FuncFormatter(func))

        # set log scale
        norm = mappable.norm
        if clip is None:
            clip = norm.clip
        if log and not isinstance(norm, mcolors.LogNorm):
            mappable.set_norm(mcolors.LogNorm(*mappable.get_clim()))
        else:
            mappable.set_norm(mcolors.Normalize(*mappable.get_clim()))
        mappable.norm.clip = clip

        # set tick locator
        if log:
            kwargs.setdefault('ticks',
                              mticker.LogLocator(subs=numpy.arange(1,11)))

        # make colour bar
        colorbar = self.colorbar(mappable, cax=cax, **kwargs)
        self.coloraxes.append(cax)

        # set label
        if label:
            colorbar.set_label(label)
        colorbar.draw_all()

        return colorbar

    # -------------------------------------------
    # GWpy data adding
    #
    # These methods try to guess which axes to add to, otherwise generate
    # a new one

    def _find_all_axes(self, projection=None):
        """Find all sets of axes for the given projection
        """
        allaxes = list(zip(*self._axstack._elements)[-1])
        allaxes.sort(key=lambda x: x[0])
        if projection is None:
            return zip(*allaxes)[1]
        else:
            return [ax for idx,ax in allaxes if ax.name == projection.lower()]

    def _find_axes(self, projection=None):
        """Find the most recently added axes for the given projection

        Raises
        ------
        IndexError
            if no axes for the projection are found
        """
        try:
            return self._find_all_axes(projection)[-1]
        except IndexError:
            if projection:
                raise IndexError("No '%s' Axes found in this Plot" % projection)
            else:
                raise IndexError("No Axes found in this Plot")

    def _increment_geometry(self):
        """Try to determine the geometry to use for a new Axes

        Raises
        ------
        ValueError
            if geometry is ambiguous
        """
        if not len(self.axes):
            return (1, 1, 1)
        current = self.axes[-1].get_geometry()
        shape = current[:2]
        pos = current[2]
        num = shape[0] * shape[1]
        if sum(shape) > 2 and pos == num:
            raise ValueError("Cannot determine where to place next Axes in "
                             "geomerty %s" % current)
        elif pos < num:
            return (shape[0], shape[1], pos+1)
        elif shape[1] == 1:
            return (shape[0] + 1, 1, pos+1)
        else:
            return (1, shape[1] + 1, pos+1)

    def _add_new_axes(self, projection):
        geometry = self._increment_geometry()
        ax = self.add_subplot(*geometry, projection=projection)
        if (geometry[0] == 1 or geometry[1] == 1 and
            geometry[2] == (geometry[0] * geometry[1])):
            idx = geometry[0] == 1 and 1 or 0
            geom = [geometry[0], geometry[1], 1]
            for i,ax_ in enumerate(self.axes[:-1]):
                ax_.change_geometry(*geom)
                geom[idx] += 1
                geom[2] += 1
        return ax

    @auto_refresh
    def _plot(self, x, y, *args, **kwargs):
        """Add a line to the current plot

        Parameters
        ----------
        x : array-like
            x positions of the line points (in axis coordinates)
        y : array-like
            y positions of the line points (in axis coordinates)
        projection : `str`, optional, default: `'timeseries'`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            additional keyword arguments passed directly on to
            the axes :meth:`~matplotlib.axes.Axes.plot` method.

        Returns
        -------
        Line2D
            the :class:`~matplotlib.lines.Line2D` for this line layer
        """
        # get axes options
        projection = kwargs.pop('projection', None)
        ax = kwargs.pop('ax', None)
        newax = kwargs.pop('newax', False)

        # set kwargs
        kwargs.setdefault("linestyle", "-")
        kwargs.setdefault("linewidth", 1)
        kwargs.setdefault("markersize", 0)

        # find relevant axes
        if ax is None and not newax:
            try:
                ax = self._find_axes(projection)
            except IndexError:
                newax = True
        if newax:
            ax = self._add_new_axes(projection=projection)
        # plot on axes
        return ax.plot(numpy.asarray(x), numpy.asarray(y), **kwargs)[0]

    @auto_refresh
    def _scatter(self, x, y, projection=None, ax=None, newax=False,
                 **kwargs):
        """Internal `Plot` method to scatter onto the most
        favourable `Axes`

        Parameters
        ----------
        x : array-like
            x positions of the line points (in axis coordinates)
        y : array-like
            y positions of the line points (in axis coordinates)
        projection : `str`, optional, default: `None`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs.
            other keyword arguments passed to the
            :meth:`matplotlib.axes.Axes.scatter` function

        Returns
        -------
        Collection
            the :class:`~matplotlib.collections.Collection` for this
            scatter layer
        """
        # set kwargs
        kwargs.setdefault("s", 20)

        # find relevant axes
        if ax is None and not newax:
            try:
                ax = self._find_axes(projection)
            except IndexError:
                newax = True
        if newax:
            ax = self._add_new_axes(projection=projection)
        # plot on axes
        return ax.scatter(numpy.asarray(x), numpy.asarray(y), **kwargs)

    @auto_refresh
    def _imshow(self, image, projection=None, ax=None, newax=False,
                 **kwargs):
        """Internal `Plot` method to imshow onto the most
        favourable `Axes`

        Parameters
        ----------
        x : array-like
            x positions of the line points (in axis coordinates)
        y : array-like
            y positions of the line points (in axis coordinates)
        projection : `str`, optional, default: `None`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs.
            other keyword arguments passed to the
            :meth:`matplotlib.axes.Axes.imshow` function

        Returns
        -------
        Collection
            the :class:`~matplotlib.image.AxesImage` for this image
        """
        # find relevant axes
        if ax is None and not newax:
            try:
                ax = self._find_axes(projection)
            except IndexError:
                newax = True
        if newax:
            ax = self._add_new_axes(projection=projection)
        # plot on axes
        return ax.imshow(image, **kwargs)

    @auto_refresh
    def add_line(self, x, y, *args, **kwargs):
        """Add a line to the current plot

        Parameters
        ----------
        x : array-like
            x positions of the line points (in axis coordinates)
        y : array-like
            y positions of the line points (in axis coordinates)
        projection : `str`, optional, default: `None`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            additional keyword arguments passed directly on to
            the axes :meth:`~matplotlib.axes.Axes.plot` method.

        Returns
        -------
        Line2D
            the :class:`~matplotlib.lines.Line2D` for this line layer
        """
        return self._plot(x, y, *args, **kwargs)

    @auto_refresh
    def add_scatter(self, x, y, **kwargs):
        """Add a set or points to the current plot

        Parameters
        ----------
        x : array-like
            x-axis data points
        y : array-like
            y-axis data points
        projection : `str`, optional, default: `None`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs.
            other keyword arguments passed to the
            :meth:`matplotlib.axes.Axes.scatter` function

        Returns
        -------
        Collection
            the :class:`~matplotlib.collections.Collection` for this
            scatter layer
        """
        return self._scatter(x, y, **kwargs)

    @auto_refresh
    def add_image(self, image, projection=None, ax=None, newax=False, **kwargs):
        """Add a 2-D image to this plot

        Parameters
        ----------
        image : `numpy.ndarray`
            2-D array of data for the image
        **kwargs
            other keyword arguments are passed to the
            :meth:`matplotlib.axes.Axes.imshow` function

        Returns
        -------
        image : :class:`~matplotlib.image.AxesImage`
        """
        return self._imshow(image, projection=projection, ax=ax, newax=newax,
                            **kwargs)


    @auto_refresh
    def add_timeseries(self, timeseries, projection='timeseries',
                       ax=None, newax=False, **kwargs):
        """Add a :class:`~gwpy.timeseries.core.TimeSeries` trace to this plot

        Parameters
        ----------
        timeseries : :class:`~gwpy.timeseries.core.TimeSeries`
            the TimeSeries to display
        projection : `str`, optional, default: `'timeseries'`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            other keyword arguments for the `Plot.add_line` function

        Returns
        -------
        Line2D
            the :class:`~matplotlib.lines.Line2D` for this line layer
        """
        return self.add_array(timeseries, 'timeseries',
                              ax=ax, newax=newax, **kwargs)

    @auto_refresh
    def add_spectrum(self, spectrum, projection='spectrum', ax=None,
                     newax=False, **kwargs):
        """Add a :class:`~gwpy.spectrum.core.Spectrum` trace to this plot

        Parameters
        ----------
        spectrum : :class:`~gwpy.spectrum.core.spectrum`
            the `Spectrum` to display
        projection : `str`, optional, default: `'Spectrum'`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            other keyword arguments for the `Plot.add_line` function

        Returns
        -------
        Line2D
            the :class:`~matplotlib.lines.Line2D` for this line layer
        """
        return self.add_array(spectrum, 'spectrum',
                              ax=ax, newax=newax, **kwargs)

    @auto_refresh
    def add_spectrogram(self, spectrogram, projection='timeseries',
                        ax=None, newax=False, **kwargs):
        """Add a :class:`~gwpy.spectrogram.core.Spectrogram` trace to
        this plot

        Parameters
        ----------
        spectrogram : :class:`~gwpy.spectrogram.core.Spectrogram`
            the `Spectrogram` to display
        projection : `str`, optional, default: `timeseries`
            name of the Axes projection on which to plot
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            other keyword arguments for the `Plot.add_line` function

        Returns
        -------
        Line2D
            the :class:`~matplotlib.lines.Line2D` for this line layer
        """
        return self.add_array(spectrogram, 'timeseries',
                              ax=ax, newax=newax, **kwargs)

    @auto_refresh
    def add_array(self, array, projection, ax=None, newax=False, **kwargs):
        """Add a :class:`~gwpy.data.array.Array` to this plot

        Parameters
        ----------
        array : :class:`~gwpy.data.array.Array`
            the `Array` to display
        projection : `str`
        ax : :class:`~gwpy.plotter.axes.Axes`
            the `Axes` on which to add these data, if this is not given,
            a guess will be made as to the best `Axes` to use. If no
            appropriate axes are found, new `Axes` will be created
        newax : `bool`, optional, default: `False`
            force data to plot on a fresh set of `Axes`
        **kwargs
            other keyword arguments for the `Plot.add_line` function

        Returns
        -------
        Artist : :class:`~matplotlib.artist.Artist`
            the layer return from the relevant plotting function
        """
        # find relevant axes
        if ax is None and not newax:
            try:
                ax = self._find_axes(projection)
            except IndexError:
                newax = True
        if newax:
            ax = self._add_new_axes(projection=projection)
        # plot on axes
        return ax.plot(array, **kwargs)

    # -------------------------------------------
    # Plot legend

    @auto_refresh
    def add_legend(self, *args, **kwargs):
        """Add a legend to this `Plot` on the most favourable `Axes`

        All non-keyword `args` and `kwargs` are passed directly to the
        :meth:`~matplotlib.axes.Axes.legend` generator

        Returns
        -------
        Legend
            the :class:`~matplotlib.legend.Legend` for this plot
        """
        # set kwargs
        alpha = kwargs.pop("alpha", 0.8)
        linewidth = kwargs.pop("linewidth", 8)

        # find relevant axes
        ax = kwargs.pop('ax', None)
        if ax is None:
            ax = self._find_axes()
        legend = ax.legend(*args, **kwargs)
        legend.set_alpha(alpha)
        [l.set_linewidth(linewidth) for l in legend.get_lines()]
        return legend

    # -------------------------------------------
    # Convenience methods for single-axes plots
    #
    # The majority of methods in this section are decorated to call the
    # equivalent method of the current Axes, and so contain no actual code

    @axes_method
    def get_xlim(self):
        pass
    get_xlim.__doc__ = axes.Axes.get_xlim.__doc__

    @axes_method
    @auto_refresh
    def set_xlim(self, *args, **kwargs):
        pass
    set_xlim.__doc__ = axes.Axes.set_xlim.__doc__

    xlim = property(fget=get_xlim, fset=set_xlim,
                    doc='x-axis limits for the current axes')

    @axes_method
    def get_ylim(self):
        pass
    get_ylim.__doc__ = axes.Axes.get_ylim.__doc__

    @axes_method
    @auto_refresh
    def set_ylim(self, *args, **kwargs):
        pass
    set_ylim.__doc__ = axes.Axes.set_ylim.__doc__

    ylim = property(fget=get_ylim, fset=set_ylim,
                    doc='y-axis limits for the current axes')

    @axes_method
    def get_xlabel(self):
        pass
    get_xlabel.__doc__ = axes.Axes.get_xlabel.__doc__

    @axes_method
    @auto_refresh
    def set_xlabel(self, *args, **kwargs):
        pass
    set_xlabel.__doc__ = axes.Axes.set_xlabel.__doc__

    xlabel = property(fget=get_xlabel, fset=set_xlabel,
                    doc='x-axis label for the current axes')

    @axes_method
    def get_ylabel(self):
        pass
    get_ylabel.__doc__ = axes.Axes.get_ylabel.__doc__

    @axes_method
    @auto_refresh
    def set_ylabel(self, *args, **kwargs):
        pass
    set_ylabel.__doc__ = axes.Axes.set_ylabel.__doc__

    ylabel = property(fget=get_ylabel, fset=set_ylabel,
                      doc='y-axis label for the current axes')

    @axes_method
    def get_title(self):
        pass
    get_title.__doc__ = axes.Axes.get_title.__doc__

    @axes_method
    @auto_refresh
    def set_title(self, *args, **kwargs):
        pass
    set_title.__doc__ = axes.Axes.set_title.__doc__

    title = property(fget=get_title, fset=set_title,
                     doc='title for the current axes')

    @axes_method
    def get_xscale(self):
        pass
    get_xscale.__doc__ = axes.Axes.get_xscale.__doc__

    @axes_method
    @auto_refresh
    def set_xscale(self, *args, **kwargs):
        pass
    set_xscale.__doc__ = axes.Axes.set_xscale.__doc__

    logx = property(fget=lambda self: self.get_xscale() == 'log',
                    fset=lambda self, b: self.set_xscale(b and 'log' or
                                                         'linear'),
                    doc="view x-axis in logarithmic scale")

    @axes_method
    def get_yscale(self):
        pass
    get_yscale.__doc__ = axes.Axes.get_yscale.__doc__

    @axes_method
    @auto_refresh
    def set_yscale(self, *args, **kwargs):
        pass
    set_yscale.__doc__ = axes.Axes.set_yscale.__doc__

    logy = property(fget=lambda self: self.get_yscale() == 'log',
                    fset=lambda self, b: self.set_yscale(b and 'log' or
                                                         'linear'),
                    doc="view y-axis in logarithmic scale")

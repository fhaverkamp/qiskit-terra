# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""
Visualization function for pulse envelope.
"""

import numpy as np


def pulse_drawer(samples, nop=1000, size=(6, 5)):
    """Plot the interpolated envelope of single pulse

    Args:
        samples (ndarray): data points of complex pulse envelope
        nop (int): data points for interpolation
        size (tuple): size of figure
    Returns:
        matplotlib.figure: a matplotlib figure object for the pulse envelope
    Raises:
        ImportError: when the output methods requieres non-installed libraries.
    """

    try:
        from matplotlib import pyplot as plt
    except ImportError:
        raise ImportError('pulse_drawer need matplotlib. '
                          'Run "pip install matplotlib" before.')
    try:
        from scipy.interpolate import CubicSpline
    except ImportError:
        raise ImportError('pulse_drawer need matplotlib. '
                          'Run "pip install scipy" before.')

    re_y = samples[:, 0]
    im_y = samples[:, 1]
    time = np.linspace(0, len(samples)-1, len(samples))

    # spline interpolation
    cs_ry = CubicSpline(time, re_y)
    cs_iy = CubicSpline(time, im_y)
    time_interp = np.linspace(0, max(time), nop)

    image = plt.figure(figsize=size)
    ax0 = image.add_subplot(111)

    ax0.scatter(x=time, y=re_y, c='red')
    ax0.scatter(x=time, y=im_y, c='blue')
    ax0.fill_between(x=time_interp, y1=cs_ry(time_interp),
                     y2=np.zeros_like(time_interp),
                     facecolors='red', alpha=0.5)
    ax0.fill_between(x=time_interp, y1=cs_iy(time_interp),
                     y2=np.zeros_like(time_interp),
                     facecolors='blue', alpha=0.5)
    ax0.set_xlim(0, max(time))
    ax0.grid(b=True, linestyle='-')

    plt.close(image)
    return image

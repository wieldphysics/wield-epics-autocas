.. _index:

IIRrational: Rational Function fitting for System ID
====================================================

Release v\ |version|. (:ref:`Installation <install>`)

IIRrational is an function-fitting library for signal processing and system identification. Fitting both poles and zeros for a rational function is a nonlinear optimization problem and typical formulations require an initial guess for convergence.

This library uses a two stage approach, where the second stage is a typical gradient descent optimization, but the first is a linear technique with fast and reliable convergence, but requires gratuitous over-fitting.

Features and Conveniences
-------------------------

 - No initial guess required
 - Automatic order reduction (using heuristics)
 - No poles or zeros with frequencies above the last data-point.
 - guaranteed stable poles (cannot currently be circumvented)
 - uses SNR weight vector
 - generates fisher matrix / covariance matrix of parameterizations
 - propagates errorbars to the fit
 - Z-domain for implementable filters
 - matlab support through the msurrogate package (TODO link)
 - Nonlinear optimization toolkit for rational functions
 - direct output of second-order-sections (biquadratic filters)

.. code-block:: python

  import iirrational.v1
  import iirrational.plots
  from iirrational.testing import iirrational_data

  dataset = iirrational_data('simple2')
  fit = iirrational.v1.data2filter(
      data = dataset.data,
      F_Hz = dataset.F_Hz,
      SNR  = dataset.SNR,
      F_nyquist_Hz = 16384,
  )
  ax = iirrational.plots.plot_fitter_flag(fit.fitter)


.. figure:: figs/simple2_fit_example.png
  :alt: Easy Example

  Easy Low order example with well-behaved data. Fits in 4s.

Contents
------------

.. toctree::
   :maxdepth: 2

   install
   quickstart
   quickstart_matlab
   development
   api_fitting
   advanced
   ideas


Example Output
---------------
Each of these fits has 1000 data points. The first is an Pitch to Vertical cross term coupling of an advanced LIGO suspension. The second is a random filter with SNR of 10 at each data point. Neither fit requires user tuning and (as is typical) correctly identifies the rolloff above the data.


solves in 60s

.. figure:: figs/quad_fit_example.png

solves in 20s

.. figure:: figs/random_fit_example.png


Future Directions
-----------------

The principle goal at this stage of the project is to improve reliability and speed of the fitting. To do this, I encourage using the :ref:`export` utility and posting the data on the github issues for integration into the test suite. Future versions aim to reliably fit all data in the test suite. Real data is essential as it exercises the heuristics in ways difficult to predict and emulate with random data.

Currently this package is only for SISO fitting. Its use for MIMO systems is limited to how automated fitting can become. Future work may extend the algorithms to intrinsically fit MIMO systems. This may be done either in the linear stage-1 or to compose many SISO functions, order-reduce them as a MIMO system and then perform nonlinear optimization on the resulting state-space formulation.

Alternatives
------------
.. TODO Links, add LIGO references

* Vectfit [matlab] https://www.sintef.no/projectweb/vectfit/
* python vectfit [python] https://github.com/PhilReinhold/vectfit_python
* fdident [matlab] https://www.mathworks.com/products/connections/product_detail/product_35570.html
* TFestimate [matlab] https://github.com/Nikhil-Mukund/TFestimate/blob/master/README.md


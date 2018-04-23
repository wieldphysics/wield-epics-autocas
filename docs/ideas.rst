.. _ideas:

Ideas
========

Power Spectra
-----------------
The two stages can be straghtforewardly adapted to fit without phase information to generate ZPK representations of power spectra. Very useful for later application of quadratic regulator methods for optimal control (even with SISO).

Order Reduction
-----------------

Use Pade tables to find alternate ZPK representations during the order reduction stage. This may work more efficiently and provide a non-greedy method. May have numerical issues.

Wiener Filter / Feedforward
--------------------------------

Since Weiner filter methods ultimately work as least-squares parallel SISO filters, this library could provide IIR representations and potentially incorporate error information better.

.. TODO:: Make a timeseries interface with internal PSD/CSD estimation, error bars, and automically feed these estimates to data2filter. Potentially compare the result to the standard FIR method with some error estimate. Perhaps allow witness vs. Fit datasets.

MIMO
---------

With sufficient reliability, this SISO fitter could compose multiple fits into a MIMO system. The Order reduction algorithms could be modified for common root identification to weak SISO ZPK outputs into a MIMO Z, common-P, K that could generate state-space matrices of a reasonable order.


Error Estimation
------------------

SNR Reconditioning
^^^^^^^^^^^^^^^^^^^^

SNR estimates from coherence can be biased and wrong in a number of ways. With enough data-points, an initial fit could be used to find the residuals and some variance smoothing method could be applied to find the (somehow defined) local SNR of data points where it is apparent that the SNR is poorly estimated. The fit could then be iterated with updated SNR estimates.

MCMC
^^^^^^^
Use `emcee <http://dfm.io/emcee/current/>`_ for a stage-3 error estimation after the least squares.




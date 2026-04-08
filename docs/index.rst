mplvega
=======

``mplvega`` is a matplotlib-shaped frontend that emits Vega-Lite JSON and can
either write browser-ready HTML directly or route the same spec into
``fortplot_render`` for PNG and PDF output.

The documentation site is generated on CI from the checked-in example scripts.
The examples section is not a screenshot dump: every page contains the generated
fortplot output, the standalone Vega HTML variant, the exact JSON spec, and the
source code used to create it.

.. raw:: html

   <div class="hero-links">
     <a class="hero-link hero-link--primary" href="examples/index.html">Open Examples Gallery</a>
     <a class="hero-link" href="getting_started.html">Get Started</a>
     <a class="hero-link" href="api.html">Browse API</a>
   </div>

Highlights
----------

- A small pyplot-shaped API for building chart specs from Python.
- Standalone Vega/Vega-Lite HTML output with no Python runtime in the browser.
- Optional ``mplvega.fortplot`` support for native Fortran-backed rendering.
- A generated gallery that keeps rendered output, JSON specs, and example code together.

.. include:: featured_examples.rst

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   getting_started
   renderers
   api
   examples/index

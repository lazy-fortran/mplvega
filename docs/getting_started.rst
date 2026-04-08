Getting Started
===============

Installation
------------

Install the package in editable mode during development:

.. code-block:: bash

   python -m pip install -e .

For examples and tests that use NumPy:

.. code-block:: bash

   python -m pip install -e .[test]

First Plot
----------

.. code-block:: python

   import mplvega as plt

   plt.figure(figsize=(6.4, 4.8))
   plt.plot([0, 1, 2], [0, 1, 4], label="quadratic")
   plt.title("My First Plot")
   plt.xlabel("x")
   plt.ylabel("y")
   plt.legend()

   plt.savefig("plot.vl.json")
   plt.savefig("plot.html")

The same figure can also be rendered through ``fortplot_render``:

.. code-block:: bash

   export MPLVEGA_FORTPLOT_RENDER=/path/to/fortplot_render

.. code-block:: python

   plt.savefig("plot.png")
   plt.savefig("plot.pdf")

Example Scripts
---------------

The checked-in examples all use a shared helper so every script emits the same
set of variants:

- ``.vl.json`` for the canonical Vega-Lite spec
- ``.html`` for direct browser viewing
- ``.png`` and ``.pdf`` through ``fortplot_render``

You can run an example directly:

.. code-block:: bash

   python examples/python/basic_plots/basic_plots.py

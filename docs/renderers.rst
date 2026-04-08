Renderers And Outputs
=====================

``mplvega`` deliberately separates the plotting surface from rendering. The
public API builds one canonical spec, and the file extension determines what
happens next when ``savefig`` is called.

Output Variants
---------------

``.vl.json``
   Writes the exact Vega-Lite JSON spec.

``.html``
   Writes a standalone HTML page that loads Vega, Vega-Lite, and Vega-Embed and
   renders the emitted spec in the browser.

``.png`` and ``.pdf``
   Calls ``fortplot_render`` through ``mplvega.fortplot``. Set
   ``MPLVEGA_FORTPLOT_RENDER`` to point at the executable when it is not on
   ``PATH``.

Environment
-----------

The fortplot bridge resolves the renderer in this order:

1. ``MPLVEGA_FORTPLOT_RENDER``
2. ``FORTPLOT_RENDER``
3. ``fortplot_render`` on ``PATH``

Examples Gallery
----------------

The docs build runs every checked-in example with all supported variants and
publishes them together. That keeps the gallery honest: the HTML, JSON, and
fortplot outputs shown on the site are the exact artifacts produced on CI.

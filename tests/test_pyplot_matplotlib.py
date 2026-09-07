"""Behavioral compatibility checked against an actual Matplotlib figure."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as mpl
import numpy as np
import pytest

import mplvega as plt
from mplvega._state import frontend


@pytest.fixture(autouse=True)
def fresh_figures():
    plt.figure()
    with matplotlib.rc_context(matplotlib.rcParamsDefault):
        mpl.figure()
        yield
    mpl.close("all")


@pytest.mark.parametrize("args", [
    (), (3,), ([1, 4, 2],), ([1, 4, 2], "--"),
    ([0, 1], [2, 3], ":"),
    ([0, 1], [2, 3], "--", [1, 2, 3], [3, 2, 1], ":"),
    (np.array([[1, 3], [2, 4], [4, 5]]),),
    ([0, 1, 2], np.array([[1, 3], [2, 4], [4, 5]])),
    (np.array([[0, 4], [1, 5], [2, 6]]), [1, 4, 2]),
])
def test_plot_series_match_matplotlib(args):
    reference = mpl.plot(*args)
    actual = plt.plot(*args)
    assert len(actual) == len(reference)
    for ours, theirs in zip(actual, reference):
        np.testing.assert_array_equal(ours.get_xdata(), theirs.get_xdata())
        np.testing.assert_array_equal(ours.get_ydata(), theirs.get_ydata())
    emitted = frontend.to_spec()
    layers = emitted.get("layer", [emitted]) if actual else []
    for layer, theirs in zip(layers, reference):
        np.testing.assert_array_equal([p["x"] for p in layer["data"]["values"]],
                                      theirs.get_xdata())
        np.testing.assert_array_equal([p["y"] for p in layer["data"]["values"]],
                                      theirs.get_ydata())


@pytest.mark.parametrize("args", [
    ([0, 1], [2]), (np.zeros((2, 3)), np.zeros((2, 2))),
    (np.zeros((2, 3, 4)),),
])
def test_invalid_plot_shapes_match_matplotlib(args):
    with pytest.raises(ValueError):
        mpl.plot(*args)
    with pytest.raises(ValueError):
        plt.plot(*args)


def test_data_mapping_labels_and_artist_updates_reach_spec():
    data = {"time": [0, 1, 2], "voltage": [2, 4, 1]}
    reference, = mpl.plot("time", "voltage", data=data)
    actual, = plt.plot("time", "voltage", data=data)
    assert actual.get_label() == reference.get_label()
    actual.set_label("updated")
    reference.set_label("updated")
    assert frontend.to_spec()["data"]["values"][0]["series"] == reference.get_label()


@pytest.mark.parametrize("values", [None, [0], [3], [1, 4, 2]])
@pytest.mark.parametrize("axis", ["x", "y"])
def test_limits_autoscale_partial_and_reset_match_matplotlib(values, axis):
    if values is not None:
        plt.plot(values, values)
        mpl.plot(values, values)
    ours, theirs = getattr(plt, axis + "lim"), getattr(mpl, axis + "lim")
    np.testing.assert_allclose(ours(), theirs())
    key = "left" if axis == "x" else "bottom"
    np.testing.assert_allclose(ours(**{key: -2}), theirs(**{key: -2}))
    np.testing.assert_allclose(ours(np.array([5, -3])), theirs(np.array([5, -3])))
    plt.figure()
    mpl.figure()
    np.testing.assert_allclose(ours(), theirs())


@pytest.mark.parametrize("bounds", [(float("nan"), 1), (0, float("inf"))])
def test_nonfinite_limits_rejected_like_matplotlib(bounds):
    with pytest.raises(ValueError):
        mpl.xlim(*bounds)
    with pytest.raises(ValueError):
        plt.xlim(*bounds)


def test_grid_toggle_uses_current_figure():
    for new_figure in (False, True, False):
        if new_figure:
            plt.figure()
            mpl.figure()
        plt.grid()
        mpl.grid()
        assert frontend._show_grid == mpl.gca().get_xgridlines()[0].get_visible()


@pytest.mark.parametrize("setter", ["title", "xlabel", "ylabel"])
def test_text_artists_update_rendered_label(setter):
    ours = getattr(plt, setter)("before")
    theirs = getattr(mpl, setter)("before")
    ours.set_text("after")
    theirs.set_text("after")
    assert getattr(frontend, "_" + setter) == theirs.get_text()


@pytest.mark.parametrize("fmt,kwargs", [
    ("ro", {}), ("b", {}), ("gs--", {}), ("k-", {"linewidth": 3}),
    ("-", {"color": np.array([0.2, 0.4, 0.6])}),
    ("ro-", {"color": "blue", "ls": ":", "ms": 8, "alpha": 0.5}),
])
def test_line_format_and_keyword_properties_match_matplotlib(fmt, kwargs):
    from matplotlib.colors import to_rgba

    actual, = plt.plot([0, 1, 2], [2, 1, 3], fmt, **kwargs)
    reference, = mpl.plot([0, 1, 2], [2, 1, 3], fmt, **kwargs)
    for name in ("linestyle", "marker", "linewidth", "markersize", "alpha"):
        assert getattr(actual, "get_" + name)() == getattr(reference, "get_" + name)()
    np.testing.assert_allclose(to_rgba(actual.get_color()), to_rgba(reference.get_color()))
    spec = frontend.to_spec()
    layers = spec.get("layer", [spec])
    for layer in layers:
        mark = layer["mark"]
        np.testing.assert_allclose(to_rgba(mark["color"]), to_rgba(reference.get_color()), atol=0.5 / 255)
        if mark["type"] == "point":
            assert mark["size"] == pytest.approx((reference.get_markersize() * mpl.gcf().dpi / 72) ** 2)
        else:
            assert mark["strokeWidth"] == pytest.approx(reference.get_linewidth() * mpl.gcf().dpi / 72)
    expected = int(reference.get_linestyle() != "None") + int(reference.get_marker() != "None")
    assert len(layers) == expected


def test_explicit_colors_and_markers_do_not_advance_line_cycle():
    for fmt in ("ro-", "--", "bs", "-"):
        actual, = plt.plot([1, 2], fmt)
        reference, = mpl.plot([1, 2], fmt)
        from matplotlib.colors import to_rgba
        np.testing.assert_allclose(to_rgba(actual.get_color()), to_rgba(reference.get_color()))


@pytest.mark.parametrize("shape", [(3, 3), (2, 4)])
def test_pcolormesh_field_order_matches_matplotlib(shape):
    from mplvega._state import _field_matrix

    values = np.arange(np.prod(shape)).reshape(shape)
    x, y = np.arange(shape[1] + 1), np.arange(shape[0] + 1)
    reference = mpl.pcolormesh(x, y, values)
    plt.pcolormesh(x, y, values)
    field = frontend.to_spec()["layer"][0]["fortplotField"]
    # Reconstruct exactly as native Fortran RESHAPE does, independently of the
    # browser adapter. Both must agree with the actual Matplotlib QuadMesh.
    native = np.asarray(field["z"]).reshape((field["nrows"], field["ncols"]), order="F")
    np.testing.assert_array_equal(native, reference.get_array())
    np.testing.assert_array_equal(_field_matrix(field, "z")[2], reference.get_array())


def test_contourf_preserves_asymmetric_field_and_default_colormap():
    values = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])
    reference = mpl.contourf([0, 1, 2], [0, 1, 2], values, levels=[0, 4, 8])
    plt.contourf([0, 1, 2], [0, 1, 2], values, levels=[0, 4, 8])
    field = frontend.to_spec()["layer"][0]["fortplotField"]
    native = np.asarray(field["z"]).reshape((field["nrows"], field["ncols"]), order="F")
    np.testing.assert_array_equal(native, values)
    assert field["colormap"] == reference.cmap.name


@pytest.mark.parametrize("overlay", [False, True])
def test_field_limits_follow_matplotlib_sticky_edges(overlay):
    x, y = [0, 1, 2, 3], [0, 1, 2]
    values = np.arange(6).reshape(2, 3)
    plt.pcolormesh(x, y, values)
    mpl.pcolormesh(x, y, values)
    if overlay:
        plt.plot([-1, 1], [1, 3])
        mpl.plot([-1, 1], [1, 3])
    np.testing.assert_allclose(plt.xlim(), mpl.xlim())
    np.testing.assert_allclose(plt.ylim(), mpl.ylim())


@pytest.mark.parametrize("marker", ["D", "d", "^", "v", "<", ">", "+", "x", "*"])
def test_browser_marker_geometry_matches_actual_matplotlib(marker):
    import re
    import xml.etree.ElementTree as ET
    import vl_convert as vlc
    from matplotlib.markers import MarkerStyle
    from mplvega._state import _browser_spec

    plt.plot([0], [0], marker=marker, ls="None", color="red", ms=14.4)
    svg = ET.fromstring(vlc.vegalite_to_svg(_browser_spec(frontend.to_spec())))
    path = next(element for element in svg.iter()
                if element.attrib.get("aria-roledescription") == "point")
    coords = np.asarray([float(v) for v in re.findall(r"[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?",
                                                      path.attrib["d"])])
    coords = coords.reshape(-1, 2)
    reference = MarkerStyle(marker)
    expected = reference.get_path().transformed(reference.get_transform()).vertices * 20
    expected[:, 1] *= -1
    np.testing.assert_allclose(coords.min(axis=0), expected.min(axis=0), atol=0.002)
    np.testing.assert_allclose(coords.max(axis=0), expected.max(axis=0), atol=0.002)
    parents = {child: parent for parent in svg.iter() for child in parent}
    inherited = path
    while "fill" not in inherited.attrib and inherited in parents:
        inherited = parents[inherited]
    assert (inherited.attrib.get("fill") != "none") == reference.is_filled()
    assert float(path.attrib.get("opacity", 1)) == 1.0


@pytest.mark.parametrize("setter", ["title", "xlabel", "ylabel"])
def test_old_text_handles_do_not_change_new_figures(setter):
    actual_old = getattr(plt, setter)("old figure")
    reference_old = getattr(mpl, setter)("old figure")
    plt.figure()
    mpl.figure()
    getattr(plt, setter)("new figure")
    reference_new = getattr(mpl, setter)("new figure")
    actual_old.set_text("changed old")
    reference_old.set_text("changed old")
    assert actual_old.get_text() == reference_old.get_text()
    assert getattr(frontend, "_" + setter) == reference_new.get_text()


def test_invisible_line_retains_data_limits_label_and_empty_browser_path():
    import xml.etree.ElementTree as ET
    import vl_convert as vlc
    from mplvega._state import _browser_spec

    actual, = plt.plot([10, 20], [30, 40], ls="None", label="hidden")
    reference, = mpl.plot([10, 20], [30, 40], ls="None", label="hidden")
    assert actual.get_label() == reference.get_label()
    np.testing.assert_array_equal(actual.get_data(), reference.get_data())
    np.testing.assert_allclose(plt.xlim(), mpl.xlim())
    np.testing.assert_allclose(plt.ylim(), mpl.ylim())
    svg = ET.fromstring(vlc.vegalite_to_svg(_browser_spec(frontend.to_spec())))
    paths = [element for element in svg.iter()
             if element.attrib.get("aria-roledescription") == "line mark"]
    assert not any(path.attrib.get("d") for path in paths)
    actual.set_label("renamed")
    reference.set_label("renamed")
    assert actual.get_label() == reference.get_label()


@pytest.mark.parametrize("axis", ["x", "y"])
def test_scalar_limit_sets_only_lower_bound(axis):
    actual, reference = getattr(plt, axis + "lim"), getattr(mpl, axis + "lim")
    np.testing.assert_allclose(actual(2), reference(2))
    np.testing.assert_allclose(actual(np.array(3)), reference(np.array(3)))


@pytest.mark.parametrize("values", [None, [1, 100], [1], [5], [10], [-5, 0, 1, 100]])
@pytest.mark.parametrize("axis", ["x", "y"])
def test_log_limit_getter_matches_actual_matplotlib(values, axis):
    getattr(plt, axis + "scale")("log")
    getattr(mpl, axis + "scale")("log")
    if values is not None:
        plt.plot(values, values)
        mpl.plot(values, values)
    actual = getattr(plt, axis + "lim")()
    reference = getattr(mpl, axis + "lim")()
    np.testing.assert_allclose(actual, reference)
    np.testing.assert_allclose(frontend.to_spec()["encoding"][axis]["scale"]["domain"],
                               reference)


@pytest.mark.parametrize("kwargs", [
    {"marker": "no-such-marker"}, {"alpha": -0.1}, {"alpha": 2},
    {"alpha": float("nan")}, {"alpha": float("inf")},
    {"alpha": "0.5"}, {"linewidth": 2, "lw": 3},
    {"linestyle": "no-such-style"},
])
def test_invalid_line_properties_fail_before_plot_state_changes(kwargs):
    with pytest.raises((ValueError, TypeError)) as reference_error:
        mpl.plot([0, 1], [1, 2], **kwargs)
    before = frontend.to_spec()
    with pytest.raises(type(reference_error.value)):
        plt.plot([0, 1], [1, 2], **kwargs)
    assert frontend.to_spec() == before


def test_later_invalid_format_does_not_add_earlier_groups():
    args = ([0, 1], [1, 2], "-", [2, 3], [4, 5], "not-a-format")
    with pytest.raises(ValueError):
        mpl.plot(*args)
    with pytest.raises(ValueError):
        plt.plot(*args)
    assert len(frontend._layers) == len(mpl.gca().lines)

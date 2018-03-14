# import json
import json
import leo.core.leoGlobals as g
from leo.core.leoQt import QtCore, QtWidgets
QtConst = QtCore.Qt

DockAreas = (
    QtConst.TopDockWidgetArea, QtConst.BottomDockWidgetArea,
    QtConst.LeftDockWidgetArea, QtConst.RightDockWidgetArea
)

@g.command('dock-dockify')
def dockify(event=None):
    """
    dockify - Move UI elements into docks

    Args:
        event: Leo command event
    """
    c = event['c']
    mw = c.frame.top
    childs = []
    splits = (QtWidgets.QSplitter, QtWidgets.QSplitterHandle)
    for splitter in c.frame.top.centralWidget().findChildren(QtWidgets.QSplitter):
        for child in splitter.children():
            if isinstance(child, splits):
                continue
            if not isinstance(child, QtWidgets.QWidget):
                continue  # have seen QActions
            g.log(child.objectName())
            g.log(child)
            g.log(getattr(child, '_ns_id', None))
            childs.append(child)

    for child in childs:
        w = QtWidgets.QDockWidget(child.objectName(), mw)
        w.setWidget(child)
        mw.addDockWidget(QtConst.TopDockWidgetArea, w)

    tb = QtWidgets.QToolBar()
    mw.addToolBar(QtConst.BottomToolBarArea, tb)
    tb.addWidget(c.frame.miniBufferWidget.widget.parent())

    mw.centralWidget().close()

    for child in mw.findChildren(QtWidgets.QDockWidget):
        if child.windowTitle() == 'logFrame':
            log_dock = child
            break
    else:
        raise Exception("Can't find logFrame")

    tw = c.frame.log.tabWidget
    while tw.count() > 1:
        dw = QtWidgets.QDockWidget(tw.tabText(1), mw)
        w = tw.widget(1)
        if not hasattr(w, '_ns_id'):
            w._ns_id = '_leo_tab:%s' % tw.tabText(1)
        dw.setWidget(w)
        mw.tabifyDockWidget(log_dock, dw)
def to_json(c):
    """to_json - introspect dock layout

    Args:
        c (context): outline
    Returns:
        dict: 'json' rep. of layout
    """

    _id = lambda x: x.widget()._ns_id

    ans = {'area': {}, 'widget': {}, 'tab_group': {}}
    widgets = c.frame.top.findChildren(QtWidgets.QDockWidget)
    tab_known = set()  # widgets with known tab status
    tab_group = 0
    for w in widgets:
        area = c.frame.top.dockWidgetArea(w)
        ans['area'].setdefault(area, []).append(_id(w))
        # dict for w, maybe already added by tabbed_with code
        d = ans['widget'].setdefault(_id(w), {})
        d['area'] = area
        # https://stackoverflow.com/a/22238571/1072212
        # test for tabs being visible
        d['visible'] = not w.visibleRegion().isEmpty()
        if w not in tab_known:  # see if widget is in a tab group
            tabbed_with = c.frame.top.tabifiedDockWidgets(w)
            if tabbed_with:
                assert w not in tabbed_with
                tabbed_with.append(w)  # include widget in group, this seems to
                                       # preserve tab order, but feels fragile
                tab_group += 1
                ans['tab_group'][tab_group] = [_id(i) for i in tabbed_with]
                for tw in tabbed_with:  # assign group ID to all members
                    tab_known.add(tw)
                    ans['widget'].setdefault(_id(tw), {})['tab_group'] = tab_group
            else:
                d['tab_group'] = None
        for i in 'x', 'y', 'width', 'height':
            d[i] = getattr(w, i)()
        d['_ns_id'] = _id(w)
    return ans


@g.command('dock-json')
def dock_json(event=None):
    """dock_json - introspect dock layout

    Args:
        event: Leo command event
    """
    json.dump(
        to_json(event['c']),
        open(g.os_path_join(g.computeHomeDir(), 'dock.json'), 'w'),
        indent=4,
        sort_keys=True
    )
@g.command('dock-toggle-titles')
def toggle_titles(event):

    c = event['c']
    mw = c.frame.top
    # find the first QDockWidget and see if titles are hidden
    if mw.findChild(QtWidgets.QDockWidget).titleBarWidget() is None:
        # default, not hidden, so hide with blank widget
        widget_factory = lambda: QtWidgets.QWidget()
    else:
        # hidden, so revert to default, not hidden
        widget_factory = lambda: None
    # apply to all QDockWidgets
    for child in mw.findChildren(QtWidgets.QDockWidget):
        child.setTitleBarWidget(widget_factory())

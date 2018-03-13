# import json
from pprint import pprint
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
        w = QtWidgets.QDockWidget(tw.tabText(1), mw)
        w.setWidget(tw.widget(1))
        mw.tabifyDockWidget(log_dock, w)
def to_json(c):
    """to_json - introspect dock layout

    Args:
        c (context): outline
    Returns:
        dict: 'json' rep. of layout
    """
    ans = {'area': {}, 'widget': {}, 'tab': {}}
    widgets = c.frame.top.findChildren(QtWidgets.QDockWidget)
    tab_known = set()
    tab_set = 0
    for w in widgets:
        area = c.frame.top.dockWidgetArea(w)
        ans['area'].setdefault(area, []).append(w)
        # maybe already added by tabbed_with code
        ans['widget'].setdefault(w, {})['area'] = area
        d = ans['widget'][w]
        # https://stackoverflow.com/a/22238571/1072212
        d['visible'] = not w.visibleRegion().isEmpty()
        if w not in tab_known:
            tabbed_with = c.frame.top.tabifiedDockWidgets(w)
            if tabbed_with:
                assert w not in tabbed_with
                tabbed_with[0:0] = [w]
                tab_set += 1
                ans['tab'][tab_set] = tabbed_with
                for tw in tabbed_with:
                    tab_known.add(tw)
                    ans['widget'].setdefault(tw, {})['tab'] = tab_set
            else:
                ans['widget'][w]['tab'] = None
        for i in 'x', 'y', 'width', 'height':
            d[i] = getattr(w, i)()
        d['_ns_id'] = getattr(w.widget(), '_ns_id', None) if w.widget() else None
    return ans


@g.command('dock-json')
def dock_json(event=None):
    """dock_json - introspect dock layout

    Args:
        event: Leo command event
    """
    g.log(pprint(to_json(event['c'])))
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

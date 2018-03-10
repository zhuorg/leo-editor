import leo.core.leoGlobals as g
from leo.core.leoQt import QtCore, QtWidgets
QtConst = QtCore.Qt
from leo.plugins.nested_splitter import NestedSplitter, NestedSplitterHandle

@g.command('dock-dockify')
def dockify(event):

    c = event['c']
    mw = c.frame.top
    childs = []
    for splitter in c.free_layout.get_top_splitter().self_and_descendants():
        for child in splitter.children():
            if isinstance(child, (NestedSplitter, NestedSplitterHandle)):
                continue
            if not isinstance(child, QtWidgets.QWidget):
                continue
            g.log(child.objectName())
            g.log(child)
            g.log(getattr(child, '_ns_id', None))
            childs.append(child)

    childs.reverse()
    # childs.append(c.frame.miniBufferWidget.widget.parent())
    for child in childs:
        w = QtWidgets.QDockWidget(child.objectName(), mw)
        w.setWidget(child)
        mw.addDockWidget(QtConst.TopDockWidgetArea, w)

    tb = QtWidgets.QToolBar()
    mw.addToolBar(QtConst.BottomToolBarArea, tb)
    tb.addWidget(c.frame.miniBufferWidget.widget.parent())

    # c.free_layout.get_top_splitter().close()
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

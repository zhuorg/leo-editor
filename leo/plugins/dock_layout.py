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
@g.command('dock-load-json-plot')
def load_json_plot(event):
    """load_json - load layout from JSON file

    Args:
        event: Leo command event
    """
    d = json.load(open(g.os_path_join(g.computeHomeDir(), 'dock.json')))
    from matplotlib import pyplot as plt
    for ns_id, w in d['widget'].items():
        if not w['visible']:
            continue
        x = abs(w['x'])
        y = abs(w['y'])
        width = abs(w['width'])
        height = abs(w['height'])
        plt.plot(
            [x, x+width, x+width, x, x],
            [-y, -y, -y-height, -y-height, -y]
        )
        plt.text(x+width/2, -y-height/2, ns_id)
    plt.show()
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

@g.command('dock-load-json')
def load_json(event):
    dm = DockManager(event['c'])
    dm.load_json()
class DockManager(object):
    """DockManager - manage QDockWidget layouts"""

    def __init__(self, c):
        """bind to Leo context

    Args:
        c (context): Leo outline
        """
        self.c = c


    @staticmethod
    def bbox(widgets):
        """bbox - get max extent of list of widgets

        Args:
            widgets ([{attr}]): list of dicts of widget's attributes
        Returns:
            tuple: xmin, ymin, xmax, ymax
        """
        x = []
        y = []
        for w in [i for i in widgets if i['visible']]:
            x.append(w['x'])
            x.append(w['x']+w['width'])
            y.append(-w['y'])
            y.append(-w['y']-w['height'])
        return min(x), min(y), max(x), max(y)
    @staticmethod
    def in_bbox(widget, bbox):
        """in_bbox - determine if the widget's in a bbox

        Args:
            widget ({attr}): widget attributes
            bbox (tuple): xmin, ymin, xmax, ymax
        Returns:
            bool: widget is in bbox
        """
        xctr = widget['x']+widget['width']/2
        yctr = -widget['y']-widget['height']/2
        return bbox[0] < xctr < bbox[2] and bbox[1] < yctr < bbox[3]

    @staticmethod
    def area_span(widget, bbox):
        """area_span - find max. proportion of area width/height spanned
        by widget

        Args:
            widget ({attr}): widget attributes
            bbox (tuple): xmin, ymin, xmax, ymax
        Returns:
            tuple: (float, bool) max. proportion, is width
        """
        xprop = widget['width'] / float(bbox[2] - bbox[0])
        yprop = widget['height'] / float(bbox[3] - bbox[1])
        if xprop > yprop:
            return xprop, True
        else:
            return yprop, False

    def find_dock(self, ns_id):
        """find_dock - find a dock widget

        Args:
            ns_id (str): the ID for the widget
        Returns:
            QWidget: the widget
        """
        for child in self.c.frame.top.findChildren(QtWidgets.QDockWidget):
            if child.widget()._ns_id == ns_id:
                return child
        g.log("Didn't find "+ns_id, color='warning')
    @staticmethod
    def swap_dock(a, b):
        """swap_dock - swap contents / titles of a pair of dock widgets

        Args:
            a (QDockWidget): widget a
            b (QDockWidget): widget b
        """
        w = a.widget()
        a_txt = a.windowTitle()
        a.setWidget(b.widget())
        a.setWindowTitle(b.windowTitle())
        b.setWidget(w)
        b.setWindowTitle(a_txt)
    def load_json(self):
        """load_json - load layout from JSON file

        Args:
            event: Leo command event
        """

        c = self.c
        d = json.load(open(g.os_path_join(g.computeHomeDir(), 'dock.json')))

        # make sure nothing's tabbed
        for w in c.frame.top.findChildren(QtWidgets.QDockWidget):
            if not d['widget'][w.widget()._ns_id]['visible']:
                c.frame.top.removeDockWidget(w)
            else:
                c.frame.top.addDockWidget(QtConst.TopDockWidgetArea, w)

        widgets = list(d['widget'].values())
        todo = [(widgets, self.bbox(widgets), None, None)]

        while todo:
            widgets, bbox, ref, align = todo.pop(0)
            ordered = sorted(
                widgets,
                key=lambda x: self.area_span(x, bbox),
                reverse=True
            )
            first = ordered[0]
            if self.area_span(first, bbox)[1]:  # width spanning
                below = (bbox[0], bbox[1], bbox[2], -first['y']-first['height'])
                above = (bbox[0], -first['y'], bbox[2], bbox[3])
                in_below = [i for i in widgets if i['visible'] and self.in_bbox(i, below)]
                in_above = [i for i in widgets if i['visible'] and self.in_bbox(i, above)]

                if ref:
                    ref_w = self.find_dock(ref)
                    nxt_w = self.find_dock(first['_ns_id'])

                    if align == QtConst.Vertical:
                        if d['widget'][ref]['y'] > first['y']:
                            print("Swap V, width")
                            self.swap_dock(ref_w, nxt_w)
                    else:
                        if d['widget'][ref]['x'] > first['x']:
                            self.swap_dock(ref_w, nxt_w)

                    c.frame.top.splitDockWidget(ref_w, nxt_w, align)

                if in_below:
                    todo.append((in_below, below, first['_ns_id'], QtConst.Vertical))
                if in_above:
                    todo.append((in_above, above, first['_ns_id'], QtConst.Vertical))
            else:  # height spanning
                left = (bbox[0], bbox[1], first['x'], bbox[3])
                right = (first['x']+first['width'], bbox[1], bbox[2], bbox[3])
                in_left = [i for i in widgets if i['visible'] and self.in_bbox(i, left)]
                in_right = [i for i in widgets if i['visible'] and self.in_bbox(i, right)]

                if ref:
                    ref_w = self.find_dock(ref)
                    nxt_w = self.find_dock(first['_ns_id'])

                    if align == QtConst.Vertical:
                        if d['widget'][ref]['y'] > first['y']:
                            self.swap_dock(ref_w, nxt_w)
                    else:
                        if d['widget'][ref]['x'] > first['x']:
                            self.swap_dock(ref_w, nxt_w)

                    c.frame.top.splitDockWidget(ref_w, nxt_w, align)

                if in_left:
                    todo.append((in_left, left, first['_ns_id'], QtConst.Horizontal))
                if in_right:
                    todo.append((in_right, right, first['_ns_id'], QtConst.Horizontal))

        if hasattr(c.frame.top, 'resizeDocks'):
            widgets = sorted(
                list(d['widget'].values()),
                key=lambda x: self.area_span(x, bbox),
                reverse=True
            )
            docks = [self.find_dock(i['_ns_id']) for i in widgets if i['visible']]
            heights = [i['height'] for i in widgets if i['visible']]
            c.frame.top.resizeDocks(docks, heights, QtConst.Vertical)
            widths = [i['width'] for i in widgets if i['visible']]
            c.frame.top.resizeDocks(docks, widths, QtConst.Horizontal)

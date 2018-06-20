"""
dock_layout - use QDockWidgets to layout Leo panes.

## Implementation notes

dock_layout puts all Leo panes into QDockWidgets. All docks are placed
in a single dock area, and the QMainWindow's main widget is not used.
Nested docking is enabled, allowing almost any layout to be created. The
Minibuffer is moved to the toolbar.
"""
import binascii
import json
import os
import types

import leo.core.leoGlobals as g
from leo.core.leoQt import QtCore, QtWidgets, QtGui
QtConst = QtCore.Qt

DockAreas = (
    QtConst.TopDockWidgetArea, QtConst.BottomDockWidgetArea,
    QtConst.LeftDockWidgetArea, QtConst.RightDockWidgetArea
)
def init():
    '''Return True if the plugin has loaded successfully.'''
    if g.app.gui.guiName() != "qt":
        print('dock_layout.py plugin not loading because gui is not Qt')
        return False
    g.registerHandler('after-create-leo-frame', onCreate)
    g.plugin_signon(__name__)
    create_commands()
    return True
def onCreate (tag, key):
    c = key.get('c')
    DockManager(c)
    ToolManager(c)
    CorePaneToolProvider(c)
def create_commands():
    """create_commands - add commands"""
    cmds = [
        'dockify', 'load_layout', 'save_layout', 'toggle_titles',
        'open_dock_menu',
    ]
    for cmd_name in cmds:
        def cmd(event, cmd_name=cmd_name):
            getattr(event['c']._dock_manager, cmd_name)()
        g.command("dock-%s" % cmd_name.replace('_', '-'))(cmd)

def wid(w, value=None):
    """wid - get/set widget ID. Didn't originally simply use Qt QObject name,
    but still a useful helper.

    Args:
        w: widget
        value (str): value to set
    Returns:
        str: widget id
    """
    if value is None:
        return w.objectName()
    else:
        w.setObjectName(value)

class LeoDockWidget(QtWidgets.QDockWidget):
    """LeoDockWidget - special close event etc.
    """

    def __init__(self, *args, **kwargs):
        QtWidgets.QDockWidget.__init__(self, *args, **kwargs)
    def closeEvent(self, event):
        w = self.widget()
        if w and wid(w) in ('outlineFrame', 'logFrame', 'bodyFrame'):
            return QtWidgets.QDockWidget.closeEvent(self, event)
        w.close()
        self.deleteLater()
class DockManager(object):
    """DockManager - manage QDockWidget layouts
    
    Key QObject names
    outlineFrame, logFrame, bodyFrame
    """

    def __init__(self, c):
        """bind to Leo context

        Args:
            c (context): Leo outline
        """
        self.c = c
        c._dock_manager = self
        self.tab2id = {}

        try:
            # check the default layout's loadable
            path = g.os_path_finalize_join(
                g.computeHomeDir(), '.leo', 'layouts', 'default.json')
            json.load(open(path))
            def load(timer, self=self):
                timer.stop()
                self.load()
            timer = g.IdleTime(load, delay=1000)
            timer.start()
            self.patch_things()
        except:
            g.log("Couldn't open default layout '%s'" % path)
    def dockify(self):
        """dockify - Move UI elements into docks"""
        c = self.c
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
            w = LeoDockWidget(child.objectName(), mw)
            w.setWidget(child)
            w.setObjectName(("_dw:%s" % wid(child)))
            mw.addDockWidget(QtConst.TopDockWidgetArea, w)

        tb = QtWidgets.QToolBar()
        mw.addToolBar(QtConst.BottomToolBarArea, tb)
        tb.addWidget(c.frame.miniBufferWidget.widget.parent())
        tb.setWindowTitle("Minibuffer")

        mw.centralWidget().close()

        for child in mw.findChildren(QtWidgets.QDockWidget):
            if child.windowTitle() == 'logFrame':
                log_dock = child
                break
        else:
            raise Exception("Can't find logFrame")

        tw = c.frame.log.tabWidget
        while tw.count() > 0:
            dw = LeoDockWidget(tw.tabText(1), mw)
            w = tw.widget(1)
            if not wid(w):
                wid(w, tw.tabText(1))
            self.tab2id[tw.tabText(1)] = wid(w)
            c._corepanetoolprovider.add_tab_pane(wid(w))

            dw.setWidget(w)
            dw.setObjectName("_dw:%s" % wid(w))
            mw.tabifyDockWidget(log_dock, dw)

    def find_dock(self, id_, state=None, title=None):
        """find_dock - find a dock widget

        Args:
            ns_id (str): the ID for the widget
        Returns:
            QWidget: the widget
        """
        for child in self.c.frame.top.findChildren(QtWidgets.QDockWidget):
            if wid(child.widget()) == id_:
                return child
        w = self.c._tool_manager.provide(id_, state=state)
        if w:
            dock = LeoDockWidget()# self.c.frame.top)
            dock.setWidget(w)
            dock.setObjectName(("_dw:%s" % wid(w)))
            dock.setWindowTitle(title or wid(w))
            self.c.frame.top.addDockWidget(QtConst.TopDockWidgetArea, dock)
            return dock
        g.log("Didn't find %s" % id_, color='warning')
    def from_dict(self, data):
        """from_dict - load from dict

        Args:
            data (dict): dict describing layout
        """
        for widget in data['widgets']:
            # creates panes that don't exist
            self.find_dock(widget['id'], state=widget['state'], title=widget['title'])
        # restores geometry (not state) of panes
        self.c.frame.top.restoreState(binascii.a2b_base64(data['QtLayout']))
        self.toggle_titles(data['title_mode'])
    def load(self):
        """load - load layout on idle after load"""
        self.dockify()
        def delayed_layout(timer, self=self):
            timer.stop()
            g.es('loading layout')
            self.load_layout_file(g.os_path_finalize_join(
                g.computeHomeDir(), '.leo', 'layouts', 'default.json'))
        timer = g.IdleTime(delayed_layout, delay=1000)
        timer.start()
    def load_layout(self):
        """load_layout - load a layout"""
        layouts = g.os_path_finalize_join(g.computeHomeDir(), '.leo', 'layouts')
        if not g.os_path_exists(layouts):
            os.makedirs(layouts)
        file = g.app.gui.runOpenFileDialog(self.c, "Pick a layout",
            [("Layout files", '*.json'), ("All files", '*')], startpath=layouts)
        if file:
            self.load_layout_file(file)
    def load_layout_file(self, file):
        """load_layout_file - load a layout file

        Args:
            file (str): path to file
        """
        with open(file) as in_:
            self.from_dict(json.load(in_))

    def open_dock_menu(self, pos=None):
        """open_dock_menu - open a dock"""
        menu = QtWidgets.QMenu(self.c.frame.top)

        for id_, name in self.c._tool_manager.tools():
            act = QtWidgets.QAction(name, menu)
            act.triggered.connect(lambda checked, id_=id_, name=name: self.open_dock(id_, name))
            menu.addAction(act)
        menu.exec_(QtGui.QCursor.pos())
    def open_dock(self, id_, name):
        """open_dock - open a dock

        Args:
            id_ (str): dock ID
        """
        w = self.c._tool_manager.provide(id_)
        if w:
            wid(w, id_)
            main_window = self.c.frame.top
            new_dock = LeoDockWidget(name, main_window)
            new_dock.setWidget(w)
            new_dock.setObjectName("_dw:%s" % wid(w))
            main_window.addDockWidget(QtConst.TopDockWidgetArea, new_dock)
        else:
            g.log("Could not find tool: %s" % id_, color='error')
    def patch_things(self):
        """patch_things - patch core"""
        def selectTab(self, tabName, createText=True, widget=None, wrap='none', dc=self, rec=[]):
            if rec:
                return
            rec.append(1)
            if tabName not in dc.tab2id:
                g.log("Didn't find tab: %s" % tabName)
                del rec[0]
                return
            w = dc.find_dock(dc.tab2id[tabName])
            w.raise_()
            del rec[0]

        self.c.frame.log.selectTab = types.MethodType(selectTab, self.c.frame.log)
    def save_layout(self):
        """save_layout - save a layout"""
        # FIXME: startpath option here?  cwd doesn't work
        layouts = g.os_path_finalize_join(g.computeHomeDir(), '.leo', 'layouts')
        if not g.os_path_exists(layouts):
            os.makedirs(layouts)
        old_cwd = os.getcwd()
        os.chdir(layouts)
        file = g.app.gui.runSaveFileDialog(self.c, title="Save a layout",
            filetypes=[("Layout files", '*.json'), ("All files", '*')],
            initialfile=layouts)
        os.chdir(old_cwd)
        if not file.endswith('.json'):
            file += '.json'
        if file:
            self.save_layout_file(file)
    def save_layout_file(self, file):
        """save_layout_file - save layout to a file

        Args:
            file (str): path to file
        """
        with open(file, 'w') as out:
            json.dump(self.to_dict(), out)
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
    def to_dict(self):
        """to_dict - return dict representing layout"""

        return {
            'QtLayout': binascii.b2a_base64(self.c.frame.top.saveState()).decode('utf-8'),
            'widgets': [
                {
                    'title': i.windowTitle(),
                    'id': wid(i.widget()),
                    'state': self.c._tool_manager.save_state(i.widget()),
                }
                for i in self.c.frame.top.findChildren(QtWidgets.QDockWidget)
            ],
            'title_mode': 'off' if self.titles_hidden() else 'on'
        }
    def titles_hidden(self):
        # find the first QDockWidget and see if titles are hidden
        return self.c.frame.top.findChild(QtWidgets.QDockWidget).titleBarWidget() is not None

    def toggle_titles(self, mode=None):
        c = self.c
        mw = c.frame.top
        # find the first QDockWidget and see if titles are hidden
        if mode == 'on' or self.titles_hidden():
            # hidden, so revert to not hidden
            widget_factory = lambda: None
        else:
            # not hidden, so hide with blank widget
            widget_factory = lambda: QtWidgets.QWidget()
        # apply to all QDockWidgets
        for child in mw.findChildren(QtWidgets.QDockWidget):
            child.setTitleBarWidget(widget_factory())
class ToolManager(object):
    """ToolManager - manage tools (panes, widgets)

    Things that provide widgets should do:

        c.user_dict.setdefault('_tool_providers', []).append(provider)

    which avoids dependence of this class being inited.

    provider should be an object with callables as follows:

        provider.tm_provides() - a list of (id_, name) tuples, ids and names of
        things this provider can provide

        provider.tm_provide(id_, state) - provide a QWidget based on ID, which
        will be initialized with dict state

        provider.tm_save_state(w) - provide a JSON serialisable dict that saves
        state for widget w

    NOTE: providers are only asked to provide things they've already claimed
    (tm_provides()) they provide, unline NestedSplitter which asked all
    providers in turn to provide a widget. So providers /no longer/ need to
    check what they're being asked for, unless they provide more than one thing.

    Example:

        class LeoEditPane:
            def tm_provides(): return [('_lep', "Leo Edit Pane")]
            def tm_provide(id_, state):
                assert id_ == '_lep'
                return self.make_editpane(state)
                # e.g. if 'UNL' in state, select that node
            def tm_save_state(w):
                assert w._tm_id == '_lep'
                return self.save_state(w)
                # e.g. {'UNL': self.c.vnode2position(w.v).get_UNL()}
    """

    def __init__(self, c):
        """bind to c"""
        self.c = c
        self.providers = c.user_dict.setdefault('_tool_providers', [])
        c._tool_manager = self

    def tools(self):
        """tools - list available tools"""
        ans = []
        for provider in self.providers:
            ans.extend(provider.tm_provides())
        return ans

    def provide(self, id_, state=None):
        if state is None:
            state = {}
        for provider in self.providers:
            ids = [i[0] for i in provider.tm_provides()]
            if id_ in ids:
                w = provider.tm_provide(id_, state)
                if w:
                    wid(w, id_)
                    g.log("Provided %s" % id_)
                    return w
        g.log("Couldn't provide %s" % id_, color='warning')
    def save_state(self, w):
        """find provider for w and call save_state() on it"""
        for provider in self.providers:
            ids = [i[0] for i in provider.tm_provides()]
            if wid(w) in ids:
                return provider.tm_save_state(w)
        return {}
class CorePaneToolProvider:
    def __init__(self, c):
        self.c = c
        c._corepanetoolprovider = self
        c.user_dict.setdefault('_tool_providers', []).append(self)
        self.core_panes = [
            ('outlineFrame', 'Tree pane'),
            ('logFrame', 'Log pane'),
            ('bodyFrame', 'Body pane'),
        ]
    def add_tab_pane(self, name):
        self.core_panes.append((name, name))
    def tm_provides(self):
        return self.core_panes
    def tm_provide(self, id_, state):
        w = self.c.frame.top.findChild(QtWidgets.QWidget, id_)
        if w and isinstance(w.parent(), QtWidgets.QDockWidget):
            w.parent().deleteLater()
        return w
    def tm_save_state(self, w):
        return {}

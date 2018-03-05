# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20140907131341.18707: * @file ../plugins/qt_tree.py
#@@first
'''Leo's Qt tree class.'''
#@+<< imports >>
#@+node:ekr.20140907131341.18709: ** << imports >> (qt_tree.py)
import leo.core.leoGlobals as g
import leo.core.leoFrame as leoFrame
import leo.core.leoNodes as leoNodes
import leo.core.leoPlugins as leoPlugins # Uses leoPlugins.TryNext.
import leo.plugins.qt_text as qt_text
from leo.core.leoQt import QtConst, QtCore, QtGui, QtWidgets
import re
#@-<< imports >>
#@+others
#@+node:ekr.20160514120051.1: ** class LeoQtTree
class LeoQtTree(leoFrame.LeoTree):
    '''Leo Qt tree class'''
    callbacksInjected = False # A class var.
    #@+others
    #@+node:ekr.20110605121601.18404: *3* qtree.Birth
    #@+node:ekr.20110605121601.18405: *4* qtree.__init__
    def __init__(self, c, frame):
        '''Ctor for the LeoQtTree class.'''
        leoFrame.LeoTree.__init__(self, frame)
            # Init the base class.
        self.c = c
        # Widget independent status ivars...
        self.prev_v = None
        self.redrawing = False
        self.redrawCount = 0 # Count for debugging.
        self.revertHeadline = None # Previous headline text for abortEditLabel.
        self.selecting = False
        # Debugging...
        self.nodeDrawCount = 0
        self.traceCallersFlag = False # Enable traceCallers method.
        self.editWidgetsDict = {} # keys are native edit widgets, values are wrappers.
        self.reloadSettings()
        # Components.
        self.canvas = self # An official ivar used by Leo's core.
        self.headlineWrapper = qt_text.QHeadlineWrapper # This is a class.
        self.treeWidget = w = frame.top.leo_ui.treeWidget # An internal ivar.
            # w is a LeoQTreeWidget, a subclass of QTreeWidget.
        # "declutter", node appearance tweaking
        self.declutter_patterns = None  # list of pairs of patterns for decluttering
        self.declutter_iconDir = g.os_path_abspath(g.os_path_normpath(
            g.os_path_join(g.app.loadDir,"..","Icons")))
        self.declutter_update = False  # true when update on idle needed
        self.rootPosition = None # 2018/03/05 for hoist and chapters 
        g.registerHandler('save1', self.clear_visual_icons)
        g.registerHandler('save2', self.reset_visual_icons)
        w.setIconSize(QtCore.QSize(160, 16))
    #@+node:ekr.20110605121601.17866: *4* qtree.get_name
    def getName(self):
        '''Return the name of this widget: must start with "canvas".'''
        return 'canvas(tree)'
    #@+node:ekr.20110605121601.18406: *4* qtree.initAfterLoad
    def initAfterLoad(self):
        '''Do late-state inits.'''
        # Called by Leo's core.
        c = self.c
        # w = c.frame.top
        tw = self.treeWidget
        if not LeoQtTree.callbacksInjected:
            LeoQtTree.callbacksInjected = True
            self.injectCallbacks() # A base class method.
        tw.itemDoubleClicked.connect(self.onItemDoubleClicked)
        tw.itemClicked.connect(self.onItemClicked)
        tw.itemSelectionChanged.connect(self.onTreeSelect)
        tw.itemCollapsed.connect(self.onItemCollapsed)
        tw.itemExpanded.connect(self.onItemExpanded)
        tw.customContextMenuRequested.connect(self.onContextMenu)
        # tw.onItemChanged.connect(self.onItemChanged)
        g.app.gui.setFilter(c, tw, self, tag='tree')
        # 2010/01/24: Do not set this here.
        # The read logic sets c.changed to indicate nodes have changed.
        # c.setChanged(False)
        self.rootVnode = c.hiddenRootNode
        self.full_redraw()

    #@+node:ekr.20110605121601.17871: *4* qtree.reloadSettings
    def reloadSettings(self):
        '''LeoQtTree.'''
        c = self.c
        self.auto_edit = c.config.getBool('single_click_auto_edits_headline', False)
        self.allow_clone_drags = c.config.getBool('allow_clone_drags')
        self.enable_drag_messages = c.config.getBool("enable_drag_messages")
        self.select_all_text_when_editing_headlines = c.config.getBool(
            'select_all_text_when_editing_headlines')
        self.stayInTree = c.config.getBool('stayInTreeAfterSelect')
        self.use_chapters = c.config.getBool('use_chapters')
        self.use_declutter = c.config.getBool('tree-declutter', default=False)

    #@+node:ekr.20110605121601.17940: *4* qtree.wrapQLineEdit
    def wrapQLineEdit(self, w):
        '''A wretched kludge for MacOs k.masterMenuHandler.'''
        c = self.c
        if isinstance(w, QtWidgets.QLineEdit):
            wrapper = self.edit_widget(c.p)
        else:
            wrapper = w
        return wrapper
    #@+node:ekr.20110605121601.17868: *3* qtree.Debugging & tracing
    def error(self, s):
        if not g.app.unitTesting:
            g.trace('LeoQtTree Error: %s' % (s), g.callers())

    def traceItem(self, item):
        if item:
            # A QTreeWidgetItem.
            return 'item %s: %s' % (id(item), item.text(0))
        else:
            return '<no item>'

    def traceCallers(self):
        if self.traceCallersFlag:
            return g.callers(5, excludeCaller=True)
        else:
            return ''
    #@+node:ekr.20110605121601.17872: *3* qtree.Drawing
    #@+node:ekr.20110605121601.18408: *4* qtree.clear
    def clear(self):
        '''Clear all widgets in the tree.'''
        w = self.treeWidget
        w.clear()
    #@+node:vitalije.20180304135426.1: *4* qtree.full_redraw   new algorithm
    def full_redraw(self, p=None, scroll=True, forceDraw=False):
        self.rootPosition = p
        self.rootVnode = p.v if p else self.c.hiddenRootNode
        self.sync_item_with_p(p, p)


    def redraw(self, *args, **kw):
        pass

    def sync_vnodes(self, vnodes):
        tw = self.treeWidget
        tw.blockSignals(True)
        rpos = self.rootPosition
        if self.rootVnode in vnodes:
            self.sync_item_with_p(rpos, rpos)
        else:
            for v in vnodes:
                for p in v.positions():
                    item = self.position2item(p, rpos)
                    if item:
                        self.sync_item_with_p(p, rpos)
        tw.blockSignals(False)
        tw.update()
    #@+node:vitalije.20180305092029.1: *5* sync_item_with_p
    def sync_item_with_p(self, p, relativeTo=None):
        c = self.c
        tw = self.treeWidget
        tw.blockSignals(True)
        #@+others
        #@+node:vitalije.20180304152436.1: *6* ensure_root_size
        def ensure_root_size(v):
            nc = tw.topLevelItemCount()
            while nc > len(v.children):
                nc -= 1
                tw.takeTopLevelItem(nc)
            for i in range(nc, len(v.children)):
                ni = QtWidgets.QTreeWidgetItem(tw)
                ni.setFlags(ni.flags() | QtCore.Qt.ItemIsEditable)
            assert tw.topLevelItemCount() == len(v.children)
        #@+node:vitalije.20180304152442.1: *6* ensure_same_size
        def ensure_same_size(item, v):
            nc = item.childCount()
            while nc > len(v.children):
                nc -= 1
                item.removeChild(item.child(nc))
            for i in range(nc, len(v.children)):
                ni = QtWidgets.QTreeWidgetItem(item)
                ni.setFlags(ni.flags() | QtCore.Qt.ItemIsEditable)
            assert item.childCount() == len(v.children)
        #@+node:vitalije.20180304152448.1: *6* addone
        def addone(par, p):
            v = p.v
            ensure_same_size(par, v)
            for i, v1 in enumerate(v.children):
                item = par.child(i)
                item.setText(0, v1.h)
                p1 = p.nthChild(i)
                data = inds(p1)
                item.setData(0, 0x100, data)
                item.setExpanded(p1.isExpanded())
                visititem(item, p1)
                seticon(p1, item)
                addone(item, p1)
        #@+node:vitalije.20180304195157.1: *6* seticon
        def seticon(p, item):
            if self.use_declutter:
                self.declutter_node(c, p, item)
            if p:
                icon = self.getIcon(p)
                item.setIcon(0, icon)
        #@+node:vitalije.20180305191846.1: *6* visititem
        def visititem(item, p):
            try:
                g.visit_tree_item(self.c, p, item)
            except leoPlugins.TryNext:
                pass
        #@-others
        inds = lambda p: tuple(x[1] for x in p.stack) + (p.childIndex(), p.gnx)
        if p is relativeTo:
            # syncing toplevel
            stack0 = p.stack + [(p.v, p.childIndex())] if p else None
            ensure_root_size(self.rootVnode)
            for i, v in enumerate(self.rootVnode.children):
                item = tw.topLevelItem(i)
                p1 = leoNodes.Position(v, i, stack0)
                item.setText(0, v.h)
                item.setData(0, 0x100, inds(p1))
                item.setExpanded(p1.isExpanded())
                visititem(item, p1)
                seticon(p1, item)
                addone(item, p1)
        else:
            # syncing one item
            item = self.position2item(p, relativeTo)
            assert item
            item.setText(0, p.h)
            item.setData(0, 0x100, (p.childIndex(), p.gnx))
            visititem(item, p)
            seticon(p, item)
            addone(item, p)
        tw.blockSignals(False)
    #@+node:tbrown.20150807093655.1: *4* qtree.clear_visual_icons
    def clear_visual_icons(self, tag, keywords):
        """clear_visual_icons - remove 'declutter' icons before save

        this method must return None to tell Leo to continue normal processing

        :param str tag: 'save1'
        :param dict keywords: Leo hook keywords
        """

        if not self.use_declutter:
            return None

        c = keywords['c']
        if c != self.c:
            return None

        if c.config.getBool('tree-declutter', default=False):
            com = c.editCommands
            for nd in c.all_unique_positions():
                icons = [i for i in com.getIconList(nd) if 'visualIcon' not in i]
                com.setIconList(nd, icons, False)

        self.declutter_update = True

        return None
    #@+node:vitalije.20180305150347.1: *4* qtree.reset_visual_icons
    def reset_visual_icons(self, tag, keywords):
        if not self.use_declutter:
            return None
        c = keywords['c']
        if c != self.c:
            return None
        p = c.rootPosition()
        while p:
            item = self.position2item(p, self.rootPosition)
            item.setText(0, p.h)
            self.declutter_node(c, p, item)
            icon = self.getIcon(p)
            item.setIcon(0, icon)
            p.moveToThreadNext()
    #@+node:tbrown.20150807090639.1: *4* qtree.declutter_node & helpers
    def declutter_node(self, c, p, item):
        """declutter_node - change the appearance of a node

        :param commander c: commander containing node
        :param position p: position of node
        :param QWidgetItem item: tree node widget item
        """
        trace = False and not g.unitTesting
        if self.declutter_patterns is None:
            self.declutter_patterns = []
            lines = c.config.getData("tree-declutter-patterns")
            for line in lines:
                try:
                    cmd, arg = line.split(None, 1)
                except ValueError:
                    # Allow empty arg, and guard against user errors.
                    cmd = line.strip()
                    arg = ''
                if cmd == 'RULE':
                    self.declutter_patterns.append((re.compile(arg), []))
                else:
                    self.declutter_patterns[-1][1].append((cmd, arg))
            if trace: g.trace('PATTERNS', self.declutter_patterns)
        text = str(item.text(0)) if g.isPython3 else g.u(item.text(0))
        new_icons = []
        for pattern, cmds in self.declutter_patterns:
            for func in (pattern.match, pattern.search):
                m = func(text)
                if m:
                    # if trace: g.trace(func.__name__, text)
                    for cmd, arg in cmds:
                        if self.declutter_replace(arg, cmd, item, m, pattern, text):
                            pass
                        else:
                            self.declutter_style(arg, c, cmd, item, new_icons)
                    break # Don't try pattern.search if pattern.match succeeds.
        com = c.editCommands
        allIcons = com.getIconList(p)
        icons = [i for i in allIcons if 'visualIcon' not in i]
        if len(allIcons) != len(icons) or new_icons:
            for icon in new_icons:
                com.appendImageDictToList(
                    icons, self.declutter_iconDir,
                    g.app.gui.getImageImageFinder(icon), 2,
                    on='vnode', visualIcon='1'
                )
            com.setIconList(p, icons, False)
    #@+node:ekr.20171122064635.1: *5* qtree.declutter_replace
    def declutter_replace(self, arg, cmd, item, m, pattern, text):
        '''
        Execute cmd and return True if cmd is any replace command.
        '''
        if cmd == 'REPLACE':
            text = pattern.sub(arg, text)
            item.setText(0, text)
            return True
        elif cmd == 'REPLACE-HEAD':
            s = text[:m.start()]
            item.setText(0, s.rstrip())
            return True
        elif cmd == 'REPLACE-TAIL':
            s = text[m.end():]
            item.setText(0, s.lstrip())
            return True
        elif cmd == 'REPLACE-REST':
            s = text[:m.start] + text[m.end():]
            item.setText(0, s.strip())
            return True
        else:
            return False
        
    #@+node:ekr.20171122055719.1: *5* qtree.declutter_style
    def declutter_style(self, arg, c, cmd, item, new_icons):
        '''Handle style options.'''
        arg = c.styleSheetManager.expand_css_constants(arg).split()[0]
        if cmd == 'ICON':
            new_icons.append(arg)
        elif cmd == 'BG':
            item.setBackground(0, QtGui.QBrush(QtGui.QColor(arg)))
        elif cmd == 'FG':
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(arg)))
        elif cmd == 'FONT':
            item.setFont(0, QtGui.QFont(arg))
        elif cmd == 'ITALIC':
            font = item.font(0)
            font.setItalic(bool(int(arg)))
            item.setFont(0, font)
        elif cmd == 'WEIGHT':
            arg = getattr(QtGui.QFont, arg, 75)
            font = item.font(0)
            font.setWeight(arg)
            item.setFont(0, font)
        elif cmd == 'PX':
            font = item.font(0)
            font.setPixelSize(int(arg))
            item.setFont(0, font)
        elif cmd == 'PT':
            font = item.font(0)
            font.setPointSize(int(arg))
            item.setFont(0, font)
    #@+node:ekr.20140907201613.18986: *4* qtree.repaint
    def repaint(self):
        '''Repaint the widget.'''
        w = self.treeWidget
        w.repaint()
        w.resizeColumnToContents(0) # 2009/12/22
    #@+node:ekr.20110605121601.17885: *3* qtree.Event handlers
    #@+node:ekr.20110605121601.17887: *4*  qtree.Click Box
    #@+node:ekr.20110605121601.17888: *5* qtree.onClickBoxClick
    def onClickBoxClick(self, event, p=None):
        c = self.c
        g.doHook("boxclick1", c=c, p=p, event=event)
        g.doHook("boxclick2", c=c, p=p, event=event)
        c.outerUpdate()
    #@+node:ekr.20110605121601.17889: *5* qtree.onClickBoxRightClick
    def onClickBoxRightClick(self, event, p=None):
        c = self.c
        g.doHook("boxrclick1", c=c, p=p, event=event)
        g.doHook("boxrclick2", c=c, p=p, event=event)
        c.outerUpdate()
    #@+node:ekr.20110605121601.17890: *5* qtree.onPlusBoxRightClick
    def onPlusBoxRightClick(self, event, p=None):
        c = self.c
        g.doHook('rclick-popup', c=c, p=p, event=event, context_menu='plusbox')
        c.outerUpdate()
    #@+node:ekr.20110605121601.17891: *4*  qtree.Icon Box
    # For Qt, there seems to be no way to trigger these events.
    #@+node:ekr.20110605121601.17892: *5* qtree.onIconBoxClick
    def onIconBoxClick(self, event, p=None):
        c = self.c
        g.doHook("iconclick1", c=c, p=p, event=event)
        g.doHook("iconclick2", c=c, p=p, event=event)
        c.outerUpdate()
    #@+node:ekr.20110605121601.17893: *5* qtree.onIconBoxRightClick
    def onIconBoxRightClick(self, event, p=None):
        """Handle a right click in any outline widget."""
        c = self.c
        g.doHook("iconrclick1", c=c, p=p, event=event)
        g.doHook("iconrclick2", c=c, p=p, event=event)
        c.outerUpdate()
    #@+node:ekr.20110605121601.17894: *5* qtree.onIconBoxDoubleClick
    def onIconBoxDoubleClick(self, event, p=None):
        c = self.c
        if not p: p = c.p
        if not g.doHook("icondclick1", c=c, p=p, event=event):
            self.endEditLabel()
            self.OnIconDoubleClick(p) # Call the method in the base class.
        g.doHook("icondclick2", c=c, p=p, event=event)
        c.outerUpdate()
    #@+node:ekr.20110605121601.17886: *4* qtree.busy
    def busy(self):
        '''not necessary any more.'''
        return False
    #@+node:ekr.20110605121601.18437: *4* qtree.onContextMenu
    def onContextMenu(self, point):
        c = self.c
        w = self.treeWidget
        handlers = g.tree_popup_handlers
        menu = QtWidgets.QMenu()
        menuPos = w.mapToGlobal(point)
        if not handlers:
            menu.addAction("No popup handlers")
        p = c.p.copy()
        done = set()
        for h in handlers:
            # every handler has to add it's QActions by itself
            if h in done:
                # do not run the same handler twice
                continue
            h(c, p, menu)
        menu.popup(menuPos)
        self._contextmenu = menu
    #@+node:ekr.20110605121601.17912: *4* qtree.onHeadChanged
    # Tricky code: do not change without careful thought and testing.

    def onHeadChanged(self, p, undoType='Typing', s=None, e=None):
        '''Officially change a headline.'''
        trace = False and not g.unitTesting
        trace_hook = True
        verbose = False
        c = self.c; u = c.undoer
        if not p:
            if trace and verbose: g.trace('** no p')
            return
        item = self.getCurrentItem()
        if not item:
            if trace and verbose: g.trace('** no item')
            return
        if not e:
            e = self.getTreeEditorForItem(item)
        if not e:
            if trace and verbose: g.trace('(nativeTree) ** not editing')
            return
        s = g.u(e.text())
        self.closeEditorHelper(e, item)
        oldHead = p.h
        changed = s != oldHead
        if trace and trace_hook:
            g.trace('headkey1: changed %s' % (changed), g.callers())
        if g.doHook("headkey1", c=c, p=c.p, v=c.p, s=s, changed=changed):
            return
        if changed:
            # New in Leo 4.10.1.
            if trace: g.trace('(nativeTree) new', repr(s), 'old', repr(p.h))
            #@+<< truncate s if it has multiple lines >>
            #@+node:ekr.20120409185504.10028: *5* << truncate s if it has multiple lines >>
            # Remove trailing newlines before warning of truncation.
            s = s.rstrip()
            # Warn if there are multiple lines.
            if '\n' in s:
                s = s.split('\n', 1)[0]
                if s != oldHead:
                    g.warning("truncating headline to one line")
            limit = 1000
            if len(s) > limit:
                s = s[: limit]
                if s != oldHead:
                    g.warning("truncating headline to", limit, "characters")
            #@-<< truncate s if it has multiple lines >>
            p.initHeadString(s)
            item.setText(0, s)
            if self.use_declutter:
                self.declutter_node(c, p, item)
            icon = self.getIcon(p)
            item.setIcon(0, icon)
            undoData = u.beforeChangeNodeContents(p, oldHead=oldHead)
            if not c.changed: c.setChanged(True)
            # New in Leo 4.4.5: we must recolor the body because
            # the headline may contain directives.
            c.frame.body.recolor(p)
            dirtyVnodeList = p.setDirty()
            u.afterChangeNodeContents(p, undoType, undoData,
                dirtyVnodeList=dirtyVnodeList, inHead=True) # 2013/08/26.
        g.doHook("headkey2", c=c, p=c.p, v=c.p, s=s, changed=changed)
        # This is a crucial shortcut.
        if g.unitTesting: return
        p.v.contentModified()
        c.outerUpdate()
    #@+node:ekr.20110605121601.17896: *4* qtree.onItemClicked
    def onItemClicked(self, item, col, auto_edit=False):
        '''Handle a click in a BaseNativeTree widget item.'''
        # This is called after an item is selected.
        #print(item.data(0, 0x100))
        #return
        trace = False and not g.unitTesting
        c = self.c
        p = self.item2position(item)
        if p:
            auto_edit = self.prev_v == p.v
            self.prev_v = p.v
            event = None
            mods = g.app.gui.qtApp.keyboardModifiers()
            isCtrl = bool(mods & QtConst.ControlModifier)
            if trace: g.trace('auto_edit', auto_edit, 'ctrl', isCtrl, p.h)
            # We could also add support for QtConst.ShiftModifier,
            # QtConst.AltModifier	& QtConst.MetaModifier.
            if isCtrl:
                if g.doHook("iconctrlclick1", c=c, p=p, event=event) is None:
                    c.frame.tree.OnIconCtrlClick(p) # Call the base class method.
                g.doHook("iconctrlclick2", c=c, p=p, event=event)
            else:
                # 2014/02/21: generate headclick1/2 instead of iconclick1/2
                g.doHook("headclick1", c=c, p=p, event=event)
                g.doHook("headclick2", c=c, p=p, event=event)
        else:
            auto_edit = None
            g.trace('*** no p')
        # 2011/05/27: click here is like ctrl-g.
        c.k.keyboardQuit(setFocus=False)
        c.treeWantsFocus() # 2011/05/08: Focus must stay in the tree!
        c.outerUpdate()
        # 2011/06/01: A second *single* click on a selected node
        # enters editing state.
        if auto_edit and self.auto_edit:
            e, wrapper = self.createTreeEditorForItem(item)
            # 2014/10/26: Reset find vars.
        c.findCommands.reset_state_ivars()
    #@+node:ekr.20110605121601.17895: *4* qtree.onItemCollapsed
    def onItemCollapsed(self, item):
        c = self.c
        p = self.item2position(item)
        if p and p.isExpanded():
            p.contract()
        self.treeWidget.setCurrentItem(item, 0,
                QtCore.QItemSelectionModel.SelectionFlags(3))
        c.outerUpdate()
    #@+node:ekr.20110605121601.17897: *4* qtree.onItemDoubleClicked
    def onItemDoubleClicked(self, item, col):
        '''Handle a double click in a BaseNativeTree widget item.'''
        c = self.c
        e, wrapper = self.createTreeEditorForItem(item)
        if not e:
            g.trace('*** no e')
        p = self.item2position(item)
        if p:
            # 2014/02/21: generate headddlick1/2 instead of icondclick1/2.
            event = None
            if g.doHook("headdclick1", c=c, p=p, event=event) is None:
                c.frame.tree.OnIconDoubleClick(p) # Call the base class method.
            g.doHook("headclick2", c=c, p=p, event=event)
        else:
            g.trace('*** no p')
        c.outerUpdate()
    #@+node:ekr.20110605121601.17898: *4* qtree.onItemExpanded
    def onItemExpanded(self, item):
        '''Handle and tree-expansion event.'''
        p = self.item2position(item)
        if p and not p.isExpanded():
            p.expand()
        self.treeWidget.setCurrentItem(item, 0,
                QtCore.QItemSelectionModel.SelectionFlags(3))
        self.c.outerUpdate()
    #@+node:ekr.20110605121601.17899: *4* qtree.onTreeSelect
    def onTreeSelect(self):
        '''Select the proper position when a tree node is selected.'''

        c = self.c
        item = self.getCurrentItem()
        p = self.item2position(item)
        if p:
            # Important: do not set lockouts here.
            # Only methods that actually generate events should set lockouts.
            self.select(p)
                # This is a call to LeoTree.select(!!)
                # Calls before/afterSelectHint.
        else:
            self.error('no p for item: %s' % item)
            self.error('itemdata[%s]'%item.data(0, 0x100))
        c.outerUpdate()
    #@+node:ekr.20110605121601.17900: *4* qtree.OnPopup & allies
    def OnPopup(self, p, event):
        """Handle right-clicks in the outline.

        This is *not* an event handler: it is called from other event handlers."""
        # Note: "headrclick" hooks handled by VNode callback routine.
        if event:
            c = self.c
            c.setLog()
            if not g.doHook("create-popup-menu", c=c, p=p, event=event):
                self.createPopupMenu(event)
            if not g.doHook("enable-popup-menu-items", c=c, p=p, event=event):
                self.enablePopupMenuItems(p, event)
            if not g.doHook("show-popup-menu", c=c, p=p, event=event):
                self.showPopupMenu(event)
        return "break"
    #@+node:ekr.20110605121601.17901: *5* qtree.OnPopupFocusLost
    #@+at
    # On Linux we must do something special to make the popup menu "unpost" if the
    # mouse is clicked elsewhere. So we have to catch the <FocusOut> event and
    # explicitly unpost. In order to process the <FocusOut> event, we need to be able
    # to find the reference to the popup window again, so this needs to be an
    # attribute of the tree object; hence, "self.popupMenu".
    # 
    # Aside: though Qt tries to be muli-platform, the interaction with different
    # window managers does cause small differences that will need to be compensated by
    # system specific application code. :-(
    #@@c
    # 20-SEP-2002 DTHEIN: This event handler is only needed for Linux.

    def OnPopupFocusLost(self, event=None):
        # self.popupMenu.unpost()
        pass
    #@+node:ekr.20110605121601.17902: *5* qtree.createPopupMenu
    def createPopupMenu(self, event):
        '''This might be a placeholder for plugins.  Or not :-)'''
    #@+node:ekr.20110605121601.17903: *5* qtree.enablePopupMenuItems
    def enablePopupMenuItems(self, p, event):
        """Enable and disable items in the popup menu."""
    #@+node:ekr.20110605121601.17904: *5* qtree.showPopupMenu
    def showPopupMenu(self, event):
        """Show a popup menu."""
    #@+node:ekr.20110605121601.17944: *3* qtree.Focus
    def getFocus(self):
        return g.app.gui.get_focus(self.c) # Bug fix: 2009/6/30

    findFocus = getFocus

    def setFocus(self):
        g.app.gui.set_focus(self.c, self.treeWidget)
    #@+node:ekr.20110605121601.18411: *3* qtree.getIcon & helper
    def getIcon(self, p):
        '''Return the proper icon for position p.'''
        p.v.iconVal = val = p.v.computeIcon()
        return self.getCompositeIconImage(p, val)
    #@+node:ekr.20110605121601.18412: *4* qtree.getCompositeIconImage
    def getCompositeIconImage(self, p, val):
        '''Get the icon at position p.'''
        trace = False and not g.unitTesting
        trace_cached = False
        userIcons = self.c.editCommands.getIconList(p)
        # don't take this shortcut - not theme aware, see getImageImage()
        # which is called below - TNB 20130313
        # if not userIcons:
        #     # if trace: g.trace('no userIcons')
        #     return self.getStatusIconImage(p)
        hash = [i['file'] for i in userIcons if i['where'] == 'beforeIcon']
        hash.append(str(val))
        hash.extend([i['file'] for i in userIcons if i['where'] == 'beforeHeadline'])
        hash = ':'.join(hash)
        if hash in g.app.gui.iconimages:
            icon = g.app.gui.iconimages[hash]
            if trace and trace_cached: g.trace('cached %s' % (icon))
            return icon
        images = [g.app.gui.getImageImage(i['file']) for i in userIcons
                 if i['where'] == 'beforeIcon']
        images.append(g.app.gui.getImageImage("box%02d.png" % val))
        images.extend([g.app.gui.getImageImage(i['file']) for i in userIcons
                      if i['where'] == 'beforeHeadline'])
        images = [z for z in images if z] # 2013/12/23: Remove missing images.
        if not images:
            return None
        hsep = self.c.config.getInt('tree-icon-separation') or 0
        width = sum([i.width() for i in images]) + hsep * (len(images)-1)
        height = max([i.height() for i in images])
        pix = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
        pix.fill(QtGui.QColor(0, 0, 0, 0).rgba()) # transparent fill, rgbA
        # .rgba() call required for Qt4.7, later versions work with straight color
        painter = QtGui.QPainter()
        if not painter.begin(pix):
            print("Failed to init. painter for icon")
            # don't return, the code still makes an icon for the cache
            # which stops this being called again and again
        x = 0
        for i in images:
            painter.drawPixmap(x, (height - i.height()) // 2, i)
            x += i.width() + hsep
        painter.end()
        icon = QtGui.QIcon(QtGui.QPixmap.fromImage(pix))
        g.app.gui.iconimages[hash] = icon
        if trace: g.trace('new %s' % (icon))
        return icon
    #@+node:ekr.20110605121601.18414: *3* qtree.Items
    #@+node:vitalije.20180305192504.1: *4* qtree.item2headline
    def item2headline(self, item):
        return self.item2vnode(item).h
    #@+node:vitalije.20180305192525.1: *4* qtree.item2position
    def item2position(self, item):
        inds = item.data(0, 0x100)
        i = inds[0]
        v = self.c.hiddenRootNode.children[i]
        p = leoNodes.Position(v, i)
        for i in inds[1:-1]:
            p.moveToNthChild(i)
        assert p.gnx == inds[-1], repr((inds, p.stack, p.h, g.callers(5)))
        return p
    #@+node:vitalije.20180305192537.1: *4* qtree.item2vnode
    def item2vnode(self, item):
        gnx = item.data(0, 0x100)[-1]
        return self.c.fileCommands.gnxDict[gnx]
    #@+node:vitalije.20180305192541.1: *4* qtree.vnode2items
    def vnode2items(self, v):
        return tuple(self.position2item(x, self.rootPosition) for x in v.positions())
    #@+node:vitalije.20180305192545.1: *4* qtree.isValidItem
    def isValidItem(self, item):
        return bool(self.item2position(item))
    #@+node:vitalije.20180305084130.1: *4* qtree.position2item
    def position2item(self, p, relativeTo=None):
        '''Returns item corresponding to thw position p.
           If tree doesn't show the whole Leo outline, but
           just one chapter or hoist, then relativeTo should
           be also given as a position of chapter root node,
           or position of hoist node.
           
           Function doesn't check items, but expects them to
           have accurate data.'''
        start = len(relativeTo.stack) + 1 if relativeTo else 0
        item = self.treeWidget.invisibleRootItem()
        for v, i in p.stack[start:]:
            item = item.child(i)
            if not item:
                return None
        return item.child(p.childIndex())
    #@+node:ekr.20110605121601.18418: *4* qtree.connectEditorWidget & helper
    def connectEditorWidget(self, e, item):
        if not e:
            return g.trace('can not happen: no e')
        # Hook up the widget.
        wrapper = self.getWrapper(e, item)

        def editingFinishedCallback(e=e, item=item, self=self, wrapper=wrapper):
            # g.trace(wrapper,g.callers(5))
            c = self.c
            w = self.treeWidget
            self.onHeadChanged(p=c.p, e=e)
            w.setCurrentItem(item)

        e.editingFinished.connect(editingFinishedCallback)
        return wrapper # 2011/02/12
    #@+node:vitalije.20180305190620.1: *4* qtree.contractPos & expandPos
    def contractPos(self, p):
        item = self.position2item(p, self.rootPosition)
        if item:
            self.treeWidget.blockSignals(True)
            item.setExpanded(False)
            self.treeWidget.blockSignals(False)

    def expandPos(self, p):
        item = self.position2item(p, self.rootPosition)
        if item:
            self.treeWidget.blockSignals(True)
            item.setExpanded(True)
            self.treeWidget.blockSignals(False)
    #@+node:ekr.20110605121601.18423: *4* qtree.getCurrentItem
    def getCurrentItem(self):
        w = self.treeWidget
        return w.currentItem()
    #@+node:ekr.20110605121601.18426: *4* qtree.getSelectedItems
    def getSelectedItems(self):
        w = self.treeWidget
        return w.selectedItems()
    #@+node:vitalije.20180305192859.1: *3* qtree Editor
    #@+node:ekr.20110605121601.18417: *4* qtree.closeEditorHelper
    def closeEditorHelper(self, e, item):
        'End editing of the underlying QLineEdit widget for the headline.' ''
        w = self.treeWidget
        if e:
            w.closeEditor(e, QtWidgets.QAbstractItemDelegate.NoHint)
            try:
                # work around https://bugs.launchpad.net/leo-editor/+bug/1041906
                # underlying C/C++ object has been deleted
                w.setItemWidget(item, 0, None)
                    # Make sure e is never referenced again.
                w.setCurrentItem(item)
            except RuntimeError:
                if 1: # Testing.
                    g.es_exception()
                else:
                    # Recover silently even if there is a problem.
                    pass
    #@+node:ekr.20110605121601.18420: *4* qtree.createTreeEditorForItem
    def createTreeEditorForItem(self, item):
        trace = False and not g.unitTesting
        w = self.treeWidget
        w.setCurrentItem(item) # Must do this first.
        if self.use_declutter:
            h = self.item2headline(item)
            item.setText(0, h)
        w.editItem(item)
        e = w.itemWidget(item, 0)
        e.setObjectName('headline')
        wrapper = self.connectEditorWidget(e, item)
        if trace: g.trace(e, wrapper)
        self.sizeTreeEditor(self.c, e)
        return e, wrapper
    #@+node:ekr.20110605121601.18422: *4* qtree.editLabelHelper
    def editLabelHelper(self, item, selectAll=False, selection=None):
        '''
        Help nativeTree.editLabel do gui-specific stuff.
        '''
        c, vc = self.c, self.c.vimCommands
        w = self.treeWidget
        w.setCurrentItem(item)
            # Must do this first.
            # This generates a call to onTreeSelect.
        w.editItem(item)
            # Generates focus-in event that tree doesn't report.
        e = w.itemWidget(item, 0) # A QLineEdit.
        if e:
            s = e.text(); len_s = len(s)
            if s == 'newHeadline': selectAll = True
            if selection:
                # pylint: disable=unpacking-non-sequence
                # Fix bug https://groups.google.com/d/msg/leo-editor/RAzVPihqmkI/-tgTQw0-LtwJ
                # Note: negative lengths are allowed.
                i, j, ins = selection
                if ins is None:
                    start, n = i, abs(i - j)
                    # This case doesn't happen for searches.
                elif ins == j:
                    start, n = i, j - i
                else:
                    start = start, n = j, i - j
                # g.trace('i',i,'j',j,'ins',ins,'-->start',start,'n',n)
            elif selectAll: start, n, ins = 0, len_s, len_s
            else: start, n, ins = len_s, 0, len_s
            e.setObjectName('headline')
            e.setSelection(start, n)
            # e.setCursorPosition(ins) # Does not work.
            e.setFocus()
            wrapper = self.connectEditorWidget(e, item) # Hook up the widget.
            if vc and c.vim_mode: #  and selectAll
                # For now, *always* enter insert mode.
                if vc.is_text_wrapper(wrapper):
                    vc.begin_insert_mode(w=wrapper)
                else:
                    g.trace('not a text widget!', wrapper)
        return e, wrapper
    #@+node:ekr.20110605121601.18427: *4* qtree.getTreeEditorForItem
    def getTreeEditorForItem(self, item):
        '''Return the edit widget if it exists.
        Do *not* create one if it does not exist.'''
        trace = False and not g.unitTesting
        w = self.treeWidget
        e = w.itemWidget(item, 0)
        if trace and e: g.trace(e.__class__.__name__)
        return e
    #@+node:ekr.20110605121601.18428: *4* qtree.getWrapper
    def getWrapper(self, e, item):
        '''Return headlineWrapper that wraps e (a QLineEdit).'''
        trace = False and not g.unitTesting
        c = self.c
        if e:
            wrapper = self.editWidgetsDict.get(e)
            if wrapper:
                pass # g.trace('old wrapper',e,wrapper)
            else:
                if item:
                    # 2011/02/12: item can be None.
                    wrapper = self.headlineWrapper(c, item, name='head', widget=e)
                    if trace: g.trace('new wrapper', e, wrapper)
                    self.editWidgetsDict[e] = wrapper
                else:
                    if trace: g.trace('no item and no wrapper',
                        e, self.editWidgetsDict)
            return wrapper
        else:
            g.trace('no e')
            return None
    #@+node:tbrown.20160406221505.1: *4* qtree.sizeTreeEditor
    @staticmethod
    def sizeTreeEditor(c, editor):
        """Size a QLineEdit in a tree headline so scrolling occurs"""
        # space available in tree widget
        space = c.frame.tree.treeWidget.size().width()
        # left hand edge of editor within tree widget
        used = editor.geometry().x() + 4  # + 4 for edit cursor
        # limit width to available space
        editor.resize(space - used, editor.size().height())
    #@+node:ekr.20110605121601.18433: *3* qtree.Scroll bars
    #@+node:ekr.20110605121601.18430: *4* qtree.scrollToItem
    def scrollToItem(self, item):
        w = self.treeWidget
        # g.trace(self.traceItem(item))
        hPos, vPos = self.getScroll()
        w.scrollToItem(item, w.EnsureVisible)
            # Fix #265: Erratic scrolling bug.
            # w.PositionAtCenter causes unwanted scrolling.
        self.setHScroll(0)
            # Necessary
    #@+node:ekr.20110605121601.18434: *4* qtree.getSCroll
    def getScroll(self):
        '''Return the hPos,vPos for the tree's scrollbars.'''
        w = self.treeWidget
        hScroll = w.horizontalScrollBar()
        vScroll = w.verticalScrollBar()
        hPos = hScroll.sliderPosition()
        vPos = vScroll.sliderPosition()
        return hPos, vPos
    #@+node:btheado.20111110215920.7164: *4* qtree.scrollDelegate
    def scrollDelegate(self, kind):
        '''Scroll a QTreeWidget up or down or right or left.
        kind is in ('down-line','down-page','up-line','up-page', 'right', 'left')
        '''
        c = self.c; w = self.treeWidget
        if kind in ('left', 'right'):
            hScroll = w.horizontalScrollBar()
            if kind == 'right':
                delta = hScroll.pageStep()
            else:
                delta = -hScroll.pageStep()
            hScroll.setValue(hScroll.value() + delta)
        else:
            vScroll = w.verticalScrollBar()
            h = w.size().height()
            lineSpacing = w.fontMetrics().lineSpacing()
            n = h / lineSpacing
            if kind == 'down-half-page': delta = n / 2
            elif kind == 'down-line': delta = 1
            elif kind == 'down-page': delta = n
            elif kind == 'up-half-page': delta = -n / 2
            elif kind == 'up-line': delta = -1
            elif kind == 'up-page': delta = -n
            else:
                delta = 0; g.trace('bad kind:', kind)
            val = vScroll.value()
            # g.trace(kind,n,h,lineSpacing,delta,val)
            vScroll.setValue(val + delta)
        c.treeWantsFocus()
    #@+node:ekr.20110605121601.18435: *4* qtree.setH/VScroll
    def setHScroll(self, hPos):
        w = self.treeWidget
        hScroll = w.horizontalScrollBar()
        hScroll.setValue(hPos)

    def setVScroll(self, vPos):
        # g.trace(vPos)
        w = self.treeWidget
        vScroll = w.verticalScrollBar()
        vScroll.setValue(vPos)
    #@+node:ekr.20110605121601.17905: *3* qtree.Selecting & editing
    #@+node:vitalije.20180305162949.1: *4* qtree.isOutsideHoist
    def isOutsideHoist(self, p):
        if self.rootPosition:
            rpos = self.rootPosition
            if len(rpos.stack) >= len(p.stack):
                return True
            it = (True for a, b in zip(rpos.stack, p.stack) if a[1] != b[1])
            for x in it:
                return True
        return False
    #@+node:ekr.20110605121601.17906: *4* qtree.afterSelectHint
    def afterSelectHint(self, p, old_p):
        if self.isOutsideHoist(p):
            g.trace('attempt to select position outside hoist')
            return
        item = self.position2item(p, self.rootPosition)
        tw = self.treeWidget
        tw.blockSignals(True)
        tw.setCurrentItem(item, 0, QtCore.QItemSelectionModel.SelectionFlags(3))
        tw.blockSignals(False)
        return
    #@+node:ekr.20110605121601.17907: *4* qtree.beforeSelectHint
    def beforeSelectHint(self, p, old_p):
        return
    #@+node:ekr.20110605121601.17908: *4* qtree.edit_widget
    def edit_widget(self, p):
        """Returns the edit widget for position p."""
        trace = False and not g.unitTesting
        verbose = False
        # if False and g.unitTesting:
            # ### Highly experimental: 10 unit tests fail.
            # return HeadWrapper(c=self.c, name='head', p=p)
        item = self.position2item(p, self.rootPosition)
        if item:
            e = self.getTreeEditorForItem(item)
            if e:
                # Create a wrapper widget for Leo's core.
                w = self.getWrapper(e, item)
                if trace: g.trace(w, p and p.h)
                return w
            else:
                # This is not an error
                # But warning: calling this method twice might not work!
                if trace and verbose: g.trace('no e for %s' % (p))
                return None
        else:
            if trace and verbose: self.error('no item for %s' % (p))
            return None
    #@+node:ekr.20110605121601.17909: *4* qtree.editLabel
    def editLabel(self, p, selectAll=False, selection=None):
        """Start editing p's headline."""
        trace = False and not g.unitTesting
        if self.busy():
            if trace: g.trace('busy')
            return
        c = self.c
        c.outerUpdate()
            # Do any scheduled redraw.
            # This won't do anything in the new redraw scheme.
        item = self.position2item(p, self.rootPosition)
        if item:
            if self.use_declutter:
                item.setText(0, self.item2headline(item))
            e, wrapper = self.editLabelHelper(item, selectAll, selection)
        else:
            e, wrapper = None, None
            self.error('no item for %s' % p)
        if trace: g.trace('p: %s e: %s' % (p and p.h, e))
        if e:
            self.sizeTreeEditor(c, e)
            # A nice hack: just set the focus request.
            c.requestedFocusWidget = e
        return e, wrapper
    #@+node:ekr.20110605121601.17911: *4* qtree.endEditLabel
    def endEditLabel(self):
        '''Override LeoTree.endEditLabel.

        End editing of the presently-selected headline.'''
        c = self.c; p = c.currentPosition()
        self.onHeadChanged(p)
    #@+node:ekr.20110605121601.17915: *4* qtree.getSelectedPositions
    def getSelectedPositions(self):
        items = self.getSelectedItems()
        pl = leoNodes.PosList(self.item2position(it) for it in items)
        return pl
    #@+node:ekr.20110605121601.17914: *4* qtree.setHeadline
    def setHeadline(self, p, s):
        '''Force the actual text of the headline widget to p.h.'''
        trace = False and not g.unitTesting
        # This is used by unit tests to force the headline and p into alignment.
        if not p:
            if trace: g.trace('*** no p')
            return
        # Don't do this here: the caller should do it.
        # p.setHeadString(s)
        e = self.edit_widget(p)
        if e:
            if trace: g.trace('e', s)
            e.setAllText(s)
        else:
            item = self.position2item(p, self.rootPosition)
            if item:
                if trace: g.trace('item', s)
                item.setText(0, s)
            else:
                if trace: g.trace('*** failed. no item for %s' % p.h)
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@@pagewidth 80
#@-leo

#@+leo-ver=5-thin
#@+node:vitalije.20190718140907.1: * @file ../plugins/qt_tree_incremental.py
import re
import time
import leo.core.leoGlobals as g
import leo.core.leoNodes as leoNodes
from leo.core.leoQt import QtCore, QtWidgets, QtGui
#@+others
#@+node:vitalije.20190715153539.1: ** drawing_items
def drawing_items(root):
    '''Returns a list of tuples (v, level) of all visible nodes.
       This is the faster version that uses only v nodes.
       
       root argument can be c.hiddenRootNode or any @chapter/hoist node.
    '''
    def it(v, lev):
        yield v, lev
        if v.isExpanded():
            for ch in v.children:
                yield from it(ch, lev + 1)
    visibles = []
    for ch in root.children:
        visibles.extend(it(ch,0))
    return visibles

def drawing_items2(c, root):
    '''Returns a list of tuples (p, level, expanded) of all visible nodes.
       
       root argument is the top visible position like c.rootPosition() or
       @chapter/hoist first child position.
    '''
    # root is a position
    p = root
    zlev = p.level()
    visibles = []
    while p:
        v = p.v
        exp = v.isExpanded() and bool([z for z in v.expandedPositions if z == p])
        visibles.append((p.copy(), p.level() - zlev, exp))
        p.moveToVisNext(c)
    return visibles

def drawing_items3(v):
    p = leoNodes.Position(None, 0)
    def inner_iter(v, j, stack):
        p.v = v
        p._childIndex = j
        p.stack = stack
        exp = v.isExpanded() and bool([z for z in v.expandedPositions if z == p])
        yield p, p.level(), exp
        if exp:
            stack = stack + [(v, j)]
            for i, ch in enumerate(v.children):
                yield from inner_iter(ch, i, stack)
    for i, ch in enumerate(v.children):
        yield from inner_iter(ch, i, [])
#@+node:vitalije.20190716124321.1: ** MyTreePainter
class MyTreePainter(QtWidgets.QWidget):
    '''The colaborator widget used by MyTree widget.
        
       This is the widget that paints itself by painting part of the QTreeWidget 
       on its own surface. QTreeWidget might contain several dummy nodes
       at the start if the first visible node is not at the top level.
       The number of this dummy nodes is in the SKIP ivar.
       
       This widget is also a parent to the editor (QLineEdit) and it
       can show or hide editor when the item is double-clicked.

       It also handles mouse clicks in the expand/contract icon.
       
       This class doesn't populate QTreeWidget, instead it just paints it
       as it is already prepopulated by MyTree widget.
    '''
    def __init__(self, c, mytree):
        QtWidgets.QWidget.__init__(self)
        self.mytree = mytree            # a MyTree instance
        self.qtree = mytree.qtree       # a QTreeWidget instance

        # editor for editing headlines
        self.editor = QtWidgets.QLineEdit("", self)
        self.editor.move(-32000,-32000)
        self.editor.returnPressed.connect(self.return_pressed)
        self.editor.editingFinished.connect(self.editing_finished)
        self._editing_node = None       # holds the v node whose headline is being edited

        self.setAutoFillBackground(True)

        # number of "dummy" nodes at the top of QTreeWidget that should not be painted
        self.SKIP = 0
        self.c = c

    #@+others
    #@+node:vitalije.20190717110058.1: *3* edit_item
    def edit_item(self, item):
        '''shows the editor at the correct position
           and gives it the focus.
           
           Also this method will set _editing_node to the v instance
           whose headline is being edited.
        '''
        e, w = self.editor, self.qtree

        r = w.visualItemRect(item) # find the coordinates of item
        x = r.x() + 58             # adjust x for icon box
        y = r.y() - self.y() - self.delta_y() # adjust y for dummy nodes
        e.move(x, y)     # move editor to correct position


        w = self.width()
        h = e.height()
        e.resize(w - x + 20, h)

        # remember which node is being edited
        p = item.data(0, 256)
        self._editing_node = p.v

        # set initial text, show and focus editor
        e.setText(p.h)
        e.show()
        e.setFocus()
    #@+node:vitalije.20190717110047.1: *3* editing_finished
    def editing_finished(self):
        # hide editor
        self.editor.move(-32000, -32000)
        self.editor.hide()

        # forget about editing node
        self._editing_node = None
        print('editing finished')
    #@+node:vitalije.20190717110053.1: *3* return_pressed
    def return_pressed(self):
        '''Idealy this should call c.frame.tree.onHeadChanged,
           but right now onHeadChanged assumes that the editor
           was the QTreeWidget line editor.
        '''
        # update v.h
        v = self._editing_node
        old_head = v.h
        v.h = self.editor.text()

        # TODO: make this change undoable
        # TODO: call hooks

        # redraw the tree
        self.mytree.refresh_visibles()
        self.update()
        print('return pressed')
    #@+node:vitalije.20190717110104.1: *3* delta_y
    def delta_y(self):
        '''This method calculates y coordinate of the first visible node,
           skipping all (if any) dummy nodes at the top of the QTreeWidget.
        '''
        item = self.qtree.topLevelItem(0)
        if item:
            for i in range(self.SKIP):
                item = item.child(0)
            return self.qtree.visualItemRect(item).y()
        else:
            return 0
    #@+node:vitalije.20190717110109.1: *3* mev2item
    def mev2item(self, mev):
        '''This method analyizes mouse event and returns a bunch of the following form:
            {
                item,    # the item at the given position or None 
                in_box,  # True if the user clicked at the expand/contract icon
                in_icon, # True if the user clicked at the node icon
                in_text, # True if the user clicked at the headline text
            }
           TODO: the magic numbers used here (-20, 8, 64) are empirically discovered and
                 most likely they are platform, version and theme dependent. We need a way
                 to calculate this values accurately regardless of the platform and theme.
        '''
        w = self.qtree
        y = self.delta_y() + mev.y() + self.y()
        x = mev.x()
        item = w.itemAt(x, y)
        if item:
            r = w.visualItemRect(item)
            dx = x - r.x()
            return g.bunch(item=item, in_box=(-20 < dx < 8), in_icon=(8 <= dx < 64), in_text=(dx >= 64))
        return g.bunch(item=None, in_box=False, in_icon=False, in_text=False)
    #@+node:vitalije.20190717110114.1: *3* mousePressEvent
    def mousePressEvent(self, mev):
        # TODO: call hooks and other handlers
        if mev.button() == 1:
            z = self.mev2item(mev)
            if z.item:
                p = z.item.data(0, 256)
                if z.in_box:
                    # toggle expanded state
                    if z.item.isExpanded():
                        p.contract()
                    else:
                        p.expand()
                    self.c.selectPosition(p)
                    self.mytree.refresh_visibles()
                    self.update()
                    return

                # otherwise just select node
                self.qtree.setCurrentItem(z.item)
                self.c.setCurrentPosition(p)
                self.update()
    #@+node:vitalije.20190717110119.1: *3* mouseDoubleClickEvent
    def mouseDoubleClickEvent(self, mev):
        # start editing headline if the click was in a node
        if mev.button() == 1:
            z = self.mev2item(mev)
            if z.item:
                self.edit_item(z.item)
    #@-others

    def paintEvent(self, ev):
        painter = QtGui.QPainter(self)

        # QScrollArea will move this widget when vertical scroll bar is changed
        # however, we are painting always the tree at the origin and only the items
        # that are inside tree are changed according to the scroll bar position
        # that is why we are reseting scrolling position before painting
        painter.translate(0, -self.y())
        self.qtree.render(painter, QtCore.QPoint(), QtGui.QRegion(0, self.delta_y(), 3000, 3000))
        painter.end()
#@+node:vitalije.20190715153547.1: ** MyTree
class MyTree(QtWidgets.QScrollArea):
    '''This class aimes to be a substitute for QTreeWidget class.
       
       Internally it uses QTreeWidget to hold nodes currently visible
       on screen. This class populates QTreeWidget with the items that
       could fit in one page. On scroll change this QTreeWidget is
       repopulated with the new segment of visible nodes.
       
       If the first visible node is at the level > 0, dummy nodes are
       added to fill all levels from 0..level. This dummy nodes should
       not be painted and that is the job of MyTreePainter class.
    '''
    def __init__(self, c, parent, root):
        QtWidgets.QScrollArea.__init__(self, parent)
        self.qtree = QtWidgets.QTreeWidget()
        self.root = root
        self.busy = False
        #self.root_pos = leoNodes.Position(root.children[0], 0)
        self.gnx_decluttered = {} # keeps cache of decluttering nodes
        self.declutter_patterns = None
        self.c = c

        # the following two ivars allows to skip expensive operation
        # drawing_items(self.root)
        # for tree redraw after scrolling there is no need to recompute
        # list of visible items.
        # Only on expand, contract and other commands that change the outline
        # we have to recalculate this list
        self._visibles_version = 0
        self._last_visibles_version = -1

        # adjust qtree to look like Leo Tree
        self.qtree.setObjectName('treeWidget')
        self.qtree.setHeaderHidden(True)

        # tree_painter does the real painting
        self.tree_painter = MyTreePainter(c, self)
        self.setWidget(self.tree_painter)

        # populate tree little bit later
        QtCore.QTimer.singleShot(100, lambda:self.populate_tree2(0))

        # handle vertical scrolling
        self.verticalScrollBar().valueChanged.connect(self.vsb_change)
        #self.add_slots()
    def resizeEvent(self, ev):
        if not self.busy:
            y = self.verticalScrollBar().value()
            self.populate_tree2(y)

    def vsb_change(self, y):
        '''when vertical scrollbar has changed'''
        if self.busy: return
        self.populate_tree2(y)
        self.update()

    def refresh_visibles(self):
        '''Request re-populating tree after any change in the visible outline.'''
        self._visibles_version += 1
        self.populate_tree2(self.verticalScrollBar().value())

    def wheelEvent(self, we):
        '''handles mouse-wheel scrolling'''
        dy = we.angleDelta().y() // 30
        vsb = self.verticalScrollBar()
        vsb.setValue(vsb.value() - dy)
    #@+others
    #@+node:vitalije.20190715153552.1: *3* declutter_node & helpers
    # this is copied from LeoQtTree and adjusted to use v nodes instead of positions
    def declutter_node(self, c, v, item):
        """declutter_node - change the appearance of a node

        :param commander c: commander containing node
        :param position p: position of node
        :param QWidgetItem item: tree node widget item
        """
        #@+others
        #@+node:vitalije.20190715153552.2: *4* init declutter_patterns
        if self.declutter_patterns is None:
            self.declutter_patterns = []
            warned = False
            lines = c.config.getData("tree-declutter-patterns")
            for line in lines:
                try:
                    cmd, arg = line.split(None, 1)
                except ValueError:
                    # Allow empty arg, and guard against user errors.
                    cmd = line.strip()
                    arg = ''
                if cmd.startswith('#'):
                    pass
                elif cmd == 'RULE':
                    self.declutter_patterns.append((re.compile(arg), []))
                else:
                    if self.declutter_patterns:
                        self.declutter_patterns[-1][1].append((cmd, arg))
                    elif not warned:
                        warned = True
                        g.log('Declutter patterns must start with RULE*',
                            color='error')
        #@+node:vitalije.20190715153552.3: *4* get_icon_list
        def get_icon_list(v):
            """Return list of icons for position p, call setIconList to apply changes"""
            fromVnode = []
            if hasattr(v, 'unknownAttributes'):
                fromVnode = [dict(i) for i in v.u.get('icons', [])]
                for i in fromVnode: i['on'] = 'VNode'
            return fromVnode
        #@+node:vitalije.20190715153552.4: *4* declutter_replace
        def declutter_replace(arg, cmd, item, m, pattern, text):
            '''
            Execute cmd and return True if cmd is any replace command.
            '''
            if cmd == 'REPLACE':
                text = pattern.sub(arg, text)
                item.setText(0, text)
                return True
            if cmd == 'REPLACE-HEAD':
                s = text[:m.start()]
                item.setText(0, s.rstrip())
                return True
            if cmd == 'REPLACE-TAIL':
                s = text[m.end():]
                item.setText(0, s.lstrip())
                return True
            if cmd == 'REPLACE-REST':
                s = text[:m.start] + text[m.end():]
                item.setText(0, s.strip())
                return True
            return False
            
        #@+node:vitalije.20190715153552.5: *4* declutter_style
        def declutter_style(arg, c, cmd, item, new_icons):
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
        #@+node:vitalije.20190715153552.6: *4* dHash
        def dHash(d):
            """Hash a dictionary"""
            return ''.join(['%s%s' % (str(k), str(d[k])) for k in sorted(d)])
        #@-others
        text = str(item.text(0))
        new_icons = []
        for pattern, cmds in self.declutter_patterns:
            for func in (pattern.match, pattern.search):
                m = func(text)
                if m:
                    for cmd, arg in cmds:
                        if declutter_replace(arg, cmd, item, m, pattern, text):
                            pass
                        else:
                            declutter_style(arg, c, cmd, item, new_icons)
                    break # Don't try pattern.search if pattern.match succeeds.
        com = c.editCommands
        allIcons = get_icon_list(v)
        icons = [i for i in allIcons if 'visualIcon' not in i]
        if len(allIcons) != len(icons) or new_icons:
            for icon in new_icons:
                com.appendImageDictToList(
                    icons, icon, 2, on='vnode', visualIcon='1'
                )
            v.u['icons'] = icons
    #@+node:vitalije.20190715153924.1: *3* qtree.getCompositeIconImage
    # this is copied from LeoQtTree and adjusted to use v nodes instead of positions
    def getCompositeIconImage(self, v, val):
        '''Get the icon at position p.'''
        #@+others
        #@+node:vitalije.20190715153924.2: *4* get_icon_list
        def get_icon_list(v):
            """Return list of icons for position p, call setIconList to apply changes"""
            fromVnode = []
            if hasattr(v, 'unknownAttributes'):
                fromVnode = [dict(i) for i in v.u.get('icons', [])]
                for i in fromVnode: i['on'] = 'VNode'
            return fromVnode
        #@-others
        userIcons = get_icon_list(v)
        # Don't take this shortcut - not theme aware, see getImageImage()
        # which is called below - TNB 20130313
            # if not userIcons:
            #     return self.getStatusIconImage(p)
        hash = [i['file'] for i in userIcons if i['where'] == 'beforeIcon']
        hash.append(str(val))
        hash.extend([i['file'] for i in userIcons if i['where'] == 'beforeHeadline'])
        hash = ':'.join(hash)
        if hash in g.app.gui.iconimages:
            icon = g.app.gui.iconimages[hash]
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
        return icon
    #@+node:vitalije.20190716110136.1: *3* get_visibles
    def get_visibles(self):
        '''returns the list of pairs (v, level) of all visible nodes.
           Uses faster iterator which uses only v nodes.
        '''
        if self._last_visibles_version == self._visibles_version:
            # only recalculate when necessary
            return self.visibles
        self._last_visibles_version = self._visibles_version

        t1 = time.process_time_ns() # some profiling ...

        self.visibles = visibles = drawing_items(self.root)

        tvis = (time.process_time_ns() - t1) * 1e-6
        print("visibles recalculated in %.2fms"%tvis) # reports time

        return visibles

    def get_visibles2(self):
        '''returns the list of tuples (p, level, expanded) of all visible nodes.
           Uses slower iterator based on Position class. This iterator
           although slower, better suits Leo and allows easier integration.
        '''
        if self._last_visibles_version == self._visibles_version:
            # only recalculate when necessary
            return self.visibles
        self._last_visibles_version = self._visibles_version

        t1 = time.process_time_ns() # some profiling...
        self.visibles = visibles = drawing_items2(self.c, self.root_pos.copy())
        tvis = (time.process_time_ns() - t1) * 1e-6
        print("visibles recalculated in %.2fms"%tvis) # report time

        return visibles

    def get_visibles3(self):
        '''returns the list of tuples (p, level, expanded) of all visible nodes.
           Uses fast position iterator. Using positions instead of vnodes better
           suits Leo and allows easier integration.
        '''
        if self._last_visibles_version == self._visibles_version:
            # only recalculate when necessary
            return self.visibles
        self._last_visibles_version = self._visibles_version

        t1 = time.process_time_ns() # some profiling...
        def mkcopy(p, lev, exp):
            return p.copy(), lev, exp
        self.visibles = visibles = [(p.copy(), lev, exp) for p, lev, exp in drawing_items3(self.root)]
        tvis = (time.process_time_ns() - t1) * 1e-6
        print("visibles recalculated in %.2fms"%tvis) # report time

        return visibles
    #@+node:vitalije.20190716132301.1: *3* row_height
    def row_height(self):
        '''determines row height in QTreeWidget using current theme.
           If the tree already contains at least one node returns
           the height of the first node;
           otherwise it adds one top level item, meassures it, and
           delete it again.
           
           This calculation is done only once.
        '''
        if hasattr(self, '_HR'):
            return self._HR
        w = self.qtree
        item = w.topLevelItem(0)
        if item:
            r = w.visualItemRect(item)
        else:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, 'dummy')
            icon = self.getCompositeIconImage(self.root, 9)
            if icon:
                item.setIcon(0, icon)
            w.addTopLevelItem(item)
            r = w.visualItemRect(item)
            w.takeTopLevelItem(0)

        # cache result for the future use
        self._HR = r.height()
        return self._HR
    #@+node:vitalije.20190716132246.1: *3* populate_tree2
    def populate_tree2(self, skip):
        '''Populates qtree widget with the items that can fit on one page,
           skipping first skip visible nodes.
        '''
        t1 = time.process_time_ns()
        w = self.qtree
        w.clear()
        w.resize(3000,3000)
        c = self.c
        #@+others
        #@+node:vitalije.20190716193504.1: *4* syncitem
        def syncitem(p, item):
            '''synchronizes data in item with the data from the given position p'''
            v = p.v
            v.iconVal = v.computeIcon()
            item.setText(0, v.h)
            vh, vhdc = self.gnx_decluttered.get(v.fileIndex, (None, None))
            if v.h != vh:
                # headline changed, so we need to declutter this node again
                self.declutter_node(c, v, item)
                self.gnx_decluttered[v.fileIndex] = v.h, item.text(0)
            else:
                # reuse cached decluttered headline
                item.setText(0, vhdc)

            item.setData(0, 256, p)

            icon = self.getCompositeIconImage(v, v.iconVal)
            if icon:
                item.setIcon(0, icon)
        #@+node:vitalije.20190716193509.1: *4* mki
        def mki(p):
            '''makes an item for the given position p'''
            item = QtWidgets.QTreeWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            syncitem(p, item)
            return item
        #@+node:vitalije.20190716193514.1: *4* dummy
        def dummy():
            '''makes a dummy item to fill necessary hierarchy at the top'''
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, 'dummy')
            return item
        #@+node:vitalije.20190717122514.1: *4* setPlusMinusIndicator
        def setPlusMinusIndicator(v, item):
            # adjust plus/minus box - indicator
            if v.children:
                a = QtWidgets.QTreeWidgetItem.ShowIndicator
            else:
                a = QtWidgets.QTreeWidgetItem.DontShowIndicator
            item.setChildIndicatorPolicy(a)
        #@+node:vitalije.20190717122618.1: *4* addItem
        def addItem(stack, item):
            if stack:
                # nitem is a child of the last item on stack
                stack[-1].addChild(item)
            else:
                # stack is empty so nitem is a topLevelItem
                w.addTopLevelItem(item)

            stack.append(item)
        #@+node:vitalije.20190717122958.1: *4* addDummies
        def addDummies(visibles, stack):
            lev0 = visibles[0][1] # at what level starts this page?
            while len(stack) < lev0:
                # fill the stack with dummy nodes
                nitem = dummy()
                if stack:
                    stack[-1].addChild(nitem)
                else:
                    w.addTopLevelItem(nitem)
                nitem.setExpanded(True)
                stack.append(nitem)

            # inform the tree_painter that we have lev0 dummy nodes
            self.tree_painter.SKIP = lev0
        #@+node:vitalije.20190717123540.1: *4* prepareForDrawing
        def prepareForDrawing(skip, count, stack):
            visibles = self.get_visibles3()
            total = len(visibles)
            skip = min(skip, total - 1)
            if skip < 0: return skip, visibles, 0

            visibles = visibles[skip:skip+count] # show just one page of visible nodes
            addDummies(visibles, stack)

            return skip, visibles, total
        #@-others
        # how many nodes will fit on a single page
        HR = self.row_height()
        count = self.viewport().height() // HR
        count = max(1, count) # ensure at least one visible node

        stack = [] # to hold the chain of ancestor items
        skip, visibles, total = prepareForDrawing(skip, count, stack)
        if skip < 0: return # there are no visible nodes !!! This should never be the case.

        sel_p = self.c.p # position that should be set as currentItem

        for p, lev, exp in visibles:
            v = p.v
            stack = stack[:lev]
            nitem = mki(p)

            setPlusMinusIndicator(v, nitem)
            addItem(stack, nitem)
            nitem.setExpanded(exp) # this has to be done after adding item to tree

            if sel_p == p:
                w.setCurrentItem(nitem)


        maxW = w.sizeHintForColumn(0)
        maxW = max(self.viewport().width(), maxW)
        minH = max(HR * total, self.viewport().height())
        self.busy = True
        self.tree_painter.resize(maxW, minH)
        self.update_scroll_bar(0, max(0, total - count), skip)
        self.busy = False
        tdraw = (time.process_time_ns() - t1) * 1e-6
        print('Drawn in: %.2fms'%tdraw)
    #@+node:vitalije.20190716101303.1: *3* update_scroll_bar
    def update_scroll_bar(self, vsb_min, vsb_max, vsb_val):
        vsb = self.verticalScrollBar()
        if vsb.minimum() != vsb_min:
            vsb.setMinimum(vsb_min)
        if vsb.maximum() != vsb_max:
            vsb.setMaximum(vsb_max)
        if vsb.value() != vsb_val:
            vsb.setValue(vsb_val)
    #@+node:vitalije.20190718143915.1: *3* slots
    #@+at
    #   TODO: the following slots are connected by LeoQtTree but they are never fired yet
    #@@c
    itemDoubleClicked = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem, name='itemDoubleClicked')
    itemClicked = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem, name='itemClicked')
    itemCollapsed = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem, name='itemCollapsed')
    itemExpanded = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem, name='itemExpanded')
    itemSelectionChanged = QtCore.pyqtSignal(name='itemSelectionChanged')
    #@+node:vitalije.20190718142831.1: *3* deletates...
    #@+at
    # methods ='''
    # collapseItem
    # currentItem
    # expandItem
    # itemWidget
    # setCurrentItem
    # setDragEnabled
    # setHeaderHidden
    # setIconSize
    # setSelectionBehavior
    # setSelectionMode
    # '''.strip().split('\n')
    # res = []
    # for m in methods:
    #     res.append('def %s(self, *args):'%m)
    #     res.append('    return self.qtree.%s(*args)'%m)
    # start, sep, rest = p.b.partition('@c\n')
    # res.insert(0, start + sep)
    # p.b = '\n'.join(res)
    #@@c

    def collapseItem(self, *args):
        return self.qtree.collapseItem(*args)
    def currentItem(self, *args):
        return self.qtree.currentItem(*args)
    def expandItem(self, *args):
        return self.qtree.expandItem(*args)
    def itemWidget(self, *args):
        return self.qtree.itemWidget(*args)
    def setCurrentItem(self, *args):
        return self.qtree.setCurrentItem(*args)
    def setDragEnabled(self, *args):
        return self.qtree.setDragEnabled(*args)
    def setHeaderHidden(self, *args):
        return self.qtree.setHeaderHidden(*args)
    def setIconSize(self, *args):
        return self.qtree.setIconSize(*args)
    def setSelectionBehavior(self, *args):
        return self.qtree.setSelectionBehavior(*args)
    def setSelectionMode(self, *args):
        return self.qtree.setSelectionMode(*args)
    #@+node:vitalije.20190718150601.1: *3* set_style
    def set_style(self):
        style = self.c.styleSheetManager.get_master_widget().styleSheet()
        self.setStyleSheet(style)
        self.qtree.setStyleSheet(style)
    #@-others
#@-others
#@-leo

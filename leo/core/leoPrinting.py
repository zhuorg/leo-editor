#@+leo-ver=5-thin
#@+node:ekr.20150419124739.1: * @file leoPrinting.py
"""
Support the commands in Leo's File:Print menu.
Adapted from printing plugin.
"""
import leo.core.leoGlobals as g
from leo.core.leoQt import printsupport, QtGui
#@+others
#@+node:ekr.20200502185008.1: ** commands: leoPrinting.py
#@+node:ekr.20200502185008.2: *3* 'preview-body'
@g.command('preview-body')
def preview_body(event):
    """Preview the body of the selected node."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_body(event)

#@+node:ekr.20200502185008.3: *3* 'preview-html'
@g.command('preview-html')
def preview_html(event):
    """
    Preview the body of the selected text as html. The body must be valid
    html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_html(event)

#@+node:ekr.20200502185008.4: *3* 'preview-expanded-body'
@g.command('preview-expanded-body')
def preview_expanded_body(event):
    """Preview the selected node's body, expanded"""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_expanded_body(event)

#@+node:ekr.20200502185008.5: *3* 'preview-expanded-html'
@g.command('preview-expanded-html')
def preview_expanded_html(event):
    """
    Preview all the expanded bodies of the selected node as html. The
    expanded text must be valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_expanded_html(event)

#@+node:ekr.20200502185008.6: *3* 'preview-marked-bodies'
@g.command('preview-marked-bodies')
def preview_marked_bodies(event):
    """Preview the bodies of the marked nodes."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_marked_bodies(event)

#@+node:ekr.20200502185008.7: *3* 'preview-marked-html'
@g.command('preview-marked-html')
def preview_marked_html(event):
    """
    Preview the concatenated bodies of the marked nodes. The concatenated
    bodies must be valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_marked_html(event)

#@+node:ekr.20200502185008.8: *3* 'preview-marked-nodes'
@g.command('preview-marked-nodes')
def preview_marked_nodes(event):
    """Preview the marked nodes."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_marked_nodes(event)

#@+node:ekr.20200502185008.9: *3* 'preview-node'
@g.command('preview-node')
def preview_node(event):
    """Preview the selected node."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_node(event)

#@+node:ekr.20200502185008.10: *3* 'preview-tree-bodies'
@g.command('preview-tree-bodies')
def preview_tree_bodies(event):
    """Preview the bodies in the selected tree."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_tree_bodies(event)

#@+node:ekr.20200502185008.11: *3* 'preview-tree-nodes'
@g.command('preview-tree-nodes')
def preview_tree_nodes(event):
    """Preview the entire tree."""
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_tree_nodes(event)

#@+node:ekr.20200502185008.12: *3* 'preview-tree-html'
@g.command('preview-tree-html')
def preview_tree_html(event):
    """
    Preview all the bodies of the selected node as html. The concatenated
    bodies must valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.preview_tree_html(event)

#@+node:ekr.20200502185008.13: *3* 'print-body'
@g.command('print-body')
def print_body(event):
    """Print the selected node's body"""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_body(event)

#@+node:ekr.20200502185008.14: *3* 'print-html'
@g.command('print-html')
def print_html(event):
    """
    Print the body of the selected text as html. The body must be valid
    html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.print_html(event)

#@+node:ekr.20200502185008.15: *3* 'print-expanded-body'
@g.command('print-expanded-body')
def print_expanded_body(event):
    """Print the selected node's body, expanded"""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_expanded_body(event)

#@+node:ekr.20200502185008.16: *3* 'print-expanded-html'
@g.command('print-expanded-html')
def print_expanded_html(event):
    """
    Print all the expanded bodies of the selected node as html. The
    expanded text must be valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.print_expanded_html(event)

#@+node:ekr.20200502185008.17: *3* 'print-marked-bodies'
@g.command('print-marked-bodies')
def print_marked_bodies(event):
    """Print the body text of marked nodes."""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_marked_bodies(event)

#@+node:ekr.20200502185008.18: *3* 'print-marked-html'
@g.command('print-marked-html')
def print_marked_html(event):
    """
    Print the concatenated bodies of the marked nodes. The concatenated
    bodies must be valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.print_marked_html(event)

#@+node:ekr.20200502185008.19: *3* 'print-marked-nodes'
@g.command('print-marked-nodes')
def print_marked_nodes(event):
    """Print all the marked nodes"""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_marked_nodes(event)

#@+node:ekr.20200502185008.20: *3* 'print-node'
@g.command('print-node')
def print_node(event):
    """Print the selected node """
    c = event.get('c')
    if not c:
        return
    c.printingController.print_node(event)

#@+node:ekr.20200502185008.21: *3* 'print-tree-bodies'
@g.command('print-tree-bodies')
def print_tree_bodies(event):
    """Print all the bodies in the selected tree."""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_tree_bodies(event)

#@+node:ekr.20200502185008.22: *3* 'print-tree-html'
@g.command('print-tree-html')
def print_tree_html(event):
    """
    Print all the bodies of the selected node as html. The concatenated
    bodies must valid html, including <html> and <body> elements.
    """
    c = event.get('c')
    if not c:
        return
    c.printingController.print_tree_html(event)

#@+node:ekr.20200502185008.23: *3* 'print-tree-nodes'
@g.command('print-tree-nodes')
def print_tree_nodes(event):
    """Print all the nodes of the selected tree."""
    c = event.get('c')
    if not c:
        return
    c.printingController.print_tree_nodes(event)

#@+node:ekr.20150420120520.1: ** class PrintingController
class PrintingController:
    """A class supporting the commands in Leo's File:Print menu."""
    #@+others
    #@+node:ekr.20150419124739.6: *3* pr.__init__ & helpers
    def __init__(self, c):
        """Ctor for PrintingController class."""
        self.c = c
        self.reload_settings()

    def reload_settings(self):
        c = self.c
        self.font_size = c.config.getString('printing-font-size') or '12'
        self.font_family = c.config.getString(
            'printing-font-family') or 'DejaVu Sans Mono'
        self.stylesheet = self.construct_stylesheet()

    reloadSettings = reload_settings
    #@+node:ekr.20150419124739.8: *4* pr.construct stylesheet
    def construct_stylesheet(self):
        """Return the Qt stylesheet to be used for printing."""
        family, size = self.font_family, self.font_size
        table = (
            # Clearer w/o f-strings.
            f"h1 {{font-family: {family}}}",
            f"pre {{font-family: {family}; font-size: {size}px}}",
        )
        return '\n'.join(table)
    #@+node:ekr.20150420072955.1: *3* pr.Doc constructors
    #@+node:ekr.20150419124739.11: *4* pr.complex document
    def complex_document(self, nodes, heads=False):
        """Create a complex document."""
        doc = QtGui.QTextDocument()
        doc.setDefaultStyleSheet(self.stylesheet)
        contents = ''
        for n in nodes:
            if heads:
                contents += f"<h1>{self.sanitize_html(n.h)}</h1>\n"
            contents += f"<pre>{self.sanitize_html(n.b)}</pre>\n"
        doc.setHtml(contents)
        return doc
    #@+node:ekr.20150419124739.9: *4* pr.document
    def document(self, text, head=None):
        """Create a Qt document."""
        doc = QtGui.QTextDocument()
        doc.setDefaultStyleSheet(self.stylesheet)
        text = self.sanitize_html(text)
        if head:
            head = self.sanitize_html(head)
            contents = f"<h1>{head}</h1>\n<pre>{text}</pre>"
        else:
            contents = f"<pre>{text}<pre>"
        doc.setHtml(contents)
        return doc
    #@+node:ekr.20150419124739.10: *4* pr.html_document
    def html_document(self, text):
        """Create an HTML document."""
        doc = QtGui.QTextDocument()
        doc.setDefaultStyleSheet(self.stylesheet)
        doc.setHtml(text)
        return doc
    #@+node:ekr.20150420073201.1: *3* pr.Helpers
    #@+node:peckj.20150421084046.1: *4* pr.expand
    def expand(self, p):
        """Return the entire script at node p."""
        return p.script
    #@+node:ekr.20150419124739.15: *4* pr.getBodies
    def getBodies(self, p):
        """Return a concatenated version of the tree at p"""
        return '\n'.join([p2.b for p2 in p.self_and_subtree(copy=False)])
    #@+node:ekr.20150420085602.1: *4* pr.getNodes
    def getNodes(self, p):
        """Return the entire script at node p."""
        result = [p.b]
        for p in p.subtree():
            result.extend(['', f"Node: {p.h}", ''])
            result.append(p.b)
        return '\n'.join(result)
    #@+node:ekr.20150419124739.14: *4* pr.sanitize html
    def sanitize_html(self, html):
        """Generate html escapes."""
        return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    #@+node:ekr.20150420081215.1: *3* pr.Preview
    #@+node:ekr.20150419124739.21: *4* pr.preview_body
    def preview_body(self, event=None):
        """Preview the body of the selected node."""
        doc = self.document(self.c.p.b)
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.19: *4* pr.preview_html
    def preview_html(self, event=None):
        """
        Preview the body of the selected text as html. The body must be valid
        html, including <html> and <body> elements.
        """
        doc = self.html_document(self.c.p.b)
        self.preview_doc(doc)
    #@+node:peckj.20150421084706.1: *4* pr.preview_expanded_body
    def preview_expanded_body(self, event=None):
        """Preview the selected node's body, expanded"""
        doc = self.document(self.expand(self.c.p))
        self.preview_doc(doc)
    #@+node:peckj.20150421084719.1: *4* pr.preview_expanded_html
    def preview_expanded_html(self, event=None):
        """
        Preview all the expanded bodies of the selected node as html. The
        expanded text must be valid html, including <html> and <body> elements.
        """
        doc = self.html_document(self.expand(self.c.p))
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.31: *4* pr.preview_marked_bodies
    def preview_marked_bodies(self, event=None):
        """Preview the bodies of the marked nodes."""
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        doc = self.complex_document(nodes)
        self.preview_doc(doc)
    #@+node:ekr.20150420081906.1: *4* pr.preview_marked_html
    def preview_marked_html(self, event=None):
        """
        Preview the concatenated bodies of the marked nodes. The concatenated
        bodies must be valid html, including <html> and <body> elements.
        """
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        s = '\n'.join([z.b for z in nodes])
        doc = self.html_document(s)
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.33: *4* pr.preview_marked_nodes
    def preview_marked_nodes(self, event=None):
        """Preview the marked nodes."""
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        doc = self.complex_document(nodes, heads=True)
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.23: *4* pr.preview_node
    def preview_node(self, event=None):
        """Preview the selected node."""
        p = self.c.p
        doc = self.document(p.b, head=p.h)
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.26: *4* pr.preview_tree_bodies
    def preview_tree_bodies(self, event=None):
        """Preview the bodies in the selected tree."""
        doc = self.document(self.getBodies(self.c.p))
        self.preview_doc(doc)
    #@+node:ekr.20150419124739.28: *4* pr.preview_tree_nodes
    def preview_tree_nodes(self, event=None):
        """Preview the entire tree."""
        p = self.c.p
        doc = self.document(self.getNodes(p), head=p.h)
        self.preview_doc(doc)
    #@+node:ekr.20150420081923.1: *4* pr_preview_tree_html
    def preview_tree_html(self, event=None):
        """
        Preview all the bodies of the selected node as html. The concatenated
        bodies must valid html, including <html> and <body> elements.
        """
        doc = self.html_document(self.getBodies(self.c.p))
        self.preview_doc(doc)
    #@+node:ekr.20150420073128.1: *3* pr.Print
    #@+node:ekr.20150419124739.20: *4* pr.print_body
    def print_body(self, event=None):
        """Print the selected node's body"""
        doc = self.document(self.c.p.b)
        self.print_doc(doc)
    #@+node:ekr.20150419124739.18: *4* pr.print_html
    def print_html(self, event=None):
        """
        Print the body of the selected text as html. The body must be valid
        html, including <html> and <body> elements.
        """
        doc = self.html_document(self.c.p.b)
        self.print_doc(doc)
    #@+node:peckj.20150421084548.1: *4* pr.print_expanded_body
    def print_expanded_body(self, event=None):
        """Print the selected node's body, expanded"""
        doc = self.document(self.expand(self.c.p))
        self.print_doc(doc)
    #@+node:peckj.20150421084636.1: *4* pr.print_expanded_html
    def print_expanded_html(self, event=None):
        """
        Print all the expanded bodies of the selected node as html. The
        expanded text must be valid html, including <html> and <body> elements.
        """
        doc = self.html_document(self.expand(self.c.p))
        self.print_doc(doc)
    #@+node:ekr.20150419124739.30: *4* pr.print_marked_bodies
    def print_marked_bodies(self, event=None):
        """Print the body text of marked nodes."""
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        doc = self.complex_document(nodes)
        self.print_doc(doc)
    #@+node:ekr.20150420085054.1: *4* pr.print_marked_html
    def print_marked_html(self, event=None):
        """
        Print the concatenated bodies of the marked nodes. The concatenated
        bodies must be valid html, including <html> and <body> elements.
        """
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        s = '\n'.join([z.b for z in nodes])
        doc = self.html_document(s)
        self.print_doc(doc)
    #@+node:ekr.20150419124739.32: *4* pr.print_marked_nodes
    def print_marked_nodes(self, event=None):
        """Print all the marked nodes"""
        nodes = [p.v for p in self.c.all_positions() if p.isMarked()]
        doc = self.complex_document(nodes, heads=True)
        self.print_doc(doc)
    #@+node:ekr.20150419124739.22: *4* pr.print_node
    def print_node(self, event=None):
        """Print the selected node """
        doc = self.document(self.c.p.b, head=self.c.p.h)
        self.print_doc(doc)
    #@+node:ekr.20150419124739.25: *4* pr.print_tree_bodies
    def print_tree_bodies(self, event=None):
        """Print all the bodies in the selected tree."""
        doc = self.document(self.getBodies(self.c.p))
        self.print_doc(doc)
    #@+node:ekr.20150420084948.1: *4* pr.print_tree_html
    def print_tree_html(self, event=None):
        """
        Print all the bodies of the selected node as html. The concatenated
        bodies must valid html, including <html> and <body> elements.
        """
        doc = self.html_document(self.getBodies(self.c.p))
        self.print_doc(doc)
    #@+node:ekr.20150419124739.27: *4* pr.print_tree_nodes
    def print_tree_nodes(self, event=None):
        """Print all the nodes of the selected tree."""
        doc = self.document(self.getNodes(self.c.p), head=self.c.p.h)
        self.print_doc(doc)
    #@+node:ekr.20150419124739.7: *3* pr.Top level
    #@+node:ekr.20150419124739.12: *4* pr.print_doc
    def print_doc(self, doc):
        """Print the document."""
        dialog = printsupport.QPrintDialog()
        if dialog.exec_() == dialog.Accepted:
            doc.print_(dialog.printer())
    #@+node:ekr.20150419124739.13: *4* pr.preview_doc
    def preview_doc(self, doc):
        """Preview the document."""
        dialog = printsupport.QPrintPreviewDialog()
        dialog.setSizeGripEnabled(True)
        dialog.paintRequested.connect(doc.print_)
        dialog.exec_()
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@-leo

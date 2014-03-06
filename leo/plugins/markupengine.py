#@+leo-ver=5-thin
#@+node:peckj.20140306074510.22537: * @file markupengine.py
#@@language python
#@@tabwidth -4

#@+<< docstring >>
#@+node:peckj.20140305081017.6795: ** << docstring >>
'''TBD
'''
#@-<< docstring >>

__version__ = '0.1'
#@+<< version history >>
#@+node:peckj.20140305081017.6796: ** << version history >>
#@+at
# 
# JMP 0.1 - initial version
#@-<< version history >>

#@+<< imports >>
#@+node:peckj.20140305081017.6797: ** << imports >>
import leo.core.leoGlobals as g

import sys
import traceback

if g.isPython3:
    from io import StringIO
else:
    from StringIO import StringIO

# pygments, for source-code highlighting
try:
    import pygments
except ImportError:
    pygments = None

## individual markup imports here

# for reST
#@+<< import docutils >>
#@+node:peckj.20140305081017.6820: *3* << import docutils >>
try:
    import docutils
    import docutils.core
except ImportError:
    docutils = None
if docutils:
    try:
        from docutils.core import publish_string
        from docutils.utils import SystemMessage
        got_docutils = True
    except ImportError:
        got_docutils = False
        g.es_exception()
    except SyntaxError:
        got_docutils = False
        g.es_exception()
else:
    #g.es_print('viewrendered2.py: docutils not found',color='red')
    got_docutils = False
#@-<< import docutils >>

# for markdown
#@+<< import markdown >>
#@+node:peckj.20140305081017.6821: *3* << import markdown >>
try:
    from markdown import markdown
    got_markdown = True
except ImportError:
    got_markdown = False
#@-<< import markdown >>


#@-<< imports >>

#@+others
#@+node:peckj.20140305081017.6798: ** init
def init ():

    if g.app.gui is None:
        g.app.createQtGui(__file__)

    ok = g.app.gui.guiName().startswith('qt')

    if ok:
        g.registerHandler(('new','open2'),onCreate)
        g.plugin_signon(__name__)
    else:
        g.es('Error loading plugin markupengine.py', color='red')

    return ok
#@+node:peckj.20140305081017.6799: ** onCreate
def onCreate (tag, keys):
    c = keys.get('c')
    if not c: return
    
    mec = MarkupEngineController(c)
    c.markup = mec
#@+node:peckj.20140305081017.6800: ** class MarkupEngineController
class MarkupEngineController:
    
    #@+others
    #@+node:peckj.20140305081017.6801: *3* __init__
    def __init__(self, c):
        # Warning: hook handlers must use keywords.get('c'), NOT self.c.
        
        self.c = c
        self.markup_engines = {}
        self.markup_aliases = {}
        self.initialize_markup_engines()

    #@+node:peckj.20140305081017.6822: *4* initialize_markup_engines
    def initialize_markup_engines(self):
        ''' initialize all the markup engines here '''
        if got_docutils:
            rme = RSTMarkupEngine(self.c)
            self.markup_engines['rst'] = rme
            self.markup_aliases['rest'] = 'rst'
        if got_markdown:
            mde = MDMarkupEngine(self.c)
            self.markup_engines['md'] = mde
    #@+node:peckj.20140305081017.6823: *3* @property supported_markup
    @property
    def supported_markup(self):
        ''' return a list of supported markup languages '''
        return self.markup_engines.keys()
    #@+node:peckj.20140305081017.6825: *3* get_engine
    def get_engine(self, name):
        ''' return the MarkupEngine object corresponding to the 
            type of markup given as 'name', or None, if not 
            supported
        '''
        if name in self.markup_aliases.keys():
            name = self.markup_aliases[name]
        return self.markup_engines.get(name, None)
    #@+node:peckj.20140305081017.6824: *3* get_html
    def get_html(self, rootNode, subtreeMode=None, showCode=False, 
                 executeCode=False, codeReturnsMarkup=False, 
                 verbose=False, assets=None, headers=None, mode='rst'):
        ''' explanation of arguments:
            rootNode: root node of the tree to be rendered, or just the node to be rendered
            subtreeMode: one of 'inorder', 'sections', 'slideshow', or None
                         inorder -> subtree in order, ignoring @others and < < sections > >
                         sections -> expanded value of rootNode, ignoring headlines
                         slideshow -> same as inorder, but output formatted as a slideshow
                         None -> just the single rootNode
            showCode: render code in a <pre> block?
            executeCode: run any @language python nodes?
            codeReturnsMarkup: any executed code returns markup
            verbose: extra logging and output of intermediate files
            assets: a list of .js and .css files to include in the headers
            headers: custom text inserted verbatim into the headers
            mode: incoming markup language, used to delegate to a proper MarkupEngine instance
      
            delegates to a MarkupEngine instance that does the fancy stuff that vr2 currently does, returning
            an HTML string
        '''
        
        result = None
        engine = self.get_engine(mode)
        if engine:
            result = engine.get_html(rootNode, subtreeMode=subtreeMode, showCode=showCode,
                                     executeCode=executeCode, codeReturnsMarkup=codeReturnsMarkup, 
                                     verbose=verbose, assets=assets, headers=headers)
        else:
            g.es("%s not supported!" % mode, color='red')
        return result
        
    #@+node:peckj.20140306074510.22568: *3* get_markup
    def get_markup(self, rootNode, subtreeMode=None, showCode=False, 
                 executeCode=False, codeReturnsMarkup=False, 
                 verbose=False, mode='rst'):
        ''' explanation of arguments:
            rootNode: root node of the tree to be rendered, or just the node to be rendered
            subtreeMode: one of 'inorder', 'sections', or None
                         inorder -> subtree in order, ignoring @others and < < sections > >
                         sections -> expanded value of rootNode, ignoring headlines
                         None -> just the single rootNode
            showCode: render code in a <pre> block?
            executeCode: run any @language python nodes?
            codeReturnsMarkup: any executed code returns markup
            verbose: extra logging and output of intermediate files
            mode: incoming markup language, used to delegate to a proper MarkupEngine instance
      
            delegates to a MarkupEngine instance that does the fancy stuff that vr2 currently does, returning
            a constructed markup string
        '''
        
        result = None
        engine = self.get_engine(mode)
        if engine:
            result = engine.get_markup(rootNode, subtreeMode=subtreeMode, showCode=showCode,
                                     executeCode=executeCode, codeReturnsMarkup=codeReturnsMarkup, 
                                     verbose=verbose)
        else:
            g.es("%s not supported!" % mode, color='red')
        return result
        
    #@-others
#@+node:peckj.20140305081017.6817: ** MarkupEngines
#@+at
# These classes must provide the following function with this sigature:
# 
#     get_html(rootNode, subtreeMode, showCode,
#              executeCode, codeReturnsMarkup, 
#              verbose, assets, headers)
#     
#     get_markup(rootNode, subtreeMode, showCode,
#                executeCode, codeReturnsMarkup,
#                verbose)
# 
#     See MarkupEngineController.get_html() for details on these params.
#@+node:peckj.20140305081017.6818: *3* class RSTMarkupEngine
class RSTMarkupEngine:
    #@+others
    #@+node:peckj.20140305150735.6567: *4* __init__
    def __init__(self, c):
        self.c = c
    #@-others
#@+node:peckj.20140305081017.6819: *3* class MDMarkupEngine
class MDMarkupEngine:
    #@+others
    #@+node:peckj.20140305081017.6848: *4* __init__
    def __init__(self, c):
        self.c = c
        self.name = 'Markdown MarkupEngine' # not terribly useful
    #@+node:peckj.20140305081017.6849: *4* get_html
    def get_html(self, rootNode, subtreeMode=None, showCode=False, 
                 executeCode=False, codeReturnsMarkup=False,  
                 verbose=False, assets=None, headers=None):
        self.rootNode = rootNode.copy()
        self.subtreeMode = subtreeMode
        self.sections = sections
        self.showCode = showCode
        self.executeCode = executeCode
        self.codeReturnsMarkup = codeReturnsMarkup
        self.slideshow = (subtreeMode == 'slideshow') # unused
        self.verbose = verbose
        self.assets = assets
        self.headers = headers
        
        html = '<html><head>'
        
        if headers:
            html = html + headers
        if assets:
            for asset in assets:
                if asset.endswith('.js'):
                    html = html + '<script src="%s"></script>' % asset
                elif asset.endswith('.css'):
                    html = html + '<link rel="stylesheet" type="text/css" href="%s">' % asset

        html = html + '</head><body>'
        
        bodytext = self.md_to_html()
        
        html = html + bodytext + '</body></html>'
        
        return html
    #@+node:peckj.20140305081017.6850: *5* md_to_html
    def md_to_html(self):
        c = self.c
        html = self.process_nodes()
        
        try:
            # Call markdown to get the string.
            mdext = c.config.getString('view-rendered-md-extensions') or 'extra'
            mdext = [x.strip() for x in mdext.split(',')]
            if pygments:
                mdext.append('codehilite')
            html = markdown(html, mdext)
            return g.toUnicode(html)
        except Exception as e:
            print(e)
            return 'Markdown error... %s' % e
    #@+node:peckj.20140305081017.6851: *6* process_nodes
    def process_nodes(self):
        """
        Process the markdown for a node, defaulting to node's entire tree.
        
        Any code blocks found (designated by @language python) will be executed
        in order found as the tree is walked. No section references are heeded.
        Output directed to stdout and stderr are included in the md source.
        If self.showcode is True, then the execution output is included in a
        '```' block. Otherwise the output is assumed to be valid markdown and
        included in the md source.
        """
        c = self.c
        root = self.rootNode
        self.reflevel = c.p.level() # for self.underline2().
        result = []
        environment = {'c': c, 'g': g, 'p': c.p}
        self.process_one_node(root,result,environment)
        if self.subtreeMode in ['inorder', 'slideshow']:
            for p in root.subtree():
                self.process_one_node(p,result,environment)
        s = '\n'.join(result)
        if self.verbose:
            self.write_md(root,s)
        return s
    #@+node:peckj.20140305081017.6842: *7* process_one_node
    def process_one_node(self,p,result,environment):
        '''Handle one node.'''
        c = self.c
        result.append(self.underline2(p))
        d = c.scanAllDirectives(p)
        if self.verbose:
            g.trace(d.get('language') or 'None',':',p.h)
        s,code = self.process_directives(p.b,d)
        result.append(s)
        result.append('\n\n')
            # Add an empty line so bullet lists display properly.
        if code and self.executeCode:
            s,err = self.exec_code(code,environment)
                # execute code found in a node, append to md
            if not self.codeReturnsMarkup and s.strip():
                s = self.format_output(s)  # if some non-md to print
            result.append(s) # append, whether plain or md output
            if err:
                err = self.format_output(err, prefix='**Error**:')      
                result.append(err)
    #@+node:peckj.20140305081017.6845: *8* process_directives
    def process_directives(self, s, d):
        """s is string to process, d is dictionary of directives at the node."""
        trace = False and not g.unitTesting
        lang = d.get('language') or 'python' # EKR.
        codeflag = lang != 'md' # EKR
        lines = g.splitLines(s)
        result = []
        code = ''
        if codeflag and self.showCode:
            result.append(self.code_directive(lang)) # EKR
        for s in lines:
            if s.startswith('@'):
                i = g.skip_id(s,1)
                word = s[1:i]
                # Add capability to detect mid-node language directives (not really that useful).
                # Probably better to just use a code directive.  "execute-script" is not possible.
                # If removing, ensure "if word in g.globalDirectiveList:  continue" is retained
                # to stop directive being put into the reST output.
                if word=='language' and not codeflag:  # only if not already code
                    lang = s[i:].strip()
                    codeflag = lang in ['python',]
                    if codeflag:
                        if self.verbose:
                            g.es('New code section within node:',lang)
                        if self.showCode:
                            result.append(self.code_directive(lang)) # EKR
                    else:
                        result.append('\n\n')
                    continue
                elif word in g.globalDirectiveList:
                    continue
            if codeflag:
                if self.showCode:
                    result.append('    ' + s)  # 4 space indent on each line
                code += s  # accumulate code lines for execution
            else:
                result.append(s)
        result = ''.join(result)
        if trace: g.trace('result:\n',result) # ,'\ncode:',code)
        return result, code
    #@+node:peckj.20140305081017.6843: *8* exec_code
    def exec_code(self,code,environment):
        """Execute the code, capturing the output in stdout and stderr."""
        trace = True and not g.unitTesting
        if trace: g.trace('\n',code)
        c = self.c
        saveout = sys.stdout  # save stdout
        saveerr = sys.stderr
        sys.stdout = bufferout = StringIO()
        sys.stderr = buffererr = StringIO()
        # Protect against exceptions within exec
        try:
            exec(code,environment)
        except Exception:
            print >> buffererr, traceback.format_exc()
            buffererr.flush()  # otherwise exception info appears too late
            g.es('MDMarkupEngine exception')
            g.es_exception()
        # Restore stdout, stderr
        sys.stdout = saveout  # was sys.__stdout__
        sys.stderr = saveerr  # restore stderr
        return bufferout.getvalue(), buffererr.getvalue()
    #@+node:peckj.20140305081017.6846: *8* underline2
    def underline2(self, p):
        """
        Use the given string and convert it to a markdown headline for display
        """
        # Use relatively unused underline characters, cater for many levels
        l = p.level()-self.reflevel+1
        ch = '#' * l
        ch += ' ' + p.h
        return ch
    #@+node:peckj.20140305081017.6844: *8* format_output
    def format_output(self,s, prefix='```'):
        """Formats the multi-line string 's' into a md literal block."""
        out = '\n\n'+prefix+'\n\n'
        lines = g.splitLines(s)
        for line in lines:
            out += '    ' + line
        return out + '\n```\n'
    #@+node:peckj.20140305081017.6841: *8* code_directive
    def code_directive(self,lang):
        '''Return a markdown block or code directive.'''
        if pygments:
            d = '\n    :::' + lang
            return d
        else:
            return '\n'
    #@+node:peckj.20140305081017.6847: *7* write_md
    def write_md(self,root,s):
        '''Write s, the final assembled md text, to leo.md.'''
        c = self.c
        filename = 'leo.md'
        d = c.scanAllDirectives(root)
        path = d.get('path')
        pathname = g.os_path_finalize_join(path,filename)

        f = open(pathname,'wb')
        f.write(s.encode('utf8'))
        f.close()
    #@+node:peckj.20140306074510.22566: *4* get_markup
    def get_markup(self, rootNode, subtreeMode=None, showCode=False, 
                 executeCode=False, codeReturnsMarkup=False,  
                 verbose=False):
        self.rootNode = rootNode.copy()
        self.subtreeMode = subtreeMode
        self.sections = sections
        self.showCode = showCode
        self.executeCode = executeCode
        self.codeReturnsMarkup = codeReturnsMarkup
        self.verbose = verbose
        self.slideshow = False
        
        markup = self.process_nodes()
    #@-others
#@-others
#@-leo

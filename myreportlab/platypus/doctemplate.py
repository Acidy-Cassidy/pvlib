"""
Document templates for PLATYPUS.
"""

from ..pdfgen import Canvas
from ..lib.pagesizes import A4, LETTER
from .frames import Frame
from .flowables import PageBreak


class PageTemplate:
    """
    Template for a page layout.
    """

    def __init__(self, id=None, frames=None, onPage=None, onPageEnd=None,
                 pagesize=None, autoNextPageTemplate=None):
        """
        Create a page template.

        Args:
            id: Template identifier
            frames: List of Frame objects
            onPage: Callback before page content
            onPageEnd: Callback after page content
            pagesize: Page dimensions
            autoNextPageTemplate: Next template ID
        """
        self.id = id
        self.frames = frames or []
        self.onPage = onPage
        self.onPageEnd = onPageEnd
        self.pagesize = pagesize
        self.autoNextPageTemplate = autoNextPageTemplate

    def beforeDrawPage(self, canvas, doc):
        """Called before page content."""
        if self.onPage:
            self.onPage(canvas, doc)

    def afterDrawPage(self, canvas, doc):
        """Called after page content."""
        if self.onPageEnd:
            self.onPageEnd(canvas, doc)


class BaseDocTemplate:
    """
    Base document template.
    """

    def __init__(self, filename, pagesize=LETTER, pageTemplates=None,
                 showBoundary=0, leftMargin=72, rightMargin=72,
                 topMargin=72, bottomMargin=72, allowSplitting=1,
                 title=None, author=None, subject=None, creator=None,
                 producer=None, keywords=None, pageCompression=None,
                 _pageBreakQuick=1, encrypt=None):
        """
        Create base document template.

        Args:
            filename: Output file path
            pagesize: Page dimensions
            pageTemplates: List of PageTemplate objects
            leftMargin, rightMargin, topMargin, bottomMargin: Page margins
            title, author, etc.: Document metadata
        """
        self.filename = filename
        self.pagesize = pagesize
        self.pageTemplates = pageTemplates or []
        self.showBoundary = showBoundary
        self.leftMargin = leftMargin
        self.rightMargin = rightMargin
        self.topMargin = topMargin
        self.bottomMargin = bottomMargin
        self.allowSplitting = allowSplitting
        self.title = title
        self.author = author
        self.subject = subject
        self.creator = creator
        self.producer = producer
        self.keywords = keywords
        self.pageCompression = pageCompression
        self.encrypt = encrypt

        # State
        self._pageNum = 0
        self.canv = None
        self.page = None
        self.frame = None
        self.width = pagesize[0] - leftMargin - rightMargin
        self.height = pagesize[1] - topMargin - bottomMargin

    def addPageTemplates(self, templates):
        """Add page templates."""
        if isinstance(templates, list):
            self.pageTemplates.extend(templates)
        else:
            self.pageTemplates.append(templates)

    def build(self, flowables, filename=None, canvasmaker=Canvas):
        """
        Build the document.

        Args:
            flowables: List of flowable objects
            filename: Override output file
            canvasmaker: Canvas class to use
        """
        filename = filename or self.filename

        # Create canvas
        self.canv = canvasmaker(filename, pagesize=self.pagesize)

        # Set metadata
        if self.title:
            self.canv._info = {"Title": self.title}

        # Get page template
        if self.pageTemplates:
            self.page = self.pageTemplates[0]
        else:
            # Create default template
            frame = Frame(
                self.leftMargin,
                self.bottomMargin,
                self.width,
                self.height,
                id="normal"
            )
            self.page = PageTemplate(id="First", frames=[frame])

        # Process flowables
        self._build(flowables)

        # Save
        self.canv.save()

    def _build(self, flowables):
        """Process flowables and build pages."""
        # Start first page
        self._startPage()

        remaining = list(flowables)
        while remaining:
            f = remaining.pop(0)

            # Handle page break
            if isinstance(f, PageBreak):
                self._endPage()
                self._startPage()
                continue

            # Wrap flowable
            w, h = f.wrap(self.frame._aW, self.frame.availHeight)

            # Check if fits
            if h > self.frame.availHeight and self.frame.availHeight < self.frame._aH:
                # Need new page
                self._endPage()
                self._startPage()
                w, h = f.wrap(self.frame._aW, self.frame.availHeight)

            # Try to add
            result = self.frame.add(f, self.canv, trySplit=self.allowSplitting)

            if result == 0:
                # Doesn't fit at all
                if self.allowSplitting:
                    parts = f.split(self.frame._aW, self.frame.availHeight)
                    if parts:
                        remaining = parts + remaining
                        continue

                # Start new page and retry
                self._endPage()
                self._startPage()
                remaining.insert(0, f)

        # End last page
        self._endPage()

    def _startPage(self):
        """Start a new page."""
        self._pageNum += 1

        # Reset frame
        if self.page.frames:
            self.frame = self.page.frames[0]
            self.frame._reset()

        # Call template callback
        self.page.beforeDrawPage(self.canv, self)

    def _endPage(self):
        """End current page."""
        self.page.afterDrawPage(self.canv, self)
        self.canv.showPage()

    @property
    def pageNum(self):
        return self._pageNum


class SimpleDocTemplate(BaseDocTemplate):
    """
    Simple document template with single-frame pages.
    """

    def __init__(self, filename, pagesize=LETTER, rightMargin=72,
                 leftMargin=72, topMargin=72, bottomMargin=72,
                 showBoundary=0, **kwargs):
        """
        Create simple document template.

        Args:
            filename: Output file path
            pagesize: Page dimensions
            margins: Page margins
        """
        super().__init__(
            filename,
            pagesize=pagesize,
            rightMargin=rightMargin,
            leftMargin=leftMargin,
            topMargin=topMargin,
            bottomMargin=bottomMargin,
            showBoundary=showBoundary,
            **kwargs
        )

        # Create default frame
        frame = Frame(
            leftMargin,
            bottomMargin,
            pagesize[0] - leftMargin - rightMargin,
            pagesize[1] - topMargin - bottomMargin,
            id="normal"
        )

        # Create default template
        template = PageTemplate(id="First", frames=[frame], pagesize=pagesize)
        self.addPageTemplates(template)

    def build(self, flowables, onFirstPage=None, onLaterPages=None,
              canvasmaker=Canvas):
        """
        Build the document.

        Args:
            flowables: List of flowable objects
            onFirstPage: Callback for first page
            onLaterPages: Callback for subsequent pages
            canvasmaker: Canvas class
        """
        if onFirstPage:
            self.pageTemplates[0].onPage = onFirstPage

        if onLaterPages and len(self.pageTemplates) > 1:
            for t in self.pageTemplates[1:]:
                t.onPage = onLaterPages

        super().build(flowables, canvasmaker=canvasmaker)

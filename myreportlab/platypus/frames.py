"""
Frame class for document layout regions.
"""


class Frame:
    """
    A rectangular region on a page for placing flowables.
    """

    def __init__(self, x1, y1, width, height, leftPadding=6, bottomPadding=6,
                 rightPadding=6, topPadding=6, id=None, showBoundary=0,
                 overlapAttachedSpace=None, _debug=None):
        """
        Create a frame.

        Args:
            x1: X coordinate of bottom-left corner
            y1: Y coordinate of bottom-left corner
            width: Frame width
            height: Frame height
            leftPadding: Left padding
            bottomPadding: Bottom padding
            rightPadding: Right padding
            topPadding: Top padding
            id: Frame identifier
            showBoundary: Show frame boundary
        """
        self._x1 = x1
        self._y1 = y1
        self._width = width
        self._height = height
        self._leftPadding = leftPadding
        self._bottomPadding = bottomPadding
        self._rightPadding = rightPadding
        self._topPadding = topPadding
        self.id = id
        self.showBoundary = showBoundary

        # Available area
        self._aW = width - leftPadding - rightPadding
        self._aH = height - topPadding - bottomPadding

        # Current position (top-down)
        self._x = x1 + leftPadding
        self._y = y1 + height - topPadding
        self._atTop = True

    def _reset(self):
        """Reset frame position for new page."""
        self._x = self._x1 + self._leftPadding
        self._y = self._y1 + self._height - self._topPadding
        self._atTop = True

    def addFromList(self, drawlist, canv):
        """
        Add flowables from a list.

        Args:
            drawlist: List of flowables
            canv: Canvas to draw on

        Returns:
            1 if all flowables fit, 0 otherwise
        """
        while drawlist:
            f = drawlist[0]

            # Check space
            if self._atTop:
                space = 0
            else:
                space = f.getSpaceBefore()

            w, h = f.wrap(self._aW, self._y - self._y1 - self._bottomPadding)

            if self._y - h - space < self._y1 + self._bottomPadding:
                # Doesn't fit
                return 0

            # Draw
            self._y -= space
            if not self._atTop:
                self._y -= space

            f.drawOn(canv, self._x, self._y - h)
            self._y -= h

            # Add space after
            self._y -= f.getSpaceAfter()

            self._atTop = False
            del drawlist[0]

        return 1

    def add(self, flowable, canv, trySplit=0):
        """
        Add a single flowable.

        Args:
            flowable: Flowable to add
            canv: Canvas
            trySplit: Try to split if doesn't fit

        Returns:
            1 if added, 0 if doesn't fit
        """
        w, h = flowable.wrap(self._aW, self._y - self._y1 - self._bottomPadding)

        if self._atTop:
            space = 0
        else:
            space = flowable.getSpaceBefore()

        if self._y - h - space < self._y1 + self._bottomPadding:
            if trySplit:
                # Try to split
                parts = flowable.split(self._aW, self._y - self._y1 - self._bottomPadding - space)
                if parts:
                    for part in parts[:-1]:
                        self.add(part, canv, trySplit=0)
                    return 2  # Partial
            return 0

        # Draw
        self._y -= space
        flowable.drawOn(canv, self._x, self._y - h)
        self._y -= h
        self._y -= flowable.getSpaceAfter()

        self._atTop = False
        return 1

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def availWidth(self):
        return self._aW

    @property
    def availHeight(self):
        return self._y - self._y1 - self._bottomPadding

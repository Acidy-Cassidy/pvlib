"""
Page size definitions for reportlab.
All sizes are in points (1/72 inch).
"""

from .units import inch, cm, mm

# ISO A sizes (portrait)
A0 = (2384, 3370)
A1 = (1684, 2384)
A2 = (1190, 1684)
A3 = (842, 1190)
A4 = (595, 842)
A5 = (420, 595)
A6 = (297, 420)
A7 = (210, 297)
A8 = (148, 210)
A9 = (105, 148)
A10 = (74, 105)

# ISO B sizes (portrait)
B0 = (2834, 4008)
B1 = (2004, 2834)
B2 = (1417, 2004)
B3 = (1001, 1417)
B4 = (709, 1001)
B5 = (499, 709)
B6 = (354, 499)
B7 = (249, 354)
B8 = (176, 249)
B9 = (125, 176)
B10 = (88, 125)

# ISO C sizes (portrait) - for envelopes
C0 = (2599, 3677)
C1 = (1837, 2599)
C2 = (1298, 1837)
C3 = (918, 1298)
C4 = (649, 918)
C5 = (459, 649)
C6 = (323, 459)
C7 = (230, 323)
C8 = (162, 230)
C9 = (113, 162)
C10 = (79, 113)

# US sizes
LETTER = (612, 792)  # 8.5 x 11 inches
LEGAL = (612, 1008)  # 8.5 x 14 inches
TABLOID = ELEVENSEVENTEEN = (792, 1224)  # 11 x 17 inches
LEDGER = (1224, 792)  # 17 x 11 inches (landscape tabloid)

# Junior Legal
JUNIOR_LEGAL = (360, 576)  # 5 x 8 inches

# Government sizes
GOVERNMENT_LETTER = (576, 756)  # 8 x 10.5 inches
GOVERNMENT_LEGAL = (612, 936)  # 8.5 x 13 inches

# ANSI sizes
ANSI_A = LETTER
ANSI_B = TABLOID
ANSI_C = (1224, 1584)  # 17 x 22 inches
ANSI_D = (1584, 2448)  # 22 x 34 inches
ANSI_E = (2448, 3168)  # 34 x 44 inches

# Architectural sizes
ARCH_A = (648, 864)   # 9 x 12 inches
ARCH_B = (864, 1296)  # 12 x 18 inches
ARCH_C = (1296, 1728) # 18 x 24 inches
ARCH_D = (1728, 2592) # 24 x 36 inches
ARCH_E = (2592, 3456) # 36 x 48 inches
ARCH_E1 = (2160, 3024) # 30 x 42 inches

# ID card sizes
ID_1 = (243, 153)  # Credit card size (85.6 x 53.98 mm)
ID_2 = (297, 210)  # A7 size
ID_3 = (354, 250)  # B7 size

# Envelope sizes
ENVELOPE_C4 = C4
ENVELOPE_C5 = C5
ENVELOPE_C6 = C6
ENVELOPE_DL = (312, 624)  # 110 x 220 mm


def landscape(pagesize):
    """
    Return the landscape version of a page size.

    Args:
        pagesize: (width, height) tuple

    Returns:
        (height, width) tuple
    """
    width, height = pagesize
    if width < height:
        return (height, width)
    return pagesize


def portrait(pagesize):
    """
    Return the portrait version of a page size.

    Args:
        pagesize: (width, height) tuple

    Returns:
        (width, height) with height > width
    """
    width, height = pagesize
    if width > height:
        return (height, width)
    return pagesize

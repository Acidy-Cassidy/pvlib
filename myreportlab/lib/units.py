"""
Unit conversion constants for reportlab.
"""

# Base unit is points (1/72 inch)
inch = 72.0
cm = inch / 2.54
mm = cm / 10.0
pica = 12.0  # 1 pica = 12 points

# Common conversions
def toLength(s):
    """
    Convert a length string to points.

    Args:
        s: Length string (e.g., "1in", "2.5cm", "72pt")

    Returns:
        Length in points
    """
    if isinstance(s, (int, float)):
        return float(s)

    s = s.strip().lower()

    if s.endswith("in"):
        return float(s[:-2]) * inch
    elif s.endswith("cm"):
        return float(s[:-2]) * cm
    elif s.endswith("mm"):
        return float(s[:-2]) * mm
    elif s.endswith("pt"):
        return float(s[:-2])
    elif s.endswith("pc") or s.endswith("pica"):
        num = s.replace("pica", "").replace("pc", "")
        return float(num) * pica
    else:
        return float(s)

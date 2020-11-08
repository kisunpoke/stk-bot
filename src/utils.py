"""general-purpose things that don't fit anywhere"""

def percentage(value, precision=2):
    """Convert `float` to #.##% notation as `str`.
    
    A value of 1 = `"100.00%"`; 0.5 = `"50.00%"`"""
    return f"{value:.{precision}%}"
    
def comma_sep(value, precision=0):
    """Convert `int` to #,###.## notation as `str`"""
    #https://stackoverflow.com/questions/36626017/format-a-number-with-comma-separators-and-round-to-2-decimal-places-in-python-2
    return f"{value:,.{precision}f}"

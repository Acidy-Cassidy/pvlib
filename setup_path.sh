#!/bin/bash
# Add mypylibs to PYTHONPATH
# Source this file or add the export line to your ~/.bashrc or ~/.zshrc

export PYTHONPATH="/opt/mypylibs${PYTHONPATH:+:$PYTHONPATH}"

echo "PYTHONPATH updated: $PYTHONPATH"
echo "You can now use:"
echo "  import mynumpy as np"
echo "  import mypandas as pd"

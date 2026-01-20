#!/bin/bash
#===============================================================================
#
#   MYPYLIBS - Automated Installation Script for Ubuntu Linux
#
#   This script installs the custom Python libraries system-wide so they
#   can be imported from anywhere on your system.
#
#   Usage:
#       sudo ./install.sh           # Install libraries
#       sudo ./install.sh --test    # Install and run tests
#       sudo ./install.sh --remove  # Uninstall libraries
#       ./install.sh --help         # Show help
#
#===============================================================================

set -e

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_NAME="mypylibs"
PTH_FILENAME="${LIB_NAME}.pth"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------

print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BOLD}[$1/$TOTAL_STEPS]${NC} $2"
}

show_help() {
    echo ""
    echo "MYPYLIBS Installation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h      Show this help message"
    echo "  --test, -t      Run tests after installation"
    echo "  --remove, -r    Remove/uninstall the libraries"
    echo "  --check, -c     Check installation status"
    echo "  --verbose, -v   Verbose output"
    echo ""
    echo "Examples:"
    echo "  sudo $0              # Install libraries"
    echo "  sudo $0 --test       # Install and run tests"
    echo "  sudo $0 --remove     # Uninstall libraries"
    echo "  $0 --check           # Check if installed (no sudo needed)"
    echo ""
}

#-------------------------------------------------------------------------------
# System Checks
#-------------------------------------------------------------------------------

check_ubuntu() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]] || [[ "$ID_LIKE" == *"ubuntu"* ]] || [[ "$ID_LIKE" == *"debian"* ]]; then
            return 0
        fi
    fi

    # Also check for Debian-based systems
    if [ -f /etc/debian_version ]; then
        return 0
    fi

    return 1
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
        return 0
    fi
    return 1
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        return 1
    fi
    return 0
}

get_site_packages() {
    # Try multiple methods to find site-packages

    # Method 1: Use site module
    SITE_PACKAGES=$($PYTHON_CMD -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)

    if [ -n "$SITE_PACKAGES" ] && [ -d "$SITE_PACKAGES" ]; then
        echo "$SITE_PACKAGES"
        return 0
    fi

    # Method 2: Check common locations
    for dir in \
        "/usr/local/lib/python3.12/dist-packages" \
        "/usr/local/lib/python3.11/dist-packages" \
        "/usr/local/lib/python3.10/dist-packages" \
        "/usr/local/lib/python3/dist-packages" \
        "/usr/lib/python3/dist-packages"; do
        if [ -d "$dir" ]; then
            echo "$dir"
            return 0
        fi
    done

    # Method 3: Find based on Python version
    PY_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

    dir="/usr/local/lib/python${PY_MAJOR}.${PY_MINOR}/dist-packages"
    if [ -d "$dir" ]; then
        echo "$dir"
        return 0
    fi

    return 1
}

#-------------------------------------------------------------------------------
# Installation Functions
#-------------------------------------------------------------------------------

do_install() {
    TOTAL_STEPS=5

    print_header "MYPYLIBS Installation"

    #---------------------------------------------------------------------------
    # Step 1: Check operating system
    #---------------------------------------------------------------------------
    print_step 1 "Checking operating system..."

    if ! check_ubuntu; then
        print_error "This script is designed for Ubuntu/Debian-based systems."
        print_info "Detected OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2)"
        print_info "For other systems, see INSTALL.txt for manual instructions."
        exit 1
    fi

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_success "Detected: $PRETTY_NAME"
    fi

    #---------------------------------------------------------------------------
    # Step 2: Check Python installation
    #---------------------------------------------------------------------------
    print_step 2 "Checking Python installation..."

    if ! check_python; then
        print_error "Python 3 is not installed."
        print_info "Install with: sudo apt install python3"
        exit 1
    fi

    print_success "Found Python $PYTHON_VERSION ($PYTHON_CMD)"

    # Check Python version is 3.8+
    PY_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi

    #---------------------------------------------------------------------------
    # Step 3: Check permissions
    #---------------------------------------------------------------------------
    print_step 3 "Checking permissions..."

    if ! check_root; then
        print_error "This script requires root privileges."
        print_info "Please run with: sudo $0"
        exit 1
    fi

    print_success "Running with root privileges"

    #---------------------------------------------------------------------------
    # Step 4: Find site-packages and create .pth file
    #---------------------------------------------------------------------------
    print_step 4 "Installing libraries..."

    SITE_PACKAGES=$(get_site_packages)

    if [ -z "$SITE_PACKAGES" ]; then
        print_error "Could not find Python site-packages directory."
        exit 1
    fi

    print_info "Site-packages: $SITE_PACKAGES"

    PTH_FILE="$SITE_PACKAGES/$PTH_FILENAME"

    # Check if already installed
    if [ -f "$PTH_FILE" ]; then
        EXISTING_PATH=$(cat "$PTH_FILE")
        if [ "$EXISTING_PATH" == "$SCRIPT_DIR" ]; then
            print_warning "Libraries already installed at this location."
        else
            print_warning "Updating existing installation..."
            print_info "Previous path: $EXISTING_PATH"
        fi
    fi

    # Create .pth file
    echo "$SCRIPT_DIR" > "$PTH_FILE"

    if [ -f "$PTH_FILE" ]; then
        print_success "Created $PTH_FILE"
    else
        print_error "Failed to create .pth file"
        exit 1
    fi

    # Set permissions
    chmod 644 "$PTH_FILE"

    #---------------------------------------------------------------------------
    # Step 5: Verify installation
    #---------------------------------------------------------------------------
    print_step 5 "Verifying installation..."

    # Test imports
    IMPORT_TEST=$($PYTHON_CMD -c "
import sys
try:
    import mynumpy
    import mypandas
    import myrequests
    import mytqdm
    import mycolorama
    import mypsutil
    import mypytest
    import mymatplotlib
    import mybeautifulsoup
    import myhashlib
    import myfeedparser
    import mypypdf
    import myreportlab
    print('OK')
except ImportError as e:
    print(f'FAIL: {e}')
" 2>&1)

    if [ "$IMPORT_TEST" == "OK" ]; then
        print_success "All libraries imported successfully"
    else
        print_error "Import verification failed: $IMPORT_TEST"
        exit 1
    fi

    #---------------------------------------------------------------------------
    # Complete
    #---------------------------------------------------------------------------
    print_header "Installation Complete"

    echo -e "Libraries installed at: ${CYAN}$SCRIPT_DIR${NC}"
    echo -e "PTH file created at:    ${CYAN}$PTH_FILE${NC}"
    echo ""
    echo "You can now import the libraries from anywhere:"
    echo ""
    echo -e "    ${GREEN}import mynumpy as np${NC}"
    echo -e "    ${GREEN}import mypandas as pd${NC}"
    echo -e "    ${GREEN}import myrequests as requests${NC}"
    echo -e "    ${GREEN}from mytqdm import tqdm${NC}"
    echo -e "    ${GREEN}from mycolorama import Fore, Style${NC}"
    echo -e "    ${GREEN}import mypsutil as psutil${NC}"
    echo -e "    ${GREEN}import mypytest as pytest${NC}"
    echo -e "    ${GREEN}import mymatplotlib.pyplot as plt${NC}"
    echo -e "    ${GREEN}from mybeautifulsoup import BeautifulSoup${NC}"
    echo -e "    ${GREEN}import myhashlib as hashlib${NC}"
    echo -e "    ${GREEN}import myfeedparser as feedparser${NC}"
    echo -e "    ${GREEN}import mypypdf as pypdf${NC}"
    echo -e "    ${GREEN}import myreportlab${NC}"
    echo ""

    if [ "$RUN_TESTS" == "true" ]; then
        do_test
    fi
}

do_remove() {
    print_header "MYPYLIBS Uninstallation"

    if ! check_root; then
        print_error "This script requires root privileges."
        print_info "Please run with: sudo $0 --remove"
        exit 1
    fi

    if ! check_python; then
        print_error "Python not found."
        exit 1
    fi

    SITE_PACKAGES=$(get_site_packages)
    PTH_FILE="$SITE_PACKAGES/$PTH_FILENAME"

    if [ -f "$PTH_FILE" ]; then
        rm "$PTH_FILE"
        print_success "Removed $PTH_FILE"
    else
        print_warning "PTH file not found. Libraries may not be installed."
    fi

    # Verify removal
    IMPORT_TEST=$($PYTHON_CMD -c "import mynumpy" 2>&1)

    if [[ "$IMPORT_TEST" == *"ModuleNotFoundError"* ]]; then
        print_success "Libraries successfully uninstalled"
    else
        print_warning "Libraries may still be accessible via other paths"
    fi

    echo ""
    echo "Note: Library files in $SCRIPT_DIR were not deleted."
    echo "To completely remove, delete the directory manually."
}

do_check() {
    print_header "MYPYLIBS Installation Check"

    echo "Checking installation status..."
    echo ""

    # Check Python
    if check_python; then
        echo -e "Python:        ${GREEN}$PYTHON_VERSION${NC}"
    else
        echo -e "Python:        ${RED}Not found${NC}"
        exit 1
    fi

    # Check site-packages
    SITE_PACKAGES=$(get_site_packages)
    if [ -n "$SITE_PACKAGES" ]; then
        echo -e "Site-packages: ${GREEN}$SITE_PACKAGES${NC}"
    else
        echo -e "Site-packages: ${RED}Not found${NC}"
    fi

    # Check PTH file
    PTH_FILE="$SITE_PACKAGES/$PTH_FILENAME"
    if [ -f "$PTH_FILE" ]; then
        PTH_CONTENT=$(cat "$PTH_FILE")
        echo -e "PTH file:      ${GREEN}$PTH_FILE${NC}"
        echo -e "PTH content:   ${CYAN}$PTH_CONTENT${NC}"
    else
        echo -e "PTH file:      ${YELLOW}Not found${NC}"
    fi

    echo ""
    echo "Library import status:"
    echo ""

    LIBS=("mynumpy" "mypandas" "myrequests" "mytqdm" "mycolorama" "mypsutil" "mypytest" "mymatplotlib" "mybeautifulsoup" "myhashlib" "myfeedparser" "mypypdf" "myreportlab")

    ALL_OK=true
    for lib in "${LIBS[@]}"; do
        RESULT=$($PYTHON_CMD -c "import $lib; print($lib.__version__ if hasattr($lib, '__version__') else 'OK')" 2>&1)
        if [[ "$RESULT" == *"ModuleNotFoundError"* ]] || [[ "$RESULT" == *"Error"* ]]; then
            echo -e "  $lib: ${RED}Not available${NC}"
            ALL_OK=false
        else
            echo -e "  $lib: ${GREEN}v$RESULT${NC}"
        fi
    done

    echo ""
    if [ "$ALL_OK" == "true" ]; then
        echo -e "${GREEN}All libraries are installed and accessible.${NC}"
    else
        echo -e "${YELLOW}Some libraries are not accessible.${NC}"
        echo "Run 'sudo $0' to install."
    fi
}

do_test() {
    print_header "Running Test Suite"

    if [ -f "$SCRIPT_DIR/test_libs.py" ]; then
        print_info "Executing test_libs.py..."
        echo ""
        $PYTHON_CMD "$SCRIPT_DIR/test_libs.py"
        echo ""
        print_success "Test suite completed"
    else
        print_error "test_libs.py not found in $SCRIPT_DIR"
        exit 1
    fi
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

# Parse arguments
RUN_TESTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --test|-t)
            RUN_TESTS=true
            shift
            ;;
        --remove|-r)
            do_remove
            exit 0
            ;;
        --check|-c)
            do_check
            exit 0
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run installation
do_install

#!/bin/bash
#
# Zenity Prompt Helper for Interactive Firmware Development
# Provides consistent dialog interfaces for AI-to-user communication
#

set -e

# Default values
TITLE="Interactive Firmware Dev"
WIDTH=400
HEIGHT=200

# Function to show usage
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [MESSAGE/ARGS]

Zenity dialog wrapper for AI-assisted firmware development.

OPTIONS:
    --question TEXT       Show yes/no question dialog
    --error TEXT          Show error dialog
    --info TEXT           Show info dialog
    --warning TEXT        Show warning dialog
    --entry TEXT [DEFAULT]  Show text entry dialog
    --list TEXT ITEM...   Show list selection dialog
    --scale TEXT [MIN] [MAX] [DEFAULT]  Show scale/numeric input
    --file-selection      Show file picker dialog
    --progress TEXT       Show progress dialog (read percentages from stdin)
    --title TITLE         Set dialog title (default: "$TITLE")
    --width WIDTH         Set dialog width (default: $WIDTH)
    --height HEIGHT       Set dialog height (default: $HEIGHT)
    --timeout SECONDS     Auto-close after N seconds
    --help                Show this help message

EXIT CODES:
    0   Success / Yes / OK
    1   Cancel / No / Error
    5   Timeout

EXAMPLES:
    # Yes/No question
    $(basename "$0") --question "Retry flash with different baud rate?"
    
    # Text entry with default
    result=$("$0" --entry "Enter Wi-Fi SSID:" "MyNetwork")
    
    # List selection
    choice=$("$0" --list "Select action:" "Retry" "Edit config" "Skip" "Abort")
    
    # Scale input
    timeout=$("$0" --scale "Set timeout (seconds):" 1 60 10)
    
    # Error with details
    $(basename "$0") --error "Panic detected!\n\nCheck hardware connections."

EOF
}

# Check if zenity is installed
check_zenity() {
    if ! command -v zenity &> /dev/null; then
        echo "Error: zenity is not installed" >&2
        echo "Install with: sudo apt-get install zenity" >&2
        exit 1
    fi
}

# Parse arguments
DIALOG_TYPE=""
MESSAGE=""
DEFAULT_VALUE=""
LIST_ITEMS=()
SCALE_MIN=0
SCALE_MAX=100
SCALE_DEFAULT=50
TIMEOUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --question)
            DIALOG_TYPE="question"
            MESSAGE="$2"
            shift 2
            ;;
        --error)
            DIALOG_TYPE="error"
            MESSAGE="$2"
            shift 2
            ;;
        --info)
            DIALOG_TYPE="info"
            MESSAGE="$2"
            shift 2
            ;;
        --warning)
            DIALOG_TYPE="warning"
            MESSAGE="$2"
            shift 2
            ;;
        --entry)
            DIALOG_TYPE="entry"
            MESSAGE="$2"
            if [[ -n "$3" && ! "$3" =~ ^-- ]]; then
                DEFAULT_VALUE="$3"
                shift 3
            else
                shift 2
            fi
            ;;
        --list)
            DIALOG_TYPE="list"
            MESSAGE="$2"
            shift 2
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                LIST_ITEMS+=("$1")
                shift
            done
            ;;
        --scale)
            DIALOG_TYPE="scale"
            MESSAGE="$2"
            if [[ -n "$3" && ! "$3" =~ ^-- ]]; then
                SCALE_MIN="$3"
                shift
            fi
            if [[ -n "$3" && ! "$3" =~ ^-- ]]; then
                SCALE_MAX="$3"
                shift
            fi
            if [[ -n "$3" && ! "$3" =~ ^-- ]]; then
                SCALE_DEFAULT="$3"
                shift
            fi
            shift 2
            ;;
        --file-selection)
            DIALOG_TYPE="file"
            shift
            ;;
        --progress)
            DIALOG_TYPE="progress"
            MESSAGE="$2"
            shift 2
            ;;
        --title)
            TITLE="$2"
            shift 2
            ;;
        --width)
            WIDTH="$2"
            shift 2
            ;;
        --height)
            HEIGHT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# Check zenity is available
check_zenity

# Build timeout args if specified
TIMEOUT_ARGS=""
if [[ -n "$TIMEOUT" ]]; then
    TIMEOUT_ARGS="--timeout=$TIMEOUT"
fi

# Execute appropriate dialog
case $DIALOG_TYPE in
    question)
        zenity --question \
            --title="$TITLE" \
            --text="$MESSAGE" \
            --width=$WIDTH \
            --height=$HEIGHT \
            $TIMEOUT_ARGS \
            --ok-label="Yes" \
            --cancel-label="No" \
            2>/dev/null
        ;;
    
    error)
        zenity --error \
            --title="$TITLE - Error" \
            --text="$MESSAGE" \
            --width=$WIDTH \
            --height=$HEIGHT \
            $TIMEOUT_ARGS \
            --no-wrap \
            2>/dev/null
        ;;
    
    info)
        zenity --info \
            --title="$TITLE" \
            --text="$MESSAGE" \
            --width=$WIDTH \
            --height=$HEIGHT \
            $TIMEOUT_ARGS \
            2>/dev/null
        ;;
    
    warning)
        zenity --warning \
            --title="$TITLE - Warning" \
            --text="$MESSAGE" \
            --width=$WIDTH \
            --height=$HEIGHT \
            $TIMEOUT_ARGS \
            2>/dev/null
        ;;
    
    entry)
        ENTRY_ARGS=(
            --entry
            --title="$TITLE"
            --text="$MESSAGE"
            --width=$WIDTH
            --height=$HEIGHT
        )
        if [[ -n "$TIMEOUT" ]]; then
            ENTRY_ARGS+=(--timeout="$TIMEOUT")
        fi
        if [[ -n "$DEFAULT_VALUE" ]]; then
            ENTRY_ARGS+=(--entry-text="$DEFAULT_VALUE")
        fi
        zenity "${ENTRY_ARGS[@]}" 2>/dev/null
        ;;
    
    list)
        LIST_ARGS=(
            --list
            --title="$TITLE"
            --text="$MESSAGE"
            --width=$WIDTH
            --height=$((HEIGHT + ${#LIST_ITEMS[@]} * 30))
            --column="Option"
        )
        if [[ -n "$TIMEOUT" ]]; then
            LIST_ARGS+=(--timeout="$TIMEOUT")
        fi
        for item in "${LIST_ITEMS[@]}"; do
            LIST_ARGS+=("$item")
        done
        zenity "${LIST_ARGS[@]}" 2>/dev/null
        ;;
    
    scale)
        zenity --scale \
            --title="$TITLE" \
            --text="$MESSAGE" \
            --min-value="$SCALE_MIN" \
            --max-value="$SCALE_MAX" \
            --value="$SCALE_DEFAULT" \
            --width=$WIDTH \
            $TIMEOUT_ARGS \
            2>/dev/null
        ;;
    
    file)
        zenity --file-selection \
            --title="$TITLE" \
            --width=$WIDTH \
            --height=$HEIGHT \
            $TIMEOUT_ARGS \
            2>/dev/null
        ;;
    
    progress)
        zenity --progress \
            --title="$TITLE" \
            --text="$MESSAGE" \
            --width=$WIDTH \
            --pulsate \
            $TIMEOUT_ARGS \
            2>/dev/null
        ;;
    
    *)
        echo "Error: No dialog type specified" >&2
        usage
        exit 1
        ;;
esac

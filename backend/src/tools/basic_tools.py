from langchain_core.tools import tool
from datetime import datetime
import pytz
import webbrowser


@tool
def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in a specific timezone.
    
    Args:
        timezone: Timezone name (e.g., 'UTC', 'America/New_York', 'Asia/Kolkata')
    
    Returns:
        Current time as a formatted string
    """
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime("%I:%M %p, %B %d, %Y")
    except Exception as e:
        return f"Error getting time: {str(e)}"
    
@tool
def open_url(link: str) -> str:
    """Open a URL in the default browser."""
    try:
        webbrowser.open(link)
        return f"Opened: {link}"
    except Exception as e:
        return f"Failed to open {link}: {e}"
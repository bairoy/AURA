from src.tools.basic_tools import get_current_time

# Test the tool
result = get_current_time.invoke({"timezone": "Asia/Kolkata"})
print(f"Current time in Kolkata: {result}")

result_utc = get_current_time.invoke({"timezone": "UTC"})
print(f"Current time in UTC: {result_utc}")
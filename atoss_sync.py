import pdfplumber
import re
import subprocess
import sys
import os
from datetime import datetime, timedelta

CALENDAR_NAME = "Arbeit"
USER_NAME = "Becker A."

def run_applescript(script):
    """Runs an AppleScript command."""
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    err_str = err.decode('utf-8').strip()
    if err_str:
        print(f"AppleScript Error: {err_str}", file=sys.stderr)
    return out.decode('utf-8'), err.decode('utf-8')

def get_applescript_date_def(var_name, dt):
    """Generates AppleScript lines to set a date variable locale-independently."""
    total_seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
    return f'''
    set {var_name} to (current date)
    set day of {var_name} to 1
    set year of {var_name} to {dt.year}
    set month of {var_name} to {dt.month}
    set day of {var_name} to {dt.day}
    set time of {var_name} to {total_seconds}
    '''

def add_to_calendar(summary, start_dt, end_dt):
    """Adds an event to Apple Calendar via AppleScript."""
    start_date_def = get_applescript_date_def("eventStartDate", start_dt)
    end_date_def = get_applescript_date_def("eventEndDate", end_dt)
    
    script = f'''
    set calendarName to "{CALENDAR_NAME}"
    set eventSummary to "{summary}"
    {start_date_def}
    {end_date_def}
    
    tell application "Calendar"
        if exists (calendar calendarName) then
            set targetCalendar to calendar calendarName
            tell targetCalendar
                make new event at end of events with properties {{summary:eventSummary, start date:eventStartDate, end date:eventEndDate}}
            end tell
        end if
    end tell
    '''
    run_applescript(script)

def clear_calendar_range(start_range, end_range):
    """Deletes existing events in the 'Arbeit' calendar within the given range."""
    start_date_def = get_applescript_date_def("rangeStart", start_range)
    end_date_def = get_applescript_date_def("rangeEnd", end_range)
    
    script = f'''
    set calendarName to "{CALENDAR_NAME}"
    {start_date_def}
    {end_date_def}
    
    tell application "Calendar"
        if exists (calendar calendarName) then
            set targetCalendar to calendar calendarName
            tell targetCalendar
                delete (every event whose (start date is greater than or equal to rangeStart) and (start date is less than or equal to rangeEnd))
            end tell
        end if
    end tell
    '''
    run_applescript(script)

def parse_pdf(pdf_path):
    all_shifts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            
            # The first row with dates is usually the header
            # Look for the row that contains date patterns like "DD.MM.YY"
            header_row = None
            for row in table:
                if any(re.search(r'\d{2}\.\d{2}\.\d{2}', str(cell)) for cell in row if cell):
                    header_row = row
                    break
            
            if not header_row:
                continue
            
            # Extract dates from header and map them to their corresponding weekday/shift columns
            dates = [None] * len(header_row)
            for idx, cell in enumerate(header_row):
                if not cell:
                    continue
                match = re.search(r'(\d{2}\.\d{2}\.\d{2,4})', cell)
                if match:
                    date_str = match.group(1)
                    try:
                        # Handle both YY and YYYY
                        if len(date_str.split('.')[-1]) == 2:
                            parsed_date = datetime.strptime(date_str, "%d.%m.%y")
                        else:
                            parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
                        
                        # The date cell is at idx. The shift cell is at idx - 2.
                        # Map both to this date to ensure alignment works.
                        dates[idx] = parsed_date
                        if idx >= 2:
                            dates[idx - 2] = parsed_date
                    except ValueError:
                        pass
            
            # Find the user's row
            user_row = None
            for row in table:
                if row and any(USER_NAME in str(cell) for cell in row if cell):
                    user_row = row
                    break
            
            if not user_row:
                continue
            
            # Match shifts to dates
            for i, cell in enumerate(user_row):
                if i >= len(dates) or dates[i] is None:
                    continue
                
                if cell is None:
                    continue
                
                cell_text = str(cell).strip()
                if not cell_text or "frei" in cell_text.lower() or "abwesend" in cell_text.lower():
                    continue
                
                # Format: "TS 15:00-23:00" or "TS 16:00-00*45"
                # Pattern: Type (optional) HH:MM - HH:MM or HH*MM
                match = re.search(r'(\d{2}[:*]\d{2})-(\d{2}[:*]\d{2})', cell_text.replace(' ', ''))
                if match:
                    start_time_str = match.group(1).replace('*', ':')
                    end_time_str = match.group(2).replace('*', ':')
                    
                    start_dt = dates[i].replace(hour=int(start_time_str.split(':')[0]), minute=int(start_time_str.split(':')[1]))
                    
                    end_hour = int(end_time_str.split(':')[0])
                    end_min = int(end_time_str.split(':')[1])
                    end_dt = dates[i].replace(hour=end_hour, minute=end_min)
                    
                    # Check if cross-day (end time < start time OR explicit '*' mentioned in original text)
                    if end_dt <= start_dt or '*' in match.group(2):
                        end_dt += timedelta(days=1)
                    
                    all_shifts.append({
                        'summary': cell_text,
                        'start': start_dt,
                        'end': end_dt
                    })
    
    return all_shifts

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python atoss_sync.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)
        
    shifts = parse_pdf(pdf_path)
    
    if not shifts:
        print("No shifts found for " + USER_NAME)
        sys.exit(0)
    
    # Clear range from first start to last end (plus a little buffer)
    min_date = min(s['start'] for s in shifts) - timedelta(days=1)
    max_date = max(s['end'] for s in shifts) + timedelta(days=1)
    
    print(f"Clearing calendar {CALENDAR_NAME} from {min_date} to {max_date}...")
    clear_calendar_range(min_date, max_date)
    
    print(f"Adding {len(shifts)} shifts...")
    for s in shifts:
        print(f"Adding: {s['summary']} ({s['start']} - {s['end']})")
        add_to_calendar(s['summary'], s['start'], s['end'])
    
    print("Done!")

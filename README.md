# ATOSS to Apple Calendar Sync

A zero-click automation tool that automatically parses ATOSS schedule PDFs from your incoming emails and synchronizes them with your Apple Calendar on macOS.

---

## Features

- **Automated Workflow:** Detects incoming emails with PDF schedules, downloads them, parses shifts, and inserts them into your Calendar.
- **Robust PDF Parsing:** Handles grouped/merged shift grids in the PDF, correctly matching shift times to the correct dates.
- **Nightshift Support:** Correctly handles shifts extending past midnight (e.g. `18:00-00*45`).
- **Clean Syncing:** Deletes old entries in the synchronized range prior to writing to prevent duplicates.
- **Locale-Independent AppleScript:** Uses a native, locale-independent date construction method in AppleScript to avoid formatting issues on German or other non-US system language settings.

---

## Setup Guide

### 1. Requirements

- **macOS**
- **Apple Mail**
- **Apple Calendar** (A calendar named `Arbeit` must exist)
- **Python 3**

---

### 2. Python Virtual Environment Setup

Initialize the virtual environment inside the repository folder:

```bash
cd /Users/artjombecker/GitHub/atoss-sync
python3 -m venv venv
source venv/bin/activate
pip install pdfplumber
```

---

### 3. AppleScript Compilation & Placement

The script triggers the Python environment when a mail matches your rule. Save/compile the script as `AtossMailRule.scpt` into the Apple Mail scripts directory:

```bash
mkdir -p ~/Library/Application\ Scripts/com.apple.mail/
osacompile -o ~/Library/Application\ Scripts/com.apple.mail/AtossMailRule.scpt AtossMailRule.applescript
```

---

### 4. Setting up the Apple Mail Rule

1. Open **Apple Mail** on your Mac.
2. Go to **Mail** -> **Settings...** (or **Preferences...**) -> **Rules**.
3. Click **Add Rule**.
4. Set description to `ATOSS Sync`.
5. Set conditions (e.g., *If **any** of the following conditions are met: **From** is [Supervisor's email]*).
6. Under **Perform the following actions**, select **Run AppleScript** and choose **`AtossMailRule`** from the dropdown menu.
7. Click **OK**.

---

## Troubleshooting

- **No entries in Calendar?**
  - Verify that the calendar **`Arbeit`** exists in Apple Calendar.
  - Manually test by right-clicking a matching email in Apple Mail and clicking **Apply Rules**.
  - Check the directory `~/Downloads/atoss_temp/` to see if the PDF was downloaded.

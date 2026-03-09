# COMPAT Ticket Status Analyzer

A Streamlit dashboard for analyzing COMPAT Jira tickets and tracking time spent in the TESTING status.

## Features

- Filter tickets by creation date range and current status
- Track how long each ticket spent in TESTING
- Export results to CSV

## How to Use

1. Select your desired date range for when tickets were created.
2. Choose which statuses to include in the analysis.
3. Click `Run Analysis` to see the results.
4. Click the `Download` button once the query is complete.

## CSV Output

The exported CSV includes:

- Ticket number and title
- Created date
- Total time in TESTING (hours)
- Current status
- First entered / last left TESTING timestamps
- Number of times entered TESTING

A value of `-1` for test time indicates the ticket is currently in TESTING.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your Jira API key:

   ```bash
   export JIRA_API_KEY=your_api_key_here
   ```

    or write the API key to a file called `JIRA_API_KEY.txt` in the project root directory.

3. Run the app:

   ```bash
   streamlit run compat_status_analyzer.py
   ```

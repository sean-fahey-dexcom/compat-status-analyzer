# COMPAT & GARY Ticket Status Analyzer

A Streamlit dashboard for analyzing COMPAT and GARY Jira tickets and tracking time spent in various statuses (excluding weekends).

## Features

- Switch between COMPAT and GARY dashboards via navigation sidebar
- Filter tickets by creation date range and current status
- Track how long each ticket spent in multiple tracked statuses (excluding weekends)
- Export results to CSV

## How to Use

1. Select the COMPAT or GARY dashboard from the sidebar navigation.
2. Select your desired date range for when tickets were created.
3. Choose which statuses to filter by in the current status filter.
4. Click `Submit` to execute the query and view metrics.
5. Click the `Download CSV` button once the query is complete.

## CSV Output

The exported CSV includes:

- Ticket number and title
- Assignee
- Created date
- Current status
- Work-week hours spent in each tracked status
- Number of times entered each tracked status

A value of `-1` for work-week hours indicates the ticket is currently in that status.

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

"""Entrypoint for the streamlit app."""

import csv
import io
from datetime import datetime

import streamlit as st

from utils.jira_connector import JiraConnection
from utils.streamlit_common import (
    COMPAT_STATUSES_TO_TRACK,
    GARY_STATUSES_TO_TRACK,
    compat_status_selector,
    date_selector,
    gary_status_selector,
    get_key,
)


def csv_writer(issues_metrics, statuses_to_track, project_name):
    """Generate CSV from issues metrics and provide download button."""
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)

    # Base headers
    headers = [
        f"{project_name} Ticket Number",
        "Title",
        "Assignee",
        "Created Date",
        "Current Status",
    ]

    # Dynamic headers for each tracked status
    for status in statuses_to_track:
        headers.extend(
            [
                f"{status} (Work Week Hours)",
                f"# Times Entered {status}",
            ]
        )
    writer.writerow(headers)

    for issue_key, metrics in issues_metrics.items():
        row = [
            issue_key,
            metrics["ticket_title"],
            metrics["assignee"],
            metrics["ticket_created_date"],
            metrics["current_status"],
        ]
        for status in statuses_to_track:
            status_metrics = metrics["status_metrics"].get(status, {})
            row.extend(
                [
                    status_metrics.get("work_week_hours", 0),
                    status_metrics.get("entry_count", 0),
                ]
            )
        writer.writerow(row)

    csv_data = csv_buffer.getvalue()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_name}_issues_metrics_{timestamp}.csv"

    st.download_button(label="Download CSV", data=csv_data, file_name=filename, mime="text/csv")


def compat_homepage():
    """Main function for the Streamlit app COMPAT homepage."""
    st.title("COMPAT Ticket Status Dashboard")

    aki_key = get_key()
    if not aki_key:
        return

    start_date, end_date = date_selector()
    st.divider()

    selected_statuses = compat_status_selector()
    st.divider()

    if st.button("Submit"):
        if not selected_statuses:
            st.warning("Please select at least one status to filter by.")
            return

        jira = JiraConnection(token=aki_key)
        query = jira.build_query(
            project="COMPAT", start_date=start_date, end_date=end_date, allowed_statuses=selected_statuses
        )
        clean_query = query.replace("\\", "")
        st.write(f"Executing JQL query: `{clean_query}`")

        issues_metrics = process_issues(jira, query, COMPAT_STATUSES_TO_TRACK, "COMPAT")
        if issues_metrics:
            csv_writer(issues_metrics, COMPAT_STATUSES_TO_TRACK, "COMPAT")


def gary_homepage():
    """Main function for the Streamlit app GARY homepage."""
    st.title("GARY Ticket Status Dashboard")

    aki_key = get_key()
    if not aki_key:
        return

    start_date, end_date = date_selector()
    st.divider()

    selected_statuses = gary_status_selector()
    st.divider()

    if st.button("Submit"):
        if not selected_statuses:
            st.warning("Please select at least one status to filter by.")
            return

        jira = JiraConnection(token=aki_key)
        query = jira.build_query(
            project="GARY", start_date=start_date, end_date=end_date, allowed_statuses=selected_statuses
        )
        clean_query = query.replace("\\", "")
        st.write(f"Executing JQL query: `{clean_query}`")

        issues_metrics = process_issues(jira, query, GARY_STATUSES_TO_TRACK, "GARY")
        if issues_metrics:
            csv_writer(issues_metrics, GARY_STATUSES_TO_TRACK, "GARY")


def process_issues(jira, query, statuses_to_track, project_name):
    """Fetch and process issues from Jira."""
    all_issues = []
    progress_text = st.empty()
    with st.spinner("Fetching issues from Jira..."):
        for issue, total_fetched in jira.search_issues(query):
            all_issues.append(issue)
            progress_text.text(f"Found {total_fetched} issues so far...")

    if not all_issues:
        progress_text.text("")
        st.warning("No issues found matching the criteria.")
        return None

    progress_text.text("")
    st.success(f"Found {len(all_issues)} issues matching the search parameters.")
    progress_bar = st.progress(0, text=f"Extracting status history from {project_name} tickets...")

    issues_metrics = {}
    for idx, issue in enumerate(all_issues):
        metrics = jira.get_status_metrics(issue, statuses_to_track)
        issues_metrics[issue.key] = metrics
        progress_bar.progress(
            (idx + 1) / len(all_issues), text=f"Extracting status history from {project_name} tickets..."
        )

    progress_bar.empty()
    return issues_metrics


if __name__ == "__main__":
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Dashboard", ["COMPAT", "GARY"])

    if page == "COMPAT":
        compat_homepage()
    else:
        gary_homepage()

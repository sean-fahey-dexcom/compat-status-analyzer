"""Entrypoint for the streamlit app."""

import csv
import io
from datetime import date, datetime, timedelta

import streamlit as st

from utils.jira_connector import JiraConnection
from utils.utils import get_jira_api_key


def date_selector():
    """Date range selector for ticket created date."""
    st.subheader("Ticket Created Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", value=date.today())

    return start_date, end_date


def status_selector():
    """Status selector with checkboxes."""
    header_col, btn_col1, btn_col2, _ = st.columns([2, 1, 1, 1])

    with header_col:
        st.subheader("Current Status Filter")
    status_options = (
        ("Triage", False),
        ("Pre-Test Review", False),
        ("Testing", False),
        ("Post-Test Review", True),
        ("Ready for Cloud PLM", True),
        ("Submitted in Cloud PLM", True),
        ("Implement Deliverable", True),
        ("QA Close Review", True),
        ("COMPLETED", True),
        ("Cancelled", False),
    )

    # Initialize session state for checkboxes if not exists
    for opt_name, opt_default in status_options:
        if f"cb_{opt_name}" not in st.session_state:
            st.session_state[f"cb_{opt_name}"] = opt_default

    # Select All / Deselect All buttons
    with btn_col1:
        if st.button("Select All"):
            for opt_name, _ in status_options:
                st.session_state[f"cb_{opt_name}"] = True
            st.rerun()
    with btn_col2:
        if st.button("Deselect All"):
            for opt_name, _ in status_options:
                st.session_state[f"cb_{opt_name}"] = False
            st.rerun()

    selected_statuses = []
    num_columns = 3
    columns = st.columns(num_columns)
    for idx, option in enumerate(status_options):
        with columns[idx % num_columns]:
            if st.checkbox(option[0], key=f"cb_{option[0]}"):
                selected_statuses.append(option[0])

    return selected_statuses


def csv_writer(issues_metrics):
    """Generate CSV from issues metrics and provide download button."""
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(
        [
            "COMPAT Ticket Number",
            "Title",
            "Created Date",
            "Total Test Time (Hours)",
            "Current Status",
            "First Entered TESTING",
            "Last Left TESTING",
            "# Times Entered TESTING",
        ]
    )
    for issue_key, metrics in issues_metrics.items():
        writer.writerow(
            [
                issue_key,
                metrics["ticket_title"],
                metrics["ticket_created_date"],
                metrics["total_testing_time_hours"],
                metrics["current_status"],
                metrics["first_entered_testing"],
                metrics["last_exited_testing"],
                metrics["times_entered_testing"],
            ]
        )

    csv_data = csv_buffer.getvalue()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"issues_metrics_{timestamp}.csv"

    st.download_button(label="Download CSV", data=csv_data, file_name=filename, mime="text/csv")


def homepage():
    """Main function for the Streamlit app homepage."""
    st.title("COMPAT Ticket Status Dashboard")

    aki_key = get_jira_api_key()
    if not aki_key:
        st.error(
            "JIRA_API_KEY environment variable is not set. Please set it to access the dashboard and reload the page."
        )
        return

    start_date, end_date = date_selector()
    st.divider()

    # Status selector with checkboxes
    selected_statuses = status_selector()
    st.divider()

    if st.button("Submit"):
        if selected_statuses == []:
            st.warning("Please select at least one status to filter by.")
            return

        jira = JiraConnection(token=aki_key)

        all_issues = []
        query = jira.build_query(start_date=start_date, end_date=end_date, allowed_statuses=selected_statuses)
        clean_query = query.replace("\\", "")
        st.write(f"Executing JQL query: `{clean_query}`")

        progress_text = st.empty()
        with st.spinner("Fetching issues from Jira..."):
            for issue, total_fetched in jira.search_issues(query):
                all_issues.append(issue)
                progress_text.text(f"Found {total_fetched} issues so far...")

        if all_issues:
            progress_text.text("")
            st.success(f"Found {len(all_issues)} issues matching the search parameters.")
            progress_bar = st.progress(0, text="Extracting status history from tickets...")

            issues_metrics = {}
            for idx, issue in enumerate(all_issues):
                (
                    first_entered_testing,
                    last_exited_testing,
                    times_entered_testing,
                    total_testing_time_hours,
                    current_status,
                    ticket_title,
                    ticket_created_date,
                ) = jira.get_testing_status_metrics(issue)
                issues_metrics[issue.key] = {}
                issues_metrics[issue.key]["first_entered_testing"] = first_entered_testing
                issues_metrics[issue.key]["last_exited_testing"] = last_exited_testing
                issues_metrics[issue.key]["times_entered_testing"] = times_entered_testing
                issues_metrics[issue.key]["total_testing_time_hours"] = total_testing_time_hours
                issues_metrics[issue.key]["current_status"] = current_status
                issues_metrics[issue.key]["ticket_title"] = ticket_title
                issues_metrics[issue.key]["ticket_created_date"] = ticket_created_date
                progress_bar.progress((idx + 1) / len(all_issues), text="Extracting status history from tickets...")

            progress_bar.empty()
            csv_writer(issues_metrics)

        else:
            progress_text.text("")
            st.warning("No issues found matching the criteria.")


if __name__ == "__main__":
    homepage()

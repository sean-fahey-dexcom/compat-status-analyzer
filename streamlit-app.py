"""Entrypoint for the streamlit app."""

import csv
import io
from datetime import date, datetime, timedelta

import streamlit as st

from utils.jira_connector import JiraConnection
from utils.utils import get_jira_api_key


def homepage():
    """Main function for the Streamlit app homepage."""
    st.title("COMPAT Ticket Status Dashboard")

    aki_key = get_jira_api_key()
    if not aki_key:
        st.error(
            "JIRA_API_KEY environment variable is not set. Please set it to access the dashboard and reload the page."
        )
        return

    # Date range selector
    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", value=date.today())

    # Status selector with checkboxes
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
    selected_statuses = []
    num_columns = 3
    columns = st.columns(num_columns)
    for idx, option in enumerate(status_options):
        with columns[idx % num_columns]:
            if st.checkbox(option[0], value=option[1], key=option[0]):
                selected_statuses.append(option[0])

    if st.button("Submit"):
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
                metrics = jira.get_testing_status_metrics(issue)
                issues_metrics[issue.key] = metrics
                progress_bar.progress((idx + 1) / len(all_issues), text="Extracting status history from tickets...")

            progress_bar.empty()

            # Generate CSV
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(
                [
                    "COMPAT Ticket Number",
                    "Title",
                    "Total Test Time (Hours)",
                    "Current Status",
                    "First Entered TESTING",
                    "Last Left TESTING",
                    "# Times Entered TESTING",
                ]
            )
            for issue_key, metrics in issues_metrics.items():
                writer.writerow([issue_key, metrics[5], metrics[3], metrics[4], metrics[0], metrics[1], metrics[2]])

            csv_data = csv_buffer.getvalue()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"issues_metrics_{timestamp}.csv"

            st.download_button(label="Download CSV", data=csv_data, file_name=filename, mime="text/csv")

        else:
            progress_text.text("")
            st.info("No issues found matching the criteria.")


if __name__ == "__main__":
    homepage()

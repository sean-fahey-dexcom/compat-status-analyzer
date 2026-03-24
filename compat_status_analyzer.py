"""Entrypoint for the streamlit app."""

import csv
import io
from datetime import datetime

import streamlit as st

from utils.jira_connector import JiraConnection
from utils.streamlit_common import compat_status_selector, date_selector, gary_status_selector, get_key


def csv_writer(issues_metrics):
    """Generate CSV from issues metrics and provide download button."""
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(
        [
            "COMPAT Ticket Number",
            "Title",
            "Assignee",
            "Created Date",
            "Total Test Time (Hours)",
            "Work Week Test Time (Hours)",
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
                metrics["assignee"],
                metrics["ticket_created_date"],
                metrics["total_testing_time_hours"],
                metrics["work_week_testing_time_hours"],
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


def compat_homepage():
    """Main function for the Streamlit app COMPAT homepage."""
    st.title("COMPAT Ticket Status Dashboard")

    aki_key = get_key()
    if not aki_key:
        return

    start_date, end_date = date_selector()
    st.divider()

    # Status selector with checkboxes
    selected_statuses = compat_status_selector()
    st.divider()

    if st.button("Submit"):
        if selected_statuses == []:
            st.warning("Please select at least one status to filter by.")
            return

        jira = JiraConnection(token=aki_key)

        all_issues = []
        query = jira.build_query(
            project="COMPAT", start_date=start_date, end_date=end_date, allowed_statuses=selected_statuses
        )
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
                    work_week_testing_time_hours,
                    current_status,
                    ticket_title,
                    ticket_created_date,
                    assignee,
                ) = jira.get_testing_status_metrics(issue)
                issues_metrics[issue.key] = {}
                issues_metrics[issue.key]["first_entered_testing"] = first_entered_testing
                issues_metrics[issue.key]["last_exited_testing"] = last_exited_testing
                issues_metrics[issue.key]["times_entered_testing"] = times_entered_testing
                issues_metrics[issue.key]["total_testing_time_hours"] = total_testing_time_hours
                issues_metrics[issue.key]["work_week_testing_time_hours"] = work_week_testing_time_hours
                issues_metrics[issue.key]["current_status"] = current_status
                issues_metrics[issue.key]["ticket_title"] = ticket_title
                issues_metrics[issue.key]["ticket_created_date"] = ticket_created_date
                issues_metrics[issue.key]["assignee"] = assignee
                progress_bar.progress((idx + 1) / len(all_issues), text="Extracting status history from tickets...")

            progress_bar.empty()
            csv_writer(issues_metrics)

        else:
            progress_text.text("")
            st.warning("No issues found matching the criteria.")


def gary_homepage():
    """Main function for the Streamlit app GARY homepage."""
    st.title("GARY Ticket Status Dashboard")

    aki_key = get_key()
    if not aki_key:
        return

    start_date, end_date = date_selector()
    st.divider()

    # Status selector with checkboxes
    selected_statuses = gary_status_selector()
    st.divider()

    if st.button("Submit"):
        if selected_statuses == []:
            st.warning("Please select at least one status to filter by.")
            return

        jira = JiraConnection(token=aki_key)

        all_issues = []
        query = jira.build_query(
            project="GARY", start_date=start_date, end_date=end_date, allowed_statuses=selected_statuses
        )
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
                    work_week_testing_time_hours,
                    current_status,
                    ticket_title,
                    ticket_created_date,
                    assignee,
                ) = jira.get_testing_status_metrics(issue)
                issues_metrics[issue.key] = {}
                issues_metrics[issue.key]["first_entered_testing"] = first_entered_testing
                issues_metrics[issue.key]["last_exited_testing"] = last_exited_testing
                issues_metrics[issue.key]["times_entered_testing"] = times_entered_testing
                issues_metrics[issue.key]["total_testing_time_hours"] = total_testing_time_hours
                issues_metrics[issue.key]["work_week_testing_time_hours"] = work_week_testing_time_hours
                issues_metrics[issue.key]["current_status"] = current_status
                issues_metrics[issue.key]["ticket_title"] = ticket_title
                issues_metrics[issue.key]["ticket_created_date"] = ticket_created_date
                issues_metrics[issue.key]["assignee"] = assignee
                progress_bar.progress((idx + 1) / len(all_issues), text="Extracting status history from tickets...")

            progress_bar.empty()
            csv_writer(issues_metrics)

        else:
            progress_text.text("")
            st.warning("No issues found matching the criteria.")


if __name__ == "__main__":
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Dashboard", ["COMPAT", "GARY"])

    if page == "COMPAT":
        compat_homepage()
    else:
        gary_homepage()

"""Shared streamlit rendering functions."""

from datetime import date, timedelta

import streamlit as st

from utils.utils import get_jira_api_key

COMPAT_STATUSES_TO_TRACK = [
    "TESTING",
    "POST-TEST REVIEW",
    "READY FOR CLOUD PLM",
    "SUBMITTED IN CLOUD PLM",
    "IMPLEMENT DELIVERABLE",
    "QA CLOSE REVIEW",
]

GARY_STATUSES_TO_TRACK = [
    "TESTING",
    "POST-TEST REVIEW",
    "SUBMITTED IN CLOUD PLM",
    "IMPLEMENTED",
]


def get_key():
    """Fetch the Jira API key from the JIRA_API_KEY environment variable."""
    aki_key = get_jira_api_key()
    if not aki_key:
        st.error(
            "JIRA_API_KEY environment variable is not set. Please set it to access the dashboard and reload the page."
        )
        return None
    return aki_key


def date_selector():
    """Date range selector for ticket created date."""
    st.subheader("Ticket Created Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", value=date.today())

    return start_date, end_date


def common_status_selector(status_options):
    """Status selector with checkboxes."""
    header_col, btn_col1, btn_col2, _ = st.columns([2, 1, 1, 1])

    with header_col:
        st.subheader("Current Status Filter")

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


def compat_status_selector():
    """Status selector for COMPAT app."""
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
    return common_status_selector(status_options)


def gary_status_selector():
    """Status selector for GARY app."""
    status_options = (
        ("Open", False),
        ("Testing", False),
        ("Post-Test Review", True),
        ("Submitted in Cloud PLM", True),
        ("Implemented", True),
        ("COMPLETED", True),
        ("Cancelled", False),
    )
    return common_status_selector(status_options)

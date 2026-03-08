"""Utility functions for the COMPAT Status Analyzer project."""

import os


def get_jira_api_key() -> str:
    """Fetch the Jira API key from the JIRA_API_KEY environment variable."""
    api_key = os.environ.get("JIRA_API_KEY")
    if not api_key:
        try:
            with open("JIRA_API_KEY.txt") as file:
                api_key = file.read().strip()
        except FileNotFoundError:
            pass
    return api_key

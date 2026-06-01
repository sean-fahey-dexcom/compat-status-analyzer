"""Jira connection handler."""

from datetime import date, datetime, timedelta

import numpy as np
from jira import JIRA


class JiraConnection:
    """Manages the connection with Jira."""

    def __init__(self, token: str):
        """Initialize the Jira connection with authentication.

        Args:
            token (str): The API token for authentication.

        Raises:
            JIRAError: If authentication fails or connection cannot be established.

        """
        self.jira = JIRA(server="https://jira.dexcom.com", token_auth=token)

    @staticmethod
    def build_query(project: str, start_date: date, end_date: date, allowed_statuses: list) -> str:
        """Build a JQL query string based on the provided parameters.

        Args:
            project (str): The Jira project key to search within.
            start_date (date): The start date for the search.
            end_date (date): The end date for the search.
            allowed_statuses (list): List of allowed issue statuses to filter the search.

        Returns:
            str: The constructed JQL query string.

        """
        allowed_statuses_sanitized = [status.replace(" ", r"\ ") for status in allowed_statuses]
        return f'project = {project} AND created >= "{start_date.strftime("%Y-%m-%d")}" AND created <= "{end_date.strftime("%Y-%m-%d")}" AND status IN ({",".join(allowed_statuses_sanitized)})'

    @staticmethod
    def calculate_work_week_hours(start_dt: datetime, end_dt: datetime) -> float:
        """Calculate the number of hours between two datetime objects, excluding weekends."""
        if start_dt >= end_dt:
            return 0.0

        start_date = start_dt.date()
        end_date = end_dt.date()

        # Case 1: Same day
        if start_date == end_date:
            if start_date.weekday() < 5:  # It's a weekday
                return (end_dt - start_dt).total_seconds() / 3600
            return 0.0

        # Case 2: Different days
        # Calculate full business days between the start and end dates
        # np.busday_count excludes the end date, so we add one day to end_date for inclusion
        num_business_days = np.busday_count(start_date, end_date + timedelta(days=1))

        # Start with total business days * 24 hours
        total_hours = num_business_days * 24.0

        # Adjust for the first day
        if start_date.weekday() < 5:
            # It's a weekday, so we've counted it as a full 24h day.
            # We need to subtract the hours that passed before start_dt
            start_of_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            total_hours -= (start_dt - start_of_day).total_seconds() / 3600

        # Adjust for the last day
        if end_date.weekday() < 5:
            # It's a weekday, so we've counted it as a full 24h day.
            # We need to subtract the hours from end_dt until the end of the day.
            end_of_day = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            total_hours -= (end_of_day - end_dt).total_seconds() / 3600

        return total_hours

    def search_issues(self, query: str, max_results_per_page: int = 50):
        """Search for existing DCI issues within a specified date range and matching allowed statuses.

        Args:
            query (str): The JQL query string to execute.
            max_results_per_page (int): Maximum number of results to fetch per page. Defaults to 50.

        Yields:
            tuple: (issue, total_fetched_so_far) for each issue found. Issues include changelog.

        """
        print(f"Searching issues with JQL: '{query}'")

        start_at = 0
        total_fetched = 0

        while True:
            issues = self.jira.search_issues(
                query, startAt=start_at, maxResults=max_results_per_page, expand="changelog"
            )
            if not issues:
                break

            for issue in issues:
                total_fetched += 1
                yield issue, total_fetched

            print(f"Fetched batch of {len(issues)} issues (total: {total_fetched})")

            if len(issues) < max_results_per_page:
                break

            start_at += max_results_per_page

        if total_fetched == 0:
            print("No issues found.")

    def get_status_metrics(self, issue, statuses_to_track):
        """Get metrics for time spent in various statuses for an issue.

        Args:
            issue: The Jira issue object (must have changelog expanded).
            statuses_to_track (list): A list of uppercase status names to track.

        Returns:
            dict: A dictionary containing ticket information and metrics for each tracked status.
                - 'ticket_title': Issue summary/title
                - 'ticket_created_date': When the ticket was created
                - 'assignee': Assignee display name or "Unassigned"
                - 'current_status': Current status of the issue
                - 'status_metrics': A nested dictionary where keys are the tracked statuses and
                                    values are dicts with:
                                    - 'total_hours': Total time in the status (float, -1 if ongoing)
                                    - 'work_week_hours': Work-week time in the status (float, -1 if ongoing)
                                    - 'entry_count': Number of times the status was entered (int)
        """
        metrics = {
            "ticket_title": str(issue.fields.summary),
            "ticket_created_date": datetime.fromisoformat(
                issue.fields.created[:-2] + ":" + issue.fields.created[-2:]
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "current_status": str(issue.fields.status.name),
            "status_metrics": {
                status: {"total_hours": 0.0, "work_week_hours": 0.0, "entry_count": 0} for status in statuses_to_track
            },
        }

        status_entry_times = {status: None for status in statuses_to_track}

        for history in issue.changelog.histories:
            history_time_str = history.created[:-2] + ":" + history.created[-2:]
            history_time = datetime.fromisoformat(history_time_str)

            for item in history.items:
                if item.field == "status":
                    from_status = str(item.fromString).upper() if item.fromString else ""
                    to_status = str(item.toString).upper() if item.toString else ""

                    # Exited a tracked status
                    if from_status in statuses_to_track and status_entry_times[from_status]:
                        entry_time = status_entry_times[from_status]
                        time_spent = (history_time - entry_time).total_seconds() / 3600
                        work_week_hours = self.calculate_work_week_hours(entry_time, history_time)

                        metrics["status_metrics"][from_status]["total_hours"] += time_spent
                        metrics["status_metrics"][from_status]["work_week_hours"] += work_week_hours
                        status_entry_times[from_status] = None

                    # Entered a tracked status
                    if to_status in statuses_to_track:
                        if not status_entry_times[to_status]:
                            status_entry_times[to_status] = history_time
                            if (
                                from_status != to_status
                            ):  # Only count entry if it's a status change, not a history update where status stays the same
                                metrics["status_metrics"][to_status]["entry_count"] += 1

        # Check if the issue is currently in any of the tracked statuses
        current_status_upper = metrics["current_status"].upper()
        if current_status_upper in statuses_to_track:
            metrics["status_metrics"][current_status_upper]["total_hours"] = -1
            metrics["status_metrics"][current_status_upper]["work_week_hours"] = -1

        return metrics

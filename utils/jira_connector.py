"""Jira connection handler."""

from datetime import date, datetime

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

    def get_testing_status_metrics(self, issue):
        """Get metrics for time spent in TESTING status for an issue.

        Args:
            issue: The Jira issue object (must have changelog expanded).

        Returns:
            tuple: (first_entered_testing, last_finished_testing, times_entered_testing, total_testing_time_hours, current_status, ticket_title, created_date, assignee)
                - first_entered_testing (datetime | None): When issue first entered TESTING
                - last_finished_testing (datetime | None): When issue last left TESTING
                - times_entered_testing (int): Number of times issue entered TESTING
                - total_testing_time_hours (float): Total time in TESTING in hours (-1 if still in TESTING)
                - current_status (str): Current status of the issue
                - ticket_title (str): Issue summary/ticket_title
                - ticket_created_date (str): When the ticket was created
                - assignee (str): Assignee display name or "Unassigned"

        """
        first_entered_testing = None
        last_finished_testing = None
        times_entered_testing = 0
        total_testing_time_hours = 0.0
        currently_in_testing = False
        entered_at = None

        # Check if issue was created in TESTING status
        # We need to check for this edge case by looking at the first status transition
        current_status = str(issue.fields.status.name)
        ticket_title = str(issue.fields.summary)
        # Parse created date from Jira format
        ticket_created_str = issue.fields.created[:-2] + ":" + issue.fields.created[-2:]
        ticket_created_date = datetime.fromisoformat(ticket_created_str).strftime("%Y-%m-%d %H:%M:%S")
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"

        for history in issue.changelog.histories:
            # Jira format: '2026-03-06T10:05:07.020+0000' -> need '+00:00'
            created_str = history.created[:-2] + ":" + history.created[-2:]
            history_time = datetime.fromisoformat(created_str)

            for item in history.items:
                if item.field == "status":
                    from_status = str(item.fromString).upper() if item.fromString else ""
                    to_status = str(item.toString).upper() if item.toString else ""

                    # Entered TESTING
                    if to_status == "TESTING" and from_status != "TESTING":
                        times_entered_testing += 1
                        entered_at = history_time
                        currently_in_testing = True
                        if first_entered_testing is None:
                            first_entered_testing = history_time

                    # Left TESTING
                    elif from_status == "TESTING" and to_status != "TESTING":
                        if entered_at is not None:
                            total_testing_time_hours += (history_time - entered_at).total_seconds() / 3600
                        last_finished_testing = history_time
                        currently_in_testing = False
                        entered_at = None

        # If still in TESTING, return -1 for total time
        if currently_in_testing or current_status.upper() == "TESTING":
            total_testing_time_hours = -1

        return (
            first_entered_testing.strftime("%Y-%m-%d %H:%M:%S") if first_entered_testing else None,
            last_finished_testing.strftime("%Y-%m-%d %H:%M:%S") if last_finished_testing else None,
            times_entered_testing,
            total_testing_time_hours,
            current_status,
            ticket_title,
            ticket_created_date,
            assignee,
        )

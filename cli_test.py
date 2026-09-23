from __future__ import annotations

import argparse
import os
import tempfile
from typing import Any


def _load_client(fresh: bool):
    if fresh:
        directory = tempfile.TemporaryDirectory(prefix="feedback-watch-tower-cli-")
        database_path = os.path.join(directory.name, "cli.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path.replace(os.sep, '/')}"
        os.environ["OPENROUTER_API_KEY"] = ""

    from app.core.config import get_settings

    get_settings.cache_clear()
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app), locals().get("directory")


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def _show(label: str, value: Any) -> None:
    print(f"{label}: {value}")


class CLIWorkspace:
    def __init__(self, client, verbose: bool = False):
        self.client = client
        self.verbose = verbose
        self.issue_id: int | None = None

    def request(self, method: str, path: str, **kwargs) -> Any:
        if self.verbose:
            print(f"[API] {method.upper()} {path}")
        response = self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            detail = response.json().get("detail", response.text)
            raise RuntimeError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    def submit_feedback(self) -> None:
        _section("REPORTER - SUBMIT FEEDBACK")
        name = input("Reporter name: ").strip()
        contact = input("Reporter contact: ").strip()
        content = input("What is your feedback? ").strip()
        context = input("Optional context: ").strip()
        feedback = self.request(
            "post",
            "/feedback",
            json={
                "name": name,
                "contact": contact,
                "content": content,
                "channel": "cli",
                "context": context or None,
            },
        )
        print("[COLLECTION] Feedback received")
        _show("Feedback ID", feedback["id"])
        _show("Status", feedback["status"])

        analysis_response = self.request("post", f"/feedback/{feedback['id']}/process")
        analysis = analysis_response["analysis"]
        print("[AGENT] Feedback classified")
        _show("Category", analysis["category"])
        _show("Issue type", analysis["issue_type"])
        _show("Priority", analysis["priority"])
        _show("Department", analysis["department"])
        _show("Summary", analysis["summary"])
        _show("Confidence", analysis["confidence"])

        routed = self.request("post", f"/feedback/{feedback['id']}/route")
        issue = routed["issue"]
        self.issue_id = issue["id"]
        print("[ISSUE] Issue created")
        _show("Issue", issue["reference"])
        _show("Status", issue["status"])
        _show("Priority", issue["priority"])
        _show("Department", issue["department"])
        _show("Handler ID", issue["handler_id"])
        print("[ROUTING] Handler assigned")
        notifications = self.request("get", f"/issues/{self.issue_id}/notifications")
        self._show_latest_notification(notifications)

    def handler_workspace(self) -> None:
        _section("HANDLER WORKSPACE")
        issues = self.request("get", "/issues")
        if not issues:
            print("No assigned issues.")
            return
        for issue in issues:
            print(
                f"[{issue['id']}] {issue['reference']} | "
                f"{issue['title']} | {issue['priority']} | {issue['status']}"
            )
        selected = input("Issue ID (blank to back): ").strip()
        if not selected:
            return
        self.issue_id = int(selected)
        while True:
            issue = self.request("get", f"/issues/{self.issue_id}")
            _section(f"ISSUE DETAILS - {issue['reference']}")
            _show("Summary", issue["summary"])
            _show("Status", issue["status"])
            _show("Handler ID", issue["handler_id"])
            print(
                "1. Start work\n2. Complete issue\n3. View timeline\n4. View notifications\n5. Back"
            )
            choice = input("Select: ").strip()
            try:
                if choice == "1":
                    result = self.request("post", f"/issues/{self.issue_id}/start")
                    self._show_transition(result)
                elif choice == "2":
                    resolution = input("Enter resolution: ").strip()
                    result = self.request(
                        "post",
                        f"/issues/{self.issue_id}/complete",
                        json={"resolution": resolution},
                    )
                    self._show_transition(result)
                elif choice == "3":
                    self.show_timeline()
                elif choice == "4":
                    self.show_notifications()
                elif choice == "5":
                    return
            except (RuntimeError, ValueError) as exc:
                self._show_error("Handler operation", exc)

    def reporter_confirmation(self) -> None:
        if self.issue_id is None:
            print("No active issue selected.")
            return
        _section("REPORTER - CONFIRMATION")
        issue = self.request("get", f"/issues/{self.issue_id}")
        _show("Issue", issue["reference"])
        _show("Status", issue["status"])
        _show("Resolution", issue["resolution"])
        choice = input(
            "1. Confirm resolution\n2. Reject resolution\n3. Back\nSelect: "
        ).strip()
        if choice not in {"1", "2"}:
            return
        result = self.request(
            "post",
            f"/issues/{self.issue_id}/confirm",
            json={"confirmed": choice == "1"},
        )
        self._show_transition(result)
        if choice == "1":
            result = self.request("post", f"/issues/{self.issue_id}/close")
            self._show_transition(result)

    def show_timeline(self) -> None:
        if self.issue_id is None:
            print("No active issue selected.")
            return
        detail = self.request("get", f"/qa/issues/{self.issue_id}")
        _section("ISSUE TIMELINE")
        for event in detail["events"]:
            print(
                f"{event['created_at']}  {event['event_type']}: {event['description']}"
            )

    def show_notifications(self) -> None:
        if self.issue_id is None:
            print("No active issue selected.")
            return
        notifications = self.request("get", f"/issues/{self.issue_id}/notifications")
        _section("NOTIFICATIONS")
        for item in notifications:
            print(
                f"[{item['id']}] {item['event_type']} | {item['status']} | "
                f"{item['message']} | {item['created_at']}"
            )

    def qa_workspace(self, interactive: bool = True) -> None:
        while True:
            dashboard = self.request("get", "/qa/dashboard")
            _section("WATCH TOWER")
            _show("Total issues", dashboard["total_issues"])
            print("Issue status:")
            for status, count in dashboard["by_status"].items():
                print(f"  {status}: {count}")
            for issue in dashboard["issues"]:
                print(
                    f"  [{issue['id']}] {issue['reference']} | {issue['status']} | "
                    f"next: {issue['next_action']}"
                )
            if not interactive:
                return
            print(
                "\n1. Recent issues\n2. Open issues\n3. Issue timeline\n"
                "4. Feedback summary\n5. Refresh\n6. Back"
            )
            choice = input("Select: ").strip()
            if choice == "1":
                for issue in dashboard["issues"]:
                    print(
                        f"{issue['reference']} | {issue['status']} | {issue['department']}"
                    )
            elif choice == "2":
                for issue in dashboard["issues"]:
                    if issue["status"] != "CLOSED":
                        print(
                            f"{issue['reference']} | {issue['status']} | {issue['next_action']}"
                        )
            elif choice == "3":
                selected = input("Issue ID: ").strip()
                if selected:
                    self.issue_id = int(selected)
                    self.show_timeline()
            elif choice == "4":
                feedback = self.request("get", "/feedback")
                print(f"Feedback total: {len(feedback)}")
                for item in feedback:
                    print(f"{item['id']} | {item['status']} | {item['channel']}")
            elif choice == "6":
                return

    def run_demo(self) -> None:
        _section("FULL LIFECYCLE DEMO")
        self.request(
            "post",
            "/feedback",
            json={
                "name": "CLI Demo Reporter",
                "contact": "cli-demo@example.com",
                "content": "My Engineering Mathematics marks are missing from the portal.",
                "channel": "cli-demo",
                "context": "Semester 2 results",
            },
        )
        feedback = self.request("get", "/feedback")
        feedback_id = next(
            item["id"] for item in feedback if item["channel"] == "cli-demo"
        )
        print("[COLLECTION] Feedback received")
        self.request("post", f"/feedback/{feedback_id}/process")
        print("[AGENT] Feedback classified")
        routed = self.request("post", f"/feedback/{feedback_id}/route")
        issue = routed["issue"]
        self.issue_id = issue["id"]
        print(
            f"[ISSUE] {issue['reference']} created and routed to {issue['department']}"
        )
        for path, payload, label in [
            ("acknowledge", None, "Reporter acknowledged"),
            ("start", None, "Handler started work"),
            (
                "complete",
                {"resolution": "Marks uploaded to the portal."},
                "Issue completed",
            ),
            ("confirm", {"confirmed": True}, "Resolution confirmed"),
            ("close", None, "Issue closed"),
        ]:
            result = self.request(
                "post", f"/issues/{self.issue_id}/{path}", json=payload
            )
            print(f"[WORKFLOW] {label}: {result['issue']['status']}")
        self.show_timeline()
        self.show_notifications()
        self.qa_workspace(interactive=False)

    def _show_transition(self, result: dict) -> None:
        issue = result["issue"]
        print(f"[WORKFLOW] {result['message']} -> {issue['status']}")

    def _show_latest_notification(self, notifications: list[dict]) -> None:
        if notifications:
            item = notifications[-1]
            print(f"[NOTIFICATION] {item['message']} (ID {item['id']})")

    @staticmethod
    def _show_error(operation: str, error: Exception) -> None:
        print(f"\nERROR\nOperation: {operation}\nError: {error}")


def _interactive(workspace: CLIWorkspace) -> None:
    while True:
        _section("FEEDBACK WATCH TOWER - CLI WORKSPACE")
        print(
            "1. Reporter\n2. Handler\n3. QA / Watch Tower\n4. Run full lifecycle demo\n5. Exit"
        )
        choice = input("Select: ").strip()
        try:
            if choice == "1":
                workspace.submit_feedback()
                workspace.reporter_confirmation()
            elif choice == "2":
                workspace.handler_workspace()
            elif choice == "3":
                workspace.qa_workspace()
            elif choice == "4":
                workspace.run_demo()
            elif choice == "5":
                return
        except (RuntimeError, ValueError) as exc:
            workspace._show_error("CLI operation", exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive Feedback Watch Tower CLI")
    parser.add_argument("--demo", action="store_true", help="run the full lifecycle")
    parser.add_argument(
        "--fresh", action="store_true", help="use a temporary isolated database"
    )
    parser.add_argument("--verbose", action="store_true", help="show API calls")
    args = parser.parse_args()
    client, directory = _load_client(args.fresh or args.demo)
    try:
        with client:
            workspace = CLIWorkspace(client, verbose=args.verbose)
            if args.demo:
                workspace.run_demo()
            else:
                _interactive(workspace)
    finally:
        if directory is not None:
            from app.core import database

            database.engine.dispose()
            directory.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

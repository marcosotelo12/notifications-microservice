from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from datetime import datetime, timezone
import json

app = Flask(__name__)
CORS(app)

DATA_FILE = Path(__file__).parent / "notifications.json"
VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_STATUSES = {"read", "unread"}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

def load_notifications():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []

def save_notifications(notifications):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(notifications, file, indent=2)


def get_next_id(notifications):
    if not notifications:
        return 1
    return max(notification["id"] for notification in notifications) + 1

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "service": "Notification Microservice",
        "endpoints": [
            "GET /notifications?user_id=<id>",
            "POST /notifications",
            "PATCH /notifications/<notification_id>/read"
        ]
    })
@app.route("/notifications", methods=["GET"])
def get_notifications():
    user_id = request.args.get("user_id")
    status = request.args.get("status")
    priority = request.args.get("priority")

    if not user_id:
        return error_response("Missing required parameter: user_id")

    if status and status not in VALID_STATUSES:
        return error_response("Invalid status. Use 'read' or 'unread'.")

    if priority and priority not in VALID_PRIORITIES:
        return error_response("Invalid priority. Use 'High', 'Medium', or 'Low'.")

    notifications = load_notifications()

    results = [
        notification for notification in notifications
        if str(notification.get("user_id")) == str(user_id)
    ]

    if status:
        results = [notification for notification in results if notification.get("status") == status]

    if priority:
        results = [notification for notification in results if notification.get("priority") == priority]

    # User story requirement: High priority notifications should appear first.
    results.sort(key=lambda item: (PRIORITY_ORDER.get(item.get("priority"), 99), item.get("due_date", "")))

    return jsonify({
        "success": True,
        "notifications": results
    }), 200

@app.route("/notifications", methods=["POST"])
def create_notification():
    data = request.get_json(silent=True)

    if not data:
        return error_response("Request body must be valid JSON.")

    required_fields = ["user_id", "title", "due_date", "priority", "message"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return error_response(f"Missing required field(s): {', '.join(missing_fields)}")

    if data["priority"] not in VALID_PRIORITIES:
        return error_response("Invalid priority. Use 'High', 'Medium', or 'Low'.")

    notifications = load_notifications()

    new_notification = {
        "id": get_next_id(notifications),
        "user_id": str(data["user_id"]),
        "title": str(data["title"]),
        "due_date": str(data["due_date"]),
        "priority": data["priority"],
        "status": "unread",
        "message": str(data["message"]),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    notifications.append(new_notification)
    save_notifications(notifications)

    return jsonify({
        "success": True,
        "notification": new_notification
    }), 201

@app.route("/notifications/<int:notification_id>/read", methods=["PATCH"])
def mark_notification_as_read(notification_id):
    """Mark a notification as read."""
    notifications = load_notifications()

    for notification in notifications:
        if notification.get("id") == notification_id:
            notification["status"] = "read"
            notification["read_at"] = datetime.now(timezone.utc).isoformat()
            save_notifications(notifications)
            return jsonify({
                "success": True,
                "notification": notification
            }), 200

    return error_response("Notification not found.", 404)


@app.route("/notifications/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    """Optional helper endpoint for testing and cleanup."""
    notifications = load_notifications()
    new_notifications = [
        notification for notification in notifications
        if notification.get("id") != notification_id
    ]

    if len(new_notifications) == len(notifications):
        return error_response("Notification not found.", 404)

    save_notifications(new_notifications)
    return jsonify({"success": True, "message": "Notification deleted."}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

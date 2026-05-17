from flask import Flask, jsonify, request
import json

app = Flask(__name__)
DATA_FILE = "notifications.json"

def load_notifications():
    with open(DATA_FILE, "r") as file:
        return json.load(file)

def save_notifications(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

@app.route("/notifications", methods=["GET"])
def get_notifications():
    notifications = load_notifications()
    return jsonify(notifications)

@app.route("/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_as_read(notification_id):
    notifications = load_notifications()

    for notification in notifications:
        if notification["id"] == notification_id:
            notification["status"] = "read"

    save_notifications(notifications)

    return jsonify({
        "success": True,
        "message": "Notification updated"
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)

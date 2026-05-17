import requests

response = requests.get(
    "http://127.0.0.1:5000/notifications"
)

print("Notifications:")
print(response.json())

update = requests.put(
    "http://127.0.0.1:5000/notifications/1/read"
)

print("Update response:")
print(update.json())

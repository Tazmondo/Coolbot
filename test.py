import json

with open("botsettings.txt", "w") as file:
    params = {
        "token": "test",
        "myid": 1,
        "myserverid": 2
    }
    file.write(json.dumps(params, indent=True))
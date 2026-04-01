with open("overwatch/backend/logs/models.py", "r") as f:
    content = f.read()

content = content.replace(
"""    generated_by = models.ForeignKey(
        "accounts.JWTUser",
        null=True, on_delete=models.SET_NULL
    )""",
"""    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, on_delete=models.SET_NULL
    )""")

with open("overwatch/backend/logs/models.py", "w") as f:
    f.write("from django.conf import settings\n" + content)

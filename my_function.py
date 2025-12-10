# This simulates what a user would upload
def handle(req):
    name = req.get("name", "World")
    return f"Hello, {name}! This is running on AryaXAI FaaS."

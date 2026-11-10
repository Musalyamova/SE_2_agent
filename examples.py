SQL_INJECTION = """
def get_user(username):
    password = "super_secret_123"
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return execute(query)
"""

HARDCODED_PASSWORD = """
def connect():
    password = "admin123"
    db.connect(user="root", password=password)
"""

INSECURE_PICKLE = """
import pickle
def load_data(data):
    return pickle.loads(data)
"""

EXAMPLES = {
    "1": ("SQL-инъекция", SQL_INJECTION),
    "2": ("Хардкод пароля", HARDCODED_PASSWORD),
    "3": ("Небезопасный pickle", INSECURE_PICKLE)
}
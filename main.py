from backend.database import init_db
from frontend.cli import menu

if __name__ == "__main__":
    init_db()
    menu()

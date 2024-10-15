
# Add the project root directory to sys.path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from models.auth import CLIAuthenticator, Account
import mysql.connector

class UserController:
    def __init__(self):
        """Controller to handle user operations."""
        self.authenticator = CLIAuthenticator()
        self.current_user = None

    def _is_admin(self):
        user = self.current_user
        return  user.roles[0] == "admin"


    def login(self):
        print("Login:")
        username = input("Username: ")
        password = input("Password: ")
        user = self.authenticator.authenticate(username, password)
        if user:
            print(f"Welcome, {user.username}!")
            print(f"Roles: {user.roles}")
            self.current_user = user
            return True
        else:
            print("Invalid credentials.")
            return False

    def signup(self):
        print("Sign up:")
        username = input("Username: ")
        password = input("Password: ")
        # role = input("Role (admin/user): ")  # Allow the user to choose a role during signup
        account = Account(username, password)
        if self.authenticator.register(account): #        if self.authenticator.register(account, role):
            print(f"Account created successfully for user: {username}!")
            return True
        else:
            print("Username already exists.")
            return False

    def __del__(self):
        """Ensure the connection is closed when the object is destroyed."""
        self.current_user = None
        self.authenticator.close()

    # def _is_admin(self):
    #     return (self.roles[0] == "admin")

if __name__ == "__main__":
    controller = UserController()
    while True:
        print("\n1. Login\n2. Signup\n3. Exit")
        option = input("Select an option: ")
        if option == "1":
            controller.login()
        elif option == "2":
            controller.signup()
        elif option == "3":
            break

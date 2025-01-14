#!/usr/bin/env python3

import argparse
import os
import subprocess

# Function to log actions
def log_action(action, details):
    with open("usermgt.log", "a") as log_file:
        log_file.write(f"{action}: {details}\n")

# Function to create a new user
def create_user(username, fullname, group, shell="/bin/bash"):
    try:
        # Check if the group exists
        result = subprocess.run(["getent", "group", group], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Group {group} does not exist. Creating group...")
            subprocess.run(["groupadd", group], check=True)
        
        # Check if the user already exists
        result = subprocess.run(["id", username], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"User {username} already exists.")
            log_action("ERROR_CREATE_USER", f"User {username} already exists.")
            return

        # Add user
        subprocess.run([
            "useradd",
            "-m",
            "-c", fullname,
            "-g", group,
            "-s", shell,
            username
        ], check=True)
        print(f"User {username} created successfully.")
        log_action("CREATE_USER", f"Username={username}, FullName={fullname}, Group={group}, Shell={shell}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating user {username}: {e}")
        log_action("ERROR_CREATE_USER", f"Error creating user {username}: {e}")
    except Exception as e:
        print(f"Unexpected error creating user {username}: {e}")
        log_action("ERROR_CREATE_USER", f"Unexpected error creating user {username}: {e}")

# Function to delete an existing user
def delete_user(username):
    try:
        # Check if the user exists
        result = subprocess.run(["id", username], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"User {username} does not exist.")
            log_action("ERROR_DELETE_USER", f"User {username} does not exist.")
            return

        # Ensure the backup directory exists
        backup_dir = f"/backup/{username}"
        os.makedirs("/backup", exist_ok=True)
        os.chmod("/backup", 0o755)

        # Backup user data before deletion
        home_dir = f"/home/{username}"
        if os.path.exists(home_dir):
            subprocess.run(["rsync", "-av", home_dir, backup_dir], check=True)
            print(f"Data for user {username} backed up to {backup_dir}.")
        else:
            print(f"No home directory found for user {username}. Skipping backup.")

        # Delete user
        result = subprocess.run(["userdel", "-r", username], stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            print(f"User {username} deleted successfully.")
            log_action("DELETE_USER", f"Username={username}")
        else:
            print(f"Failed to delete user {username}.")
            log_action("ERROR_DELETE_USER", f"Failed to delete user {username}. Return code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting user {username}: {e}")
        log_action("ERROR_DELETE_USER", f"Error deleting user {username}: {e}")
    except Exception as e:
        print(f"Unexpected error deleting user {username}: {e}")
        log_action("ERROR_DELETE_USER", f"Unexpected error deleting user {username}: {e}")

# Main function to handle argument parsing and execution
def main():
    parser = argparse.ArgumentParser(description="User Management Script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for creating a user
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--username", required=True, help="Username of the new user")
    create_parser.add_argument("--fullname", required=True, help="Full name of the user")
    create_parser.add_argument("--group", required=True, help="Group to assign the user to")
    create_parser.add_argument("--shell", default="/bin/bash", help="Shell for the user (default: /bin/bash)")

    # Subparser for deleting a user
    delete_parser = subparsers.add_parser("delete", help="Delete an existing user")
    delete_parser.add_argument("--username", required=True, help="Username of the user to delete")

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate function
    if args.command == "create":
        create_user(args.username, args.fullname, args.group, args.shell)
    elif args.command == "delete":
        delete_user(args.username)

# Entry point
if __name__ == "__main__":
    main()

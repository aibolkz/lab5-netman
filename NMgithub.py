import os
import csv
from git import Repo
from github import Github

#credentials
GITHUB_USERNAME = "aibolkz"  # Your GitHub username
REPO_NAME = "lab5-netman"  # Name of the repository
LOCAL_REPO_PATH = "./lab5-netman"  # Local directory for the repository

#token from gitaccess.csv
def read_github_token():
    try:
        with open("gitaccess.csv", mode="r", encoding="utf8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                return row["token"]
        raise ValueError("Token not found in gitaccess.csv")
    except FileNotFoundError:
        raise FileNotFoundError("gitaccess.csv file not found. Please create it with your GitHub token.")

#GitHub API
GITHUB_TOKEN = read_github_token()
github = Github(GITHUB_TOKEN)

def create_or_clone_repo():
    """new GitHub repository or clone an existing one."""
    try:
        # checkif the repository already exists
        repo = github.get_user().get_repo(REPO_NAME)
        print(f"Repository '{REPO_NAME}' already exists. Cloning...")
        Repo.clone_from(repo.clone_url, LOCAL_REPO_PATH)
    except Exception:
        #new repository if it doesn't exist
        print(f"Repository '{REPO_NAME}' does not exist. Creating...")
        repo = github.get_user().create_repo(REPO_NAME, private=True)
        print(f"Repository '{REPO_NAME}' created successfully.")
        Repo.clone_from(repo.clone_url, LOCAL_REPO_PATH)

def add_and_commit_files(repo, files):
    """add and commit files to  local repository."""
    repo.git.add(files)
    repo.index.commit(f"Added/Updated {len(files)} files: {', '.join(files)}")

def push_to_github(repo):
    """push changes to the GitHub repository."""
    origin = repo.remote(name="origin")
    origin.push()
    print("Changes pushed to GitHub.")

def get_modified_files(repo):
    """Get a list of modified files in the local repository."""
    modified_files = [item.a_path for item in repo.index.diff(None)]
    return modified_files

def main():
    #1reate or clone the repository
    create_or_clone_repo()

    #2Initialize the local repository
    repo = Repo(LOCAL_REPO_PATH)

    #3Add .txt and .jpg files to the repository
    files_to_add = []
    for root, _, files in os.walk(LOCAL_REPO_PATH):
        for file in files:
            if file.endswith((".txt", ".jpg")):
                files_to_add.append(os.path.join(root, file))

    if files_to_add:
        add_and_commit_files(repo, files_to_add)
        print(f"Added {len(files_to_add)} files to the repository.")

    #4Compare modified files and push to GitHub
    modified_files = get_modified_files(repo)
    if modified_files:
        print(f"Found {len(modified_files)} modified files: {', '.join(modified_files)}")
        add_and_commit_files(repo, modified_files)
        push_to_github(repo)
    else:
        print("No modified files found.")

if __name__ == "__main__":
    main()
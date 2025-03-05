#/usr/bin/env python3
import os
import shutil
import git
from github import Github
import csv



#gitHub credentials and repository info
GITHUB_USERNAME = "aibolkz"  # Your GitHub username
REPO_NAME = "NM_lab"  # Name of the repository
LOCAL_REPO_PATH = "./lab5-git-new"  # Local directory for the repository



#read GitHub token csv
def read_github_token():
    try:
        with open("gitaccess.csv", mode="r", encoding="utf8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                return row["token"]
        raise ValueError("Token not found in gitaccess.csv")
    except FileNotFoundError:
        raise FileNotFoundError("gitaccess.csv file not found. Please create it with your GitHub token.")




#gitHub API client
GITHUB_TOKEN = read_github_token()
github = Github(GITHUB_TOKEN)




#create or clone the repository
def create_or_clone_repo():
    """Create a new GitHub repository or clone an existing one."""
    try:
        # Check repository  exists
        repo = github.get_user().get_repo(REPO_NAME)
        print(f"Repository '{REPO_NAME}' already exists. Cloning...")
        git.Repo.clone_from(repo.clone_url, LOCAL_REPO_PATH)
    except Exception:
        #if  doesn't exist, create 
        print(f"Repository '{REPO_NAME}' does not exist. Creating...")
        repo = github.get_user().create_repo(REPO_NAME, private=True)
        print(f"Repository '{REPO_NAME}' created successfully.")
        git.Repo.clone_from(repo.clone_url, LOCAL_REPO_PATH)



#cp files to bnew local repository folder
def copy_files_to_repo():
    """Copy .txt and .jpg files to the local repository."""
    files_to_copy = []
    for file in os.listdir('.'):
        if file.endswith(('.txt', '.jpg')):
            files_to_copy.append(file)

    if not os.path.exists(LOCAL_REPO_PATH):
        os.makedirs(LOCAL_REPO_PATH)

    for file in files_to_copy:
        shutil.copy(file, LOCAL_REPO_PATH)
        print(f"File {file} copied successfully.")



#push the files to GitHub
def add_and_commit_files(repo):
    """Add files to Git and commit changes."""
    repo.git.add(A=True)  # Add all new/modified files
    repo.index.commit("Added new .txt and .jpg files")
    print("Files committed.")



def push_to_github(repo):
    """Push the changes to the GitHub repository."""
    origin = repo.remote(name="origin")
    origin.push()
    print("Changes pushed to GitHub.")



def main():
    """Main function to execute the script."""
    create_or_clone_repo()

    #open repository
    repo = git.Repo(LOCAL_REPO_PATH)

    #cp files  local repository
    copy_files_to_repo()

    # 
    add_and_commit_files(repo)

    # Push changes b
    push_to_github(repo)

if __name__ == "__main__":
    main()

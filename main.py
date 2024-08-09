import os
import requests
import uuid
import json
import sys
from tqdm import tqdm
import subprocess
import shutil

class ColorPrinter:
    @staticmethod
    def red(skk):
        print("\033[91m {}\033[00m".format(skk))
    @staticmethod
    def green(skk):
        print("\033[92m {}\033[00m".format(skk))
    @staticmethod
    def yellow(skk):
        print("\033[93m {}\033[00m".format(skk))
    @staticmethod
    def lightpurple(skk):
        print("\033[94m {}\033[00m".format(skk))
    @staticmethod
    def purple(skk):
        print("\033[95m {}\033[00m".format(skk))
    @staticmethod
    def cyan(skk):
        print("\033[96m {}\033[00m".format(skk))
    @staticmethod
    def lightgray(skk):
        print("\033[97m {}\033[00m".format(skk))
    @staticmethod
    def black(skk):
        print("\033[98m {}\033[00m".format(skk))

class Lock:
    def __init__(self):
        self.user_directory = os.path.expanduser("~")
        self.python_pm_path = os.path.join(self.user_directory, 'PythonPM')
        self.lock_path = os.path.join(self.python_pm_path, 'lock')
    def get(self):
        if not self.is_active():
            open(self.lock_path, 'a').close()
            return True
        else:
            return False
    def remove(self):
        if self.is_active():
            os.remove(self.lock_path)
    def is_active(self):
        return os.path.exists(self.lock_path)

def foldersetup():
    user_directory = os.path.expanduser("~")
    python_pm_path = os.path.join(user_directory, 'PythonPM')
    if not os.path.exists(python_pm_path):
        os.makedirs(python_pm_path)
    repos_path = os.path.join(python_pm_path, 'repos')
    temp_path = os.path.join(python_pm_path, 'temp')
    if not os.path.exists(repos_path):
        os.makedirs(repos_path)
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

def load_repo():
    pr.cyan("Loading repositories")
    user_directory = os.path.expanduser("~")
    repos_dir = os.path.join(user_directory, 'PythonPM', 'repos')
    all_repos = {"metadata": [], "apps": {}}
    for filename in os.listdir(repos_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(repos_dir, filename)
            with open(filepath, 'r') as file:
                repo_data = json.load(file)
                all_repos["metadata"].append(repo_data["metadata"])
                for app, versions in repo_data["apps"].items():
                    if app in all_repos["apps"]:
                        all_repos["apps"][app].extend(versions)
                    else:
                        all_repos["apps"][app] = versions
    return all_repos
def download_file(url):
    user_directory = os.path.expanduser("~")
    directory = os.path.join(user_directory, 'PythonPM', 'temp')
    file_extension = url.split('.')[-1]
    file_name = str(uuid.uuid4()) + '.' + file_extension
    file_path = os.path.join(directory, file_name)
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_scale=True)
    with open(file_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            progress_bar.update(len(data))
    progress_bar.close()
    return file_path

def download_repo(url):
    user_directory = os.path.expanduser("~")
    directory = os.path.join(user_directory, 'PythonPM', 'repos')
    file_extension = url.split('.')[-1]
    file_name = str(uuid.uuid4()) + '.' + file_extension
    file_path = os.path.join(directory, file_name)
    response = requests.get(url, stream=True)
    with open(file_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
    return file_path

def fetch_app(appname):
    repo = load_repo()
    return repo['apps'][appname]

def install_app(appname):
    pr.cyan(f"Searching for {appname}")
    try:
        appinfo = fetch_app(appname)
        pr.green(f"Found {appname}")
        pr.lightpurple(f"| Name: {appinfo[0]['name']}")
        pr.lightpurple(f"| Version: {appinfo[0]['version']}")
        pr.lightpurple(f"| Architecture: {appinfo[0]['arch']}")
        pr.lightpurple(f"| Developer(s): {appinfo[0]['developer']}")
        choice = input("\033[93m {}\033[00m".format("Do you want to continue? [Y/n]"))
        if choice.lower() == "y" or choice.lower() == "": pass
        else: return
    except KeyError:
        pr.red(f"App {appname} not found or metadata incomplete.")
        return
    dlfile = download_file(appinfo[0]['url'])
    command = appinfo[0]['command'].replace("||file||", dlfile)
    pr.cyan(f"Install command: {command}")
    pr.cyan("Installing")
    try:
        os.system(command)
    except Exception as e:
        pr.red(f"Error installing: {e}")
    pr.cyan("Cleaning up")
    try:
        os.remove(dlfile)
        pr.green("Done!")
    except Exception as e:
        pr.red(f"Error cleaning up: {e}")

def uninstall_app(appname):
    pr.cyan(f"Searching for {appname}")
    try:
        appinfo = fetch_app(appname)
        pr.green(f"Found {appname}")
        pr.lightpurple(f"| Uninstall command: {appinfo[0]['uninstall']}")
        choice = input("\033[93m {}\033[00m".format("Do you want to continue? [Y/n]"))
        if choice.lower() == "y" or choice.lower() == "": pass
        else: return
    except KeyError:
        pr.red(f"App {appname} not found or metadata incomplete.")
        return
    command = appinfo[0]['uninstall']
    try:
        subprocess.call(command)
        pr.green("Done")
    except Exception as e:
        pr.red(f"Error uninstalling: {e}")

def refresh_repos():
    pr.cyan("Updating repositories")
    user_directory = os.path.expanduser("~")
    repos_dir = os.path.join(user_directory, 'PythonPM', 'repos')
    if os.listdir(repos_dir):
        listing = os.listdir(repos_dir)
        count = len(listing)
        pr.green(f"Found {count} repositories")
        urls = []
        cnt = 0
        for repo in listing:
            with open(os.path.join(repos_dir, repo), 'r') as currentrepo:
                try:
                    cnt += 1
                    crjson = json.load(currentrepo)
                    urls.append(crjson['metadata']['source'])
                    pr.cyan(f"Hit {cnt}: {crjson['metadata']['source']}")
                except KeyError:
                    pr.red(f'Error: {repo} has no metadata')
        for filename in os.listdir(repos_dir):
            file_path = os.path.join(repos_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                pr.red('Failed to delete %s. Reason: %s' % (file_path, e))
        for url in urls:
            pr.cyan(f"Downloading {url}")
            namer = download_repo(url)
            pr.green(f"Saved as {namer}")
            pr.cyan("Checking repo")
            with open(os.path.join(repos_dir, namer), 'r') as copen:
                cjson = json.load(copen)
                try:
                    pr.lightpurple(f"| Name: {cjson['metadata']['name']}")
                    pr.lightpurple(f"| Author: {cjson['metadata']['author']}")
                    pr.lightpurple(f"| Source: {cjson['metadata']['source']}")
                except KeyError:
                    pr.red("Repo metadata incomplete")
            pr.green("Done")
    else:
        pr.red("No repositories found")
        sys.exit()

def cleanup():
    pr.cyan("Deleting old installers")
    user_directory = os.path.expanduser("~")
    temp_dir = os.path.join(user_directory, 'PythonPM', 'temp')
    count = len([filename for filename in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, filename))])
    pr.green(f"Found {count} files")
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pr.red('Failed to delete %s. Reason: %s' % (file_path, e))
    pr.green("Done")

if __name__ == "__main__":
    foldersetup()
    pr = ColorPrinter()
    lock = Lock()
    try:
        action = sys.argv[1]
    except IndexError:
        pr.red("No command D:")
        sys.exit()
    if lock.is_active():
        pr.red("Lock is active, this may be because you're trying to do multiple actions at once or an action was interrupted.")
        pr.red("Exiting")
        sys.exit()
    lock.get()
    match action:
        case "install":
            try:
                rpack = sys.argv[2]
            except IndexError:
                pr.red("No package name D:")
                sys.exit()
            install_app(sys.argv[2])
        case "uninstall":
            try:
                rpack = sys.argv[2]
            except IndexError:
                pr.red("No package name D:")
                sys.exit()
            uninstall_app(sys.argv[2])
        case "update":
            refresh_repos()
        case "cleanup":
            cleanup()
        case "addrepo":
            try:
                rpack = sys.argv[2]
            except IndexError:
                pr.red("No repo URL D:")
                sys.exit()
            pr.cyan(f"Downloading {rpack}")
            download_repo(sys.argv[2])
            refresh_repos()
    lock.remove()

import argparse
import os
import platform
import subprocess

parser = argparse.ArgumentParser(description='Quick shell utilities script')
kernel_version = platform.release()

# Args
parser.add_argument('-R', '--rebuild', action='store_true', help='Rebuild quickshell-git package')
parser.add_argument('-M', '--merge', action='store_true', help='Merge new configs from files ended with .lua.new in ~/.config/hypr/')

args = parser.parse_args()

if "arch" not in kernel_version:
    print("This script is intended for Arch Linux or Arch-based distributions, but not for cachy OS.")
    exit(1)

def rebuild_qs():
    if not os.path.exists("/usr/bin/yay") or not os.path.exists("/usr/bin/paru"):
        print("This script requires 'yay' or 'paru' to rebuild the quickshell-git package.")
        exit(1)
    print("Rebuilding quickshell-git package aur/quickshell-git...")
    if os.path.exists("/usr/bin/yay"):
        subprocess.run(["yay", "-S", "--noconfirm", "quickshell-git"])
    elif os.path.exists("/usr/bin/paru"):
        subprocess.run(["paru", "-S", "--noconfirm", "quickshell-git"])

def merge_configs():
    flaggedLines: dict[str, int] = {}
    config_dir = os.path.expanduser("~/.config/hypr/")
    for file in os.listdir(config_dir):
        if file.endswith(".lua.new"):
            original_file = file[:-4] # Modified file without the .new extension because of user's additional configs
            for lines in open(os.path.join(config_dir, original_file), 'r'):
                for line in lines:
                    if line.endswith("-- no-rm flag"):
                        flaggedLines.pop(line, line.index) # Save line and position to add it later to the new config file
            with open(os.path.join(config_dir, file), 'r') as new_file:
                # Add flagged lines to the new config file
                new_lines = new_file.readlines()
                for line, index in flaggedLines.items():
                    new_lines.insert(index, line)
            os.replace(os.path.join(config_dir, file), os.path.join(config_dir, original_file))             

if args.rebuild:
    rebuild_qs()
if args.merge:
    merge_configs()

import argparse
import difflib
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

def merge_preserved_lines(original_lines: list[str], new_lines: list[str]) -> list[str]:
    flagged_indices = [
        index for index, line in enumerate(original_lines)
        if "-- no-rm flag" in line
    ]
    if not flagged_indices:
        return new_lines

    flagged_set = set(flagged_indices)
    match_lines = [
        None if index in flagged_set else line
        for index, line in enumerate(original_lines)
    ]
    matching_lines: dict[int, int] = {}
    matcher = difflib.SequenceMatcher(None, match_lines, new_lines, autojunk=False)
    for original_start, new_start, size in matcher.get_matching_blocks():
        for offset in range(size):
            matching_lines[original_start + offset] = new_start + offset

    groups: list[tuple[int, int]] = []
    for index in flagged_indices:
        if groups and index == groups[-1][1]:
            groups[-1] = (groups[-1][0], index + 1)
        else:
            groups.append((index, index + 1))

    insertions: list[tuple[int, int, list[str]]] = []
    for start, end in groups:
        previous = next(
            (index for index in reversed(matching_lines) if index < start),
            None,
        )
        following = next(
            (index for index in matching_lines if index >= end),
            None,
        )
        if previous is None and following is None:
            raise ValueError(
                f"Cannot safely locate preserved line {start + 1} in the updated file"
            )

        if following is None or (
            previous is not None and start - previous <= following - end + 1
        ):
            target = matching_lines[previous] + 1
        else:
            target = matching_lines[following]
        insertions.append((target, start, original_lines[start:end]))

    for target, _, lines in sorted(
        insertions,
        key=lambda item: (item[0], item[1]),
        reverse=True,
    ):
        new_lines[target:target] = lines
    return new_lines

def merge_configs():
    config_dir = os.path.expanduser("~/.config/hypr/")
    updates: list[tuple[str, str, list[str]]] = []
    for file in sorted(os.listdir(config_dir)):
        if not file.endswith(".lua.new"):
            continue

        new_path = os.path.join(config_dir, file)
        original_path = os.path.join(config_dir, file[:-4])
        with open(original_path, "r") as original_file:
            original_lines = original_file.readlines()
        with open(new_path, "r") as new_file:
            new_lines = new_file.readlines()

        try:
            merged_lines = merge_preserved_lines(original_lines, new_lines)
        except ValueError as error:
            raise ValueError(f"{file}: {error}") from error
        updates.append((new_path, original_path, merged_lines))

    for new_path, original_path, merged_lines in updates:
        with open(new_path, "w") as new_file:
            new_file.writelines(merged_lines)
        os.replace(new_path, original_path)

if args.rebuild:
    rebuild_qs()
if args.merge:
    merge_configs()

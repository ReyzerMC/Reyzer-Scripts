import platform

repo-url: str = "https://github.com/voidlhf/StarRailGrubThemes.git"
needed-packages: str = "git, base-devel, grub, nano, less"

print("This script will install the Star Rail Grub theme on your system.")
print(f"Repository URL: {repo-url}")
print(f"Required packages: {needed-packages}")

kernel_version = platform.release()

def check_packages() -> None:
    import subprocess

    missing_packages = []
    for package in needed-packages.split(", "):
        try:
            subprocess.run(["pacman", "-Qi", package], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing_packages.append(package)

    if missing_packages:
        print(f"The following packages are missing: {', '.join(missing_packages)}")
        print("Running installation command to install missing packages...")
        subprocess.run(["pacman", "-S", "--noconfirm"] + missing_packages)

def config():
    import subprocess
    import os

    # Clone the repository
    subprocess.run(["git", "clone", repo-url, "/tmp/StarRailGrubThemes"])

    # Run all dirs in StarRailGrubThemes/assets/themes and copy them to /boot/grub/themes
    themes_dir = "/tmp/StarRailGrubThemes/assets/themes"
    target_dir = "/boot/grub/themes"
    os.makedirs(target_dir, exist_ok=True)
    for theme in os.listdir(themes_dir):
        theme_path = os.path.join(themes_dir, theme)
        if os.path.isdir(theme_path) and "_cn" not in theme: # To avoid chinese themes
            subprocess.run(["cp", "-r", theme_path, target_dir])

if "arch" in kernel_version:
    check_packages()
else:
    print("This script is intended for Arch Linux or Arch-based distributions.")
    exit(1)



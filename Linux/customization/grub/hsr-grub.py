#!/usr/bin/env python3
"""Instala los temas GRUB de Star Rail en Arch Linux (o derivadas).

Uso: sudo python starrail_grub.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/voidlhf/StarRailGrubThemes.git"
NEEDED_PACKAGES = ["git", "grub"]
THEMES_DIR = Path("/boot/grub/themes")
GRUB_DEFAULT = Path("/etc/default/grub")
GRUB_CFG = "/boot/grub/grub.cfg"


def die(msg: str) -> None:
    print(msg)
    sys.exit(1)


def is_arch_based() -> bool:
    """Detecta Arch o derivadas leyendo /etc/os-release."""
    try:
        text = Path("/etc/os-release").read_text()
    except OSError:
        return shutil.which("pacman") is not None
    ids = re.findall(r"^(?:ID|ID_LIKE)=(.*)$", text, flags=re.MULTILINE)
    words = " ".join(i.strip('"') for i in ids).split()
    return "arch" in words


def check_packages() -> None:
    missing = []
    for package in NEEDED_PACKAGES:
        result = subprocess.run(
            ["pacman", "-Qi", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            missing.append(package)

    if missing:
        print(f"Faltan paquetes: {', '.join(missing)}")
        print("Instalando paquetes faltantes...")
        subprocess.run(["pacman", "-S", "--needed", "--noconfirm", *missing], check=True)


def clear_themes_dir() -> None:
    for item in THEMES_DIR.iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()


def install_themes() -> None:
    if THEMES_DIR.exists() and any(THEMES_DIR.iterdir()):
        answer = input(
            f"{THEMES_DIR} no está vacío. ¿Quieres borrar su contenido? "
            "(puede que ya tengas temas instalados) (y/n): "
        )
        if answer.strip().lower() == "y":
            clear_themes_dir()
        else:
            print("Se mantiene el contenido actual, no se instalan temas nuevos.")
            return

    THEMES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp) / "StarRailGrubThemes"
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(repo_path)], check=True)

        source = repo_path / "assets" / "themes"
        if not source.is_dir():
            die(f"No se encontró {source}. Puede que la estructura del repo haya cambiado.")

        for theme in sorted(source.iterdir()):
            # Se omiten los temas en chino
            if theme.is_dir() and "_cn" not in theme.name:
                shutil.copytree(theme, THEMES_DIR / theme.name, dirs_exist_ok=True)


def list_themes() -> list[str]:
    if not THEMES_DIR.is_dir():
        return []
    return sorted(
        t.name
        for t in THEMES_DIR.iterdir()
        if t.is_dir() and "_cn" not in t.name and (t / "theme.txt").is_file()
    )


def choose_theme(themes: list[str]) -> str:
    try:
        import questionary

        choice = questionary.select("Selecciona un tema para GRUB:", choices=themes).ask()
    except ImportError:
        print("(questionary no está instalado, usando menú simple)")
        for i, name in enumerate(themes, 1):
            print(f"  {i}. {name}")
        choice = None
        while choice is None:
            raw = input("Número del tema: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(themes):
                choice = themes[int(raw) - 1]
    if not choice:
        die("No se seleccionó ningún tema. Cancelando.")
    return choice


def update_grub_config(choice: str) -> None:
    theme_line = f'GRUB_THEME="{THEMES_DIR}/{choice}/theme.txt"\n'

    lines = GRUB_DEFAULT.read_text().splitlines(keepends=True)
    shutil.copy2(GRUB_DEFAULT, GRUB_DEFAULT.with_suffix(".bak"))

    new_lines = []
    replaced = False
    for line in lines:
        if not replaced and re.match(r"^\s*#?\s*GRUB_THEME=", line):
            new_lines.append(theme_line)
            replaced = True
        elif replaced and re.match(r"^\s*GRUB_THEME=", line):
            new_lines.append("#" + line)  # evita duplicados activos
        else:
            new_lines.append(line)

    if not replaced:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(theme_line)

    if any(re.match(r"^\s*GRUB_TERMINAL_OUTPUT=.*console", l) for l in new_lines):
        print(
            "Aviso: GRUB_TERMINAL_OUTPUT=console está activo en /etc/default/grub; "
            "coméntalo o el tema no se mostrará."
        )

    GRUB_DEFAULT.write_text("".join(new_lines))

    print("Regenerando la configuración de GRUB...")
    subprocess.run(["grub-mkconfig", "-o", GRUB_CFG], check=True)


def main() -> None:
    if os.geteuid() != 0:
        die("Este script necesita privilegios de root. Ejecútalo con sudo.")

    if not is_arch_based():
        die("Este script es para Arch Linux o derivadas.")

    print("Este script instalará los temas GRUB de Star Rail.")
    print(f"Repositorio: {REPO_URL}")
    print(f"Paquetes requeridos: {', '.join(NEEDED_PACKAGES)}")

    try:
        check_packages()
        install_themes()

        themes = list_themes()
        if not themes:
            die(f"No hay temas disponibles en {THEMES_DIR}.")

        update_grub_config(choose_theme(themes))
    except subprocess.CalledProcessError as e:
        die(f"Falló el comando {e.cmd}: código de salida {e.returncode}")

    print("Listo. Reinicia para ver el nuevo tema.")


if __name__ == "__main__":
    main()
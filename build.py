#!/usr/bin/env python3
"""
Build and Package Script for Nous Anki Add-on
Generates 'nous-anki.ankiaddon' zip bundle for distribution and installs locally if Anki2 folder exists.
"""

import os
import shutil
import zipfile


def build_package():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "nous_anki")
    output_filename = os.path.join(base_dir, "nous-anki.ankiaddon")

    print(f"[Build] Packaging {source_dir} -> {output_filename}...")

    # Exclude __pycache__, .DS_Store, and user_files from package
    def should_include(relpath):
        parts = relpath.split(os.sep)
        if any(p.startswith(".") or p == "__pycache__" or p == "user_files" for p in parts):
            return False
        return True

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                if should_include(rel_path):
                    zf.write(full_path, arcname=rel_path)
                    print(f"  + {rel_path}")

    size_kb = os.path.getsize(output_filename) / 1024.0
    print(f"[Build] Successfully built {output_filename} ({size_kb:.1f} KB)")

    # Optional local install if Anki2 is found
    home = os.path.expanduser("~")
    anki_addons_dir = os.path.join(home, "Library", "Application Support", "Anki2", "addons21")
    if os.path.isdir(anki_addons_dir):
        dest_addon = os.path.join(anki_addons_dir, "nous_anki")
        print(f"[Install] Deploying to Anki addons directory: {dest_addon}")
        if os.path.islink(dest_addon):
            os.unlink(dest_addon)
        elif os.path.exists(dest_addon):
            shutil.rmtree(dest_addon)
        shutil.copytree(source_dir, dest_addon, ignore=shutil.ignore_patterns("__pycache__", "user_files", "*.pyc"))
        print(f"[Install] Installed to {dest_addon}")
    else:
        print("[Install] Note: Anki addons directory not found on this machine. Ready to share .ankiaddon!")


if __name__ == "__main__":
    build_package()

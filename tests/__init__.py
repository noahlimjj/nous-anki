import sys
import os

anki_packages = "/Applications/Anki.app/Contents/Resources/app_packages"
if os.path.isdir(anki_packages) and anki_packages not in sys.path:
    sys.path.insert(0, anki_packages)

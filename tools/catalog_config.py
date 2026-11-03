"""KairoX86's catalog settings. KairoX86 has no game catalog: a library entry is a PC the player
sets up (an 86Box machine folder). Its catalog is the system definition alone (catalog/system-v2.json:
the controls every entry starts from), built by shared/tools/app_catalog.py from an empty research
file, so the shared controls, catalog update and audits work as in every app (KairoX86#66, #72)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared/tools"))
from launchbox_artwork import References

APP = "kairox86"
# No game is catalogued, so no game key names a platform; "pc" is the one a key would use.
PLATFORMS = ("pc",)
ARTWORK_CODE = None
ARTWORK = References("KairoX86", ())

# The media an entry's drives take: floppy, hard disk and CD images.
KINDS = {"fd", "hd", "cd"}
COMPANION = {}
# The extensions removed from a file's name before it is looked up (no game is looked up by name).
MEDIA_EXTENSIONS = (r"\.(img|ima|imd|td0|86f|mfm|vfd|flp|dsk|xdf|hdm|fdi|360|720|12|144"
                    r"|hdi|hdx|vhd|iso|cue|bin|mds|mdf|ccd|chd)$")

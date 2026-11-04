"""
Download translated role names and save them as translations/<lang>.json.

Each translation file maps the English role name to the translated role name, e.g.
{"Washerwoman": "Lavandera"}. The files are committed to the repo, so this script
only needs to be re-run when new roles are released.

Sources:
    es: https://villacuervos.es/wiki/ (Villa Cuervos, Spanish BOTC community)
"""

import json
import os

import requests

SPANISH_ROLES_API = "https://villacuervos.es/api/roles/"
TRANSLATIONS_DIR = "translations"


def extract_spanish_names(api_roles):
    """
    Build an {english_name: spanish_name} dictionary from the Villa Cuervos API.

    Only roles from official editions are used, as the site also hosts
    homebrew roles which may reuse the names of official ones.
    """
    names = {}
    for role in api_roles:
        if not role.get("edition", {}).get("official"):
            continue
        translated = (role.get("translation") or {}).get("name")
        if role.get("name") and translated:
            names[role["name"]] = translated
    return dict(sorted(names.items()))


def main():
    response = requests.get(SPANISH_ROLES_API, timeout=60)
    response.raise_for_status()
    names = extract_spanish_names(response.json())

    os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
    output = os.path.join(TRANSLATIONS_DIR, "es.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(names, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(names)} Spanish role names to {output}")


if __name__ == "__main__":
    main()

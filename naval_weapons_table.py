import os
import json
import subprocess
import csv
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# How to update:
# remove folders 
# rm -rf $LOCALAPPDATA\WarThunder\aces.vromfs.bin_u
# rm -rf $LOCALAPPDATA\WarThunder\lang.vromfs.bin_u
# rm -rf $LOCALAPPDATA\WarThunder\char.vromfs.bin_u
# python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\lang.vromfs.bin"
# python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\aces.vromfs.bin"
# python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\char.vromfs.bin"
# python naval_weapons_table.py --weaponspath "$LOCALAPPDATA\WarThunder\aces.vromfs.bin_u\gamedata\weapons\navalmodels_weapons" --unitspath "$LOCALAPPDATA\WarThunder\aces.vromfs.bin_u\gamedata\units\ships" --outputformat html --filename "output.html"
# note: the first execution includes unpacking a lot of files, which will take A TON of time

# Paths to files and scripts
BLK_UNPACK_SCRIPT = "blk_unpack_ng.py"
UNITS_WEAPONRY_CSV = r"$LOCALAPPDATA\WarThunder\lang.vromfs.bin_u\lang\units_weaponry.csv"
UNITS_CSV = r"$LOCALAPPDATA\WarThunder\lang.vromfs.bin_u\lang\units.csv"
CHAR_CONFIG = r"$LOCALAPPDATA\WarThunder\char.vromfs.bin_u\config"
WEAPONSPRESETS = r"$LOCALAPPDATA\WarThunder\aces.vromfs.bin_u\gamedata\units\ships\weaponpresets"

# CSV format settings
CSV_LISTSEPARATOR = ', ' # This is a separator for the for the ships, BRs and the ship classes list. Include spacing and make it different than CSV_DELIMITER
CSV_DELIMITER = ';'
CSV_LINETERMINATOR = '\n'

# Flag to bypass formatting names to human-readable format
RAW_NAMES = False
weapon_name_translation_dict = {}
bullet_name_translation_dict = {}
unit_name_translation_dict = {}
unit_type_translation_dict = {}

def load_translations():
    weapon_name_translation_dict = {}
    bullet_name_translation_dict = {}
    unit_name_translation_dict = {}
    unit_type_translation_dict = {}
    name_to_display = '_1' # 0 - long, 1 - short, 2 - type
    type_to_display = '_2' # 0 - long, 1 - short, 2 - type
    if os.path.exists(UNITS_WEAPONRY_CSV):
        with open(UNITS_WEAPONRY_CSV, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                if len(row) >= 2:
                    key, value = row[0], row[1]
                    if key.startswith("weapons/"):
                        weapon_name_translation_dict[key.replace('weapons/', '')] = value
                    else:
                        bullet_name_translation_dict[key] = value
    else:
        print("Failed to find units_weaponry.csv in UNITS_WEAPONRY_CSV path!")
        exit(1)
    if os.path.exists(UNITS_CSV):
        with open(UNITS_CSV, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                if len(row) >= 2:
                    key, value = row[0], row[1]
                    if "/" not in key and name_to_display in key:
                        unit_name_translation_dict[key[:-2] if key.endswith(name_to_display) else key] = value
                    if "/" not in key and type_to_display in key:
                        unit_type_translation_dict[key[:-2] if key.endswith(type_to_display) else key] = value
    else:
        print("Failed to find units.csv in UNITS_CSV path!")
        exit(1)

    return weapon_name_translation_dict, bullet_name_translation_dict, unit_name_translation_dict, unit_type_translation_dict

weapon_name_wiki_correction = {
    "38 cm/52 SK C/34 (380 mm)": "SK L/45 (380 mm)",
}

bullet_type_translation = {
    "apc_tank": "APC",
    "apcbc_tank": "APCBC",
    "sap_tank": "SAP",
    "sapcbc_tank": "SAPCBC",
    "he_frag_tank": "HE",
    "he_frag_dist_fuse": "HE-TF",
    "he_frag_base_fuse_tank": "HE-BF",
    "he_frag_radio_fuse": "HE-VT",
    "shrapnel_tank": "Shrapnel",
    "sapbc_tank": "SAPBC",
    "sapbc_flat_nose_tank": "SAPBC",
    "aphe_tank": "APHE",
    "aphebc_tank": "APHEBC",
    "common_tank": "SAP(C)",
    "special_common_tank": "SAP(SC)",
    "apds_fs_long_tank": "APDSFS", # e.g. unused shell on 76 mm/62 OTO-Melara Compact
    "he_frag_i_tank": "HE",
    "apc_solid_medium_caliber_tank": "APC"
}

bullet_type_is_de_marre_apcbc = {
    "apc_tank": False,
    "apcbc_tank": True,
    "sap_tank": False,
    "sapcbc_tank": False,
    "he_frag_tank": False,
    "he_frag_dist_fuse": False,
    "he_frag_base_fuse_tank": False,
    "he_frag_radio_fuse": False,
    "shrapnel_tank": False,
    "sapbc_tank": False,
    "sapbc_flat_nose_tank": False,
    "aphe_tank": False,
    "aphebc_tank": False,
    "common_tank": False,
    "special_common_tank": False,
    "apds_fs_long_tank": False, # Should have a different calculation that what we are using here, but this shell is not covered by the tool
    "he_frag_i_tank": False,
    "apc_solid_medium_caliber_tank": False
}


def translate_weapon_name(weapon_name, caliber_value, output_format='wikitext'):
    if RAW_NAMES:
        return weapon_name
    name = weapon_name_translation_dict.get(weapon_name, weapon_name)
    name = name.replace(' cannon', '').replace(' gun', '').replace(', ', ' ')
    link = f"{name} ({caliber_value} mm)"
    wikiname = weapon_name_wiki_correction.get(link, link) # this is relevant only for the old-wiki.warthunder.com, link slugs on the wiki 3.0 are defined manually by the wiki community moderators, so this approach does not work there
    if output_format == 'html':
        return f'<span title="{weapon_name}">{name}</span>'
    elif output_format in ['json', 'csv']:
        return name
    return f"[[{wikiname}|{name}]]"


def translate_bullet_name(bullet_name, output_format='wikitext'):
    if RAW_NAMES:
        return bullet_name
    if output_format == 'html':
        return f'<span title="{bullet_name}">{bullet_name_translation_dict.get(bullet_name, bullet_name)}</span>'
    return bullet_name_translation_dict.get(bullet_name, bullet_name)


def translate_unit_name(unit_name, output_format='wikitext'):
    if RAW_NAMES:
        return unit_name
    translated = unit_name_translation_dict.get(unit_name, unit_name)
    if output_format == 'html':
        return f'<a href="https://wiki.warthunder.com/unit/{unit_name}" title="{unit_name}">{translated}</a>'
    elif output_format in ['json', 'csv']:
        return translated
    return f"[[{translated}]]"

def translate_unit_type(unit_name, output_format='wikitext'):
    if output_format == 'html':
        return unit_type_translation_dict.get(unit_name, f"{unit_name} is unknown").replace(' ', '&nbsp;') #\u00A0
    return unit_type_translation_dict.get(unit_name, f"{unit_name} is unknown")

def unpack_blk_file(blk_file):
    blkx_file = blk_file.with_suffix(".blkx")
    if not blkx_file.exists():
        print(f"Unpacking {blk_file} to {blkx_file}")
        subprocess.run(["python", BLK_UNPACK_SCRIPT, str(blk_file)])


def unpack_blk_files(folder_path):
    blk_files = list(Path(folder_path).glob("*.blk"))
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(unpack_blk_file, blk_files)


def build_ship_weapon_map(units_folder, output_format='wikitext'):
    ship_map = defaultdict(list)
    ship_type_map = {}  # Map unit name to ship type

    def find_weapon_blks(obj):
        stems = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == 'blk' and isinstance(v, str):
                    stems.append(Path(v).stem)
                elif isinstance(v, str) and v.lower().endswith('.blk'):
                    stems.append(Path(v).stem)
                else:
                    stems.extend(find_weapon_blks(v))
        elif isinstance(obj, list):
            for item in obj:
                stems.extend(find_weapon_blks(item))
        return stems

    for unit_file in Path(units_folder).glob("*.blkx"):
        try:
            with open(unit_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON in unit file: {unit_file}")
            continue

        # Store the ship type for this unit
        unit_name = unit_file.stem
        ship_type = translate_unit_type(unit_name, output_format)
        ship_type_map[unit_name] = ship_type

        items = raw if isinstance(raw, list) else [raw]
        stems = set()
        for item in items:
            stems.update(find_weapon_blks(item))
        for stem in stems:
            ship_map[stem].append(unit_name)

    return ship_map, ship_type_map

def build_ship_and_mod_maps(units_folder):
    """
    Parses all unit files to build two maps:
    1. A map from a weapon's filename to the list of ships that use it.
    2. A map from a modification name to the list of ships that have it.
    """
    ship_weapon_map = defaultdict(list)
    ship_mod_map = defaultdict(list)

    if not units_folder or not Path(units_folder).exists():
        print(f"Warning: Units folder '{units_folder}' not found. Cannot map ships to weapons.")
        return ship_weapon_map, ship_mod_map

    for unit_file in Path(units_folder).glob("*.blkx"):
        try:
            with open(unit_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Could not read or parse {unit_file}: {e}")
            continue

        unit_name = unit_file.stem
        
        unit_data = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    unit_data.update(item)
        elif isinstance(data, dict):
            unit_data = data

        # Map weapons from commonWeapons using only the filename as the key
        if 'commonWeapons' in unit_data and isinstance(unit_data['commonWeapons'], list):
            for weapon_entry in unit_data['commonWeapons']:
                if isinstance(weapon_entry, dict) and 'Weapon' in weapon_entry:
                    weapon_details = weapon_entry['Weapon']
                    if 'blk' in weapon_details:
                        weapon_filename = Path(weapon_details['blk']).name
                        ship_weapon_map[weapon_filename].append(unit_name)
        
        # Map modifications
        if 'modifications' in unit_data and isinstance(unit_data['modifications'], dict):
            for mod_name in unit_data['modifications'].keys():
                ship_mod_map[mod_name].append(unit_name)

    return ship_weapon_map, ship_mod_map

def load_br_values():
    br_map = {}
    for cost_file in Path(CHAR_CONFIG).glob("wpcost.blkx"):
        try:
            with open(cost_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for name, entry in data.items():
                    econ = entry.get('economicRankHistorical') if isinstance(entry, dict) else None
                    if econ is not None:
                        br_map[name] = econ
            elif isinstance(data, list):
                for entry in data:
                    name = entry.get('name')
                    econ = entry.get('economicRankHistorical')
                    if name and econ is not None:
                        br_map[name] = econ
        except json.JSONDecodeError:
            print(f"Error reading BR data in: {cost_file}")
    return br_map

def jacob_de_marre_ap(caliber: float, mass: float, speed: float, explosive_mass: float, apcbc: bool) -> float:
    """
    Calculate armor penetration (mm) using the Jacob de Marre formula for AP/APC/APBC/APCBC shells.

    Parameters:
    - caliber: projectile diameter in millimeters
    - mass: projectile mass in kilograms
    - speed: muzzle velocity in meters per second
    - explosive_mass: weight of explosive filler in kilograms
    - apcbc: True if APCBC cap option is selected, False for uncapped AP

    Returns:
    - Penetration in millimeters, rounded to two decimal places.

    It's an equivalent of cstmWgCalcChellCaliber() in https://wiki.warthunder.com/jacob_de_marre
    """
    kfbr = 1900.0
    # percentage of filler relative to total shell mass
    tnt_pct = (explosive_mass / mass) * 100.0
    # cap factor: 1.0 if capped, 0.9 if uncapped
    cap_factor = 1.0 if apcbc else 0.9

    # filler penalty (knap) tiered function
    if tnt_pct <   0.65:
        knap = 1.0
    elif tnt_pct <   1.6:
        knap = 1.0 + (tnt_pct - 0.65) * (0.93 - 1.0) / (1.6 - 0.65)
    elif tnt_pct <   2.0:
        knap = 0.93 + (tnt_pct - 1.6) * (0.9  - 0.93) / (2.0 - 1.6)
    elif tnt_pct <   3.0:
        knap = 0.9  + (tnt_pct - 2.0) * (0.85 - 0.9)  / (3.0 - 2.0)
    elif tnt_pct <   4.0:
        knap = 0.85 + (tnt_pct - 3.0) * (0.75 - 0.85) / (4.0 - 3.0)
    else:
        knap = 0.75

    # de Marre formula core calculation
    pen = (
        (speed ** 1.43) * (mass ** 0.71) /
        ((kfbr ** 1.43) * ((caliber / 100.0) ** 1.07))
    ) * 100.0 * knap * cap_factor

    return round(pen, 2)

def parse_blkx_files(weapons_folder, units_folder, output_format, output_file=None, caliber_from_mm=280.0, caliber_to_mm=500.0):
    default_demarrePenetrationK = 1

    ship_weapon_map, ship_mod_map = build_ship_and_mod_maps(units_folder)
    br_map = load_br_values()

    json_output = [] if output_format == 'json' else None
    csv_output = [] if output_format == 'csv' else None
    output_lines = []

    if output_format == 'html':
        output_lines.append(' ')
        output_lines.append('<table class="sortable">')
        output_lines.append('  <thead>')
        output_lines.append('    <tr><th>Weapon</th><th>Bullet Name</th><th>Type</th><th>Ships</th><th>BR</th><th>Class</th><th>Caliber (mm)</th><th>Speed</th><th>Rate of Fire</th><th>Max Delta Angle</th><th>Max Delta Angle Vertical</th><th>Mass</th><th>Explosive Mass</th><th>Filler %</th><th>Fuse Delay (s)</th><th>Fuse Delay (m)</th><th>Explode Threshold</th><th>Jacob de Marre Pen 0° 0m</th><th>Cx</th><th>demarrePenetrationK</th></tr>')
        output_lines.append('  </thead>')
        output_lines.append('  <tbody>')
    elif output_format == 'csv':
        csv_headers = ['Weapon', 'Bullet Name', 'Type', 'Ships', 'BR', 'Class', 'Caliber (mm)', 'Speed', 'Rate of Fire', 'Max Delta Angle', 'Max Delta Angle Vertical', 'Mass', 'Explosive Mass', 'Filler %', 'Fuse Delay (s)', 'Fuse Delay (m)', 'Explode Threshold', 'Jacob de Marre Pen 0° 0m', 'Cx', 'demarrePenetrationK']
        csv_output.append(csv_headers)

    for blkx_file in Path(weapons_folder).glob("*.blkx"):
        try:
            with open(blkx_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                data = data[0] if len(data) == 1 and isinstance(data[0], dict) else {k:v for d in data if isinstance(d, dict) for k,v in d.items()}
            if not isinstance(data, dict):
                continue

            # Filter by Caliber
            default_bullet_stats = data.get("bullet", {})
            if isinstance(default_bullet_stats, list) and default_bullet_stats:
                default_bullet_stats = default_bullet_stats[0]

            caliber = default_bullet_stats.get("caliber", 0)
            weapon_type = data.get("weaponType", 0)
            if weapon_type != 0 or not (caliber_from_mm / 1000 <= caliber <= caliber_to_mm / 1000):
                continue

            # Identify Default Bullet
            default_bullet_name = default_bullet_stats.get("bulletName")
            weapon_filename = blkx_file.name.replace('.blkx', '.blk')

            # Iterate through all bullet types defined in the file
            for key, value in data.items():
                if isinstance(value, dict) and isinstance(value.get('bullet'), dict):
                    
                    current = value.get("bullet", {})
                                        
                    if isinstance(current, list):
                        flat = {}
                        for part in current:
                            if isinstance(part, dict):
                                flat.update(part)
                        current = flat
                    
                    bullet_name_from_data = current.get("bulletName", key)

                    ship_units = set()

                    # Case 1: The bullet is the weapon's default ammunition.
                    # Find all ships that have this weapon equipped by its filename.
                    if bullet_name_from_data == default_bullet_name:
                        ships_with_weapon = ship_weapon_map.get(weapon_filename, [])
                        ship_units.update(ships_with_weapon)

                    # Case 2: The bullet is an unlockable modification.
                    # Find ships that have this bullet's block name or bulletName as a modification.
                    ships_with_mod_by_key = ship_mod_map.get(key, [])
                    ship_units.update(ships_with_mod_by_key)
                    
                    ships_with_mod_by_name = ship_mod_map.get(bullet_name_from_data, [])
                    ship_units.update(ships_with_mod_by_name)

                    # Always output the bullet information, even if no ships are found.
                    weapon_name_str = translate_weapon_name(blkx_file.stem, round(caliber * 1000), output_format)
                    bullet_name_str = translate_bullet_name(bullet_name_from_data, output_format)
                    
                    filtered_ships = [u for u in sorted(list(ship_units)) if not u.endswith("_ec")]
                    ships_str_list = [translate_unit_name(u, output_format) for u in filtered_ships]



                    bullet_type = bullet_type_translation.get(current.get("bulletType", 0), value.get("bulletType", 0))
                    br_list = [br_map[u]/3+1 for u in filtered_ships if u in br_map]
                    
                    ship_types = [translate_unit_type(unit, output_format) for unit in filtered_ships]
                    
                    demarrePenetrationK = current.get("damage", {}).get("kinetic", {}).get("demarrePenetrationK", default_demarrePenetrationK)

                    try:
                        record = {
                            "weapon": weapon_name_str,
                            "bullet_name": bullet_name_str,
                            "bullet_type": bullet_type,
                            "ships": ships_str_list,
                            "battle_ratings": [round(b,1) for b in br_list],
                            "ship_types": ship_types,
                            "caliber_mm": round(caliber*1000),
                            "speed": round(current.get("speed", 0)),
                            "rate_of_fire": round(data.get("shotFreq", 0)*60, 2),
                            "max_delta_angle": data.get("maxDeltaAngle", 0),
                            "max_delta_angle_vertical": data.get("maxDeltaAngleVertical", 0),
                            "mass": current.get("mass", 0),
                            "explosive_mass": current.get("explosiveMass", 0),
                            "filler_percent": round((current.get("explosiveMass",0)/current.get("mass",1))*100,2),
                            "fuse_delay": current.get("fuseDelay", 0),
                            "fuse_delay_m": round(current.get("fuseDelay", 0) * current.get("speed", 0),1),
                            "explode_threshold": current.get("explodeTreshold",0),
                            "jacob_de_marre": round(demarrePenetrationK * jacob_de_marre_ap(caliber*1000, current.get("mass", 0), current.get("speed", 0), current.get("explosiveMass", 0), bullet_type_is_de_marre_apcbc.get(current.get("bulletType", 0), False) ),2),
                            "Cx": current.get("Cx", 0),
                            "demarrePenetrationK": demarrePenetrationK
                        }
                    except TypeError as e:
                        print(f"TypeError {e}")
                        print(weapon_name_str)
                        print(bullet_name_str)
                        print(current.get("bulletType", 0))
                        raise

                    if output_format == 'wikitext':
                        output_lines.append(f"|-\n| {weapon_name_str}\n| {bullet_name_str}\n| {bullet_type}\n| {', '.join(ships_str_list)}\n| {', '.join(str(br) for br in record['battle_ratings'])}\n| {', '.join(ship_types)}\n| {record['caliber_mm']}\n| {record['speed']}\n| {record['rate_of_fire']}\n| {record['max_delta_angle']}\n| {record['max_delta_angle_vertical']}\n| {record['mass']}\n| {record['explosive_mass']}\n| {record['filler_percent']}\n| {record['fuse_delay']}\n| {record['fuse_delay_m']}\n| {record['explode_threshold']}\n| {record['jacob_de_marre']}\n| {record['Cx']}\n| {record['demarrePenetrationK']}")
                    elif output_format == 'html':
                        output_lines.append(f"    <tr><td>{weapon_name_str}</td><td>{bullet_name_str}</td><td>{bullet_type}</td><td>{', '.join(ships_str_list)}</td><td>{', '.join(str(b) for b in record['battle_ratings'])}</td><td>{', '.join(ship_types)}</td><td>{record['caliber_mm']}</td><td>{record['speed']}</td><td>{record['rate_of_fire']}</td><td>{record['max_delta_angle']}</td><td>{record['max_delta_angle_vertical']}</td><td>{record['mass']}</td><td>{record['explosive_mass']}</td><td>{record['filler_percent']}</td><td>{record['fuse_delay']}</td><td>{record['fuse_delay_m']}</td><td>{record['explode_threshold']}</td><td>{record['jacob_de_marre']}</td><td>{record['Cx']}</td><td>{record['demarrePenetrationK']}</td></tr>")
                    elif output_format == 'json':
                        new_ships_records = []
                        for ship, br, stype in zip(record["ships"], record["battle_ratings"], record["ship_types"]):
                            new_ships_records.append({
                                "name": ship,
                                "battle_rating": br,
                                "type": stype
                            })
                        record['ships'] = new_ships_records
                        del record["battle_ratings"]
                        del record["ship_types"]
                        json_output.append(record)
                    elif output_format == 'csv':
                        csv_row = [
                            record['weapon'],
                            record['bullet_name'],
                            record['bullet_type'],
                            CSV_LISTSEPARATOR.join(record['ships']),
                            CSV_LISTSEPARATOR.join(str(b) for b in record['battle_ratings']),
                            CSV_LISTSEPARATOR.join(record['ship_types']),
                            record['caliber_mm'],
                            record['speed'],
                            record['rate_of_fire'],
                            record['max_delta_angle'],
                            record['max_delta_angle_vertical'],
                            record['mass'],
                            record['explosive_mass'],
                            record['filler_percent'],
                            record['fuse_delay'],
                            record['fuse_delay_m'],
                            record['explode_threshold'],
                            record['jacob_de_marre'],
                            record['Cx'],
                            record['demarrePenetrationK']
                        ]
                        csv_output.append(csv_row)
                # else:
                    # print(f"failed for key {key} - stem: {blkx_file.stem}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {blkx_file}")

    if output_format == 'html':
        output_lines.append('  </tbody>')
        output_lines.append('</table>')

    # Handle output to file or stdout
    if output_file:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            if output_format == 'json':
                json.dump(json_output, f, indent=2)
            elif output_format == 'csv':
                writer = csv.writer(f, delimiter=CSV_DELIMITER, lineterminator=CSV_LINETERMINATOR)
                writer.writerows(csv_output)
            else:  # wikitext or html
                f.write('\n'.join(output_lines))
        print(f"Output saved to {output_file}")
    else:
        # Output to stdout
        if output_format == 'json':
            print(json.dumps(json_output, indent=2))
        elif output_format == 'csv':
            writer = csv.writer(subprocess.sys.stdout, delimiter=CSV_DELIMITER, lineterminator=CSV_LINETERMINATOR)
            writer.writerows(csv_output)
        else:  # wikitext or html
            for line in output_lines:
                print(line)


def main():
    parser = argparse.ArgumentParser(description="Parse naval weapons data and output as table or JSON.")
    parser.add_argument('--weaponspath', required=True, help="Path to folder containing blk and blkx files of the weapons to parse, extracted from aces.vromfs.bin")
    parser.add_argument('--unitspath', required=False, help="Path to folder containing blk and blkx files of the units (e.g. ships), extracted from aces.vromfs.bin")
    parser.add_argument('--outputformat', choices=['wikitext', 'html', 'json', 'csv'], default='wikitext', help="Output format: wikitext, html, json, or csv")
    parser.add_argument('--filename', help="Output filename. Please, include desired file extension. If not provided, output will be printed in the command line")
    parser.add_argument('--rawnames', action='store_true', help="If set, skip all translations and output raw file, bullet, and unit names")
    parser.add_argument('--from', dest='caliber_from_mm', type=float, default=280, help="Minimum calibre (in millimeters) of the guns to be displayed (accepts int or float, e.g. --from 76.2)")
    parser.add_argument('--to', dest='caliber_to_mm', type=float, default=500, help="Maximum calibre (in millimeters) of the guns to be displayed (accepts int or float)")
    args = parser.parse_args()

    weapons_folder = args.weaponspath
    units_folder = args.unitspath
    output_format = args.outputformat
    output_file = args.filename
    caliber_from_mm = args.caliber_from_mm # 283 mm - Scharnhorst
    caliber_to_mm   = args.caliber_to_mm
    global RAW_NAMES
    RAW_NAMES = args.rawnames

    if not os.path.isdir(weapons_folder):
        print("Invalid weapons folder path.")
        return
    if units_folder and not os.path.isdir(units_folder):
        print("Invalid units folder path.")
        return

    unpack_blk_files(weapons_folder)
    if units_folder:
        unpack_blk_files(units_folder)
    unpack_blk_files(CHAR_CONFIG)
    unpack_blk_files(WEAPONSPRESETS)
    

    if not RAW_NAMES:
        global weapon_name_translation_dict
        global bullet_name_translation_dict
        global unit_name_translation_dict
        global unit_type_translation_dict
        weapon_name_translation_dict, bullet_name_translation_dict, unit_name_translation_dict, unit_type_translation_dict = load_translations()
    parse_blkx_files(weapons_folder, units_folder, output_format, output_file, caliber_from_mm, caliber_to_mm)

if __name__ == "__main__":
    main()

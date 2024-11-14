import os
import json
import subprocess
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Define the path to blk_unpack_ng.py and units_weaponry.csv
BLK_UNPACK_SCRIPT = "blk_unpack_ng.py"
UNITS_WEAPONRY_CSV = r"E:\Program Files (x86)\WarThunderDev\lang.vromfs.bin_u\lang\units_weaponry.csv"

# Load translations from CSV
file_name_translation_dict = {}
bullet_name_translation_dict = {}
if os.path.exists(UNITS_WEAPONRY_CSV):
    with open(UNITS_WEAPONRY_CSV, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                key = row[0]
                value = row[1]  # Only take the English translation, which is in the second column
                if key.startswith("weapons/"):
                    file_name_translation_dict[key.replace('weapons/', '')] = value
                else:
                    bullet_name_translation_dict[key] = value
else:
    print("Failed to find units_weaponry.csv in UNITS_WEAPONRY_CSV path!")
    exit(1)

file_name_further_translation = {
    "38 cm/52 SK C/34 (380 mm)": "SK L/45 (380 mm)",
}

bullet_type_translation = {
    "apc_tank": "APC",
    "apcbc_tank": "APCBC",
    "sap_tank": "SAP",
    "sapcbc_tank": "SAPCBC",
    "he_frag_tank": "HE",
    "he_frag_dist_fuse": "HE-TF",
    "he_frag_base_fuse_tank": "HE-BF"
}

def translate_file_name(file_name, caliber_value):
    name = file_name_translation_dict.get(file_name, file_name).replace(' cannon', '').replace(' gun', '').replace(', ', ' ')
    link = f"{name} ({caliber_value} mm)"
    
    return f"[[{file_name_further_translation.get(link, link)}|{name}]]"

def translate_bullet_name(bullet_name):
    return bullet_name_translation_dict.get(bullet_name, bullet_name)

def unpack_blk_file(blk_file):
    blkx_file = blk_file.with_suffix(".blkx")
    # If the blkx file does not exist, unpack the blk file
    if not blkx_file.exists():
        print(f"Unpacking {blk_file} to {blkx_file}")
        subprocess.run(["python", BLK_UNPACK_SCRIPT, str(blk_file)])

def unpack_blk_files(folder_path):
    # Get all blk files in the directory
    blk_files = list(Path(folder_path).glob("*.blk"))
    # Use ThreadPoolExecutor to run up to 5 instances in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(unpack_blk_file, blk_files)

def parse_blkx_files(folder_path):
    # Iterate through the blkx files in the directory
    for blkx_file in Path(folder_path).glob("*.blkx"):
        try:
            # Read and parse the JSON content
            with open(blkx_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ensure the root is either a dictionary or a list containing dictionaries
            if isinstance(data, list):
                if len(data) == 1 and isinstance(data[0], dict):
                    data = data[0]
                elif all(isinstance(item, dict) for item in data):
                    # If the entire object is packed inside an array, merge dictionaries
                    merged_data = {}
                    for item in data:
                        merged_data.update(item)
                    data = merged_data
                else:
                    print(f"Skipping file {blkx_file} as it does not contain a valid dictionary at the root level.")
                    continue

            if not isinstance(data, dict):
                print(f"Skipping file {blkx_file} as it does not contain a valid dictionary at the root level.")
                continue

            # Check if bullet.caliber exists, is greater than or equal to 0.3, and if weaponType != 0
            bullet = data.get("bullet", {})
            if isinstance(bullet, list):
                bullet = bullet[0] if bullet else {}

            caliber = bullet.get("caliber", 0)
            weapon_type = data.get("weaponType", 0)
            if caliber < 0.3 or weapon_type != 0:
                continue

            # Iterate through the nodes that contain objects
            for key, value in data.items():
                if isinstance(value, dict) and key not in ["attackShipsPriority", "bullet"]:
                    current_shell = value.get("bullet", {})
                    # Handle cases where current_shell might be a list
                    if isinstance(current_shell, list):
                        flattened_shell = {}
                        for shell_part in current_shell:
                            if isinstance(shell_part, dict):
                                flattened_shell.update(shell_part)
                        current_shell = flattened_shell

                    # Extract required values
                    file_name = blkx_file.stem
                    bullet_name = current_shell.get("bulletName", key)
                    bullet_type = current_shell.get("bulletType", 0)
                    caliber_value = round(caliber * 1000)
                    bullet_speed = round(current_shell.get("speed", 0))
                    cx_value = current_shell.get("Cx", 0)
                    shot_freq = round(data.get("shotFreq", 0) * 60, 2)
                    max_delta_angle = data.get("maxDeltaAngle", 0)
                    max_delta_angle_vertical = data.get("maxDeltaAngleVertical", 0)
                    mass = current_shell.get("mass", 0)
                    explosive_mass = current_shell.get("explosiveMass", 0)
                    filler_percentage = round((explosive_mass / mass) * 100, 2) if mass != 0 else 0
                    fuse_delay = current_shell.get("fuseDelay", 0)
                    explode_threshold = current_shell.get("explodeTreshold", 0)

                    # Translate values using CSV
                    file_name = translate_file_name(file_name, caliber_value)
                    bullet_name = translate_bullet_name(bullet_name)
                    bullet_type = bullet_type_translation.get(bullet_type, bullet_type)

                    # Print the formatted output
                    print(f"|-\n| {file_name}\n| {bullet_name}\n| {bullet_type}\n| {caliber_value}\n| {bullet_speed}\n| {cx_value}\n| {shot_freq}\n| {max_delta_angle}\n| {max_delta_angle_vertical}\n| {mass}\n| {explosive_mass}\n| {filler_percentage}\n| {fuse_delay}\n| {explode_threshold}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {blkx_file}")

def main():
    folder_path = input("Enter the path to the folder containing blk and blkx files: ").strip()
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return

    # Unpack blk files that do not have corresponding blkx files
    unpack_blk_files(folder_path)
    # Parse blkx files and print the required data
    parse_blkx_files(folder_path)

if __name__ == "__main__":
    main()

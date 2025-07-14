# War Thunder Wiki & Datamining Tools

This repository contains Python scripts for auditing the War Thunder Wiki and performing datamining in the game's files.

## Table of Contents

  * [Prerequisites](#prerequisites)
  * [Setup Guide](#setup-guide)
      * [Step 1: Install Required Tools](#step-1-install-required-tools)
      * [Step 2: Download and Install `wt-tools`](#step-2-download-and-install-wt-tools)
      * [Step 3: Unpack Game Files](#step-3-unpack-game-files)
  * [Script Usage](#script-usage)
      * [Naval Weapons Table Generator (`naval_weapons_table.py`)](#naval-weapons-table-generator-naval_weapons_tablepy)
      * [Wiki Article Checker (`wiki_check_articles.py`)](#naval-weapons-table-generator-naval_weapons_tablepy)
  * [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, you must install a few essential tools on your system.

  * **Python**: This is required to run the scripts.

      * **Download**: [python.org](https://www.python.org/downloads/)
          * The entire process was tested and developed on [Python 3.7](https://www.python.org/downloads/release/python-3717/).
      * **Important**: On the first page of the installer, make sure to check the box that says **"Add Python to PATH"**.

  * **Git**: This is a version control tool required to download `wt-tools` correctly.

      * **Download**: [git-scm.com](https://git-scm.com/downloads)

  * **A Text Editor**: You will need this to configure the `naval_weapons_table.py` script.

      * **Recommended**: [Notepad++](https://notepad-plus-plus.org/)

## Setup Guide

### Step 1: Install Required Tools

Install **Python** and **Git** from the links in the [Prerequisites](#prerequisites) section. Accept the default settings during installation.

### Step 2: Download and Install `wt-tools`

You must use Git to "clone" the `wt-tools` repository - [kotiq/wt-tools](https://github.com/kotiq/wt-tools.git). This ensures all files are downloaded correctly, avoiding installation errors. For a detailed guide on cloning, see [GitHub's official documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

> [!NOTE]
> The [official installation guide](https://github.com/kotiq/wt-tools?tab=readme-ov-file#installation) can be a bit misleading, as it appears to direct you to build executables, which is a complex process that I personally never managed to complete successfully on my machine. Instead, all the scripts here need are the `.py` files and their dependencies, which can be installed in a trivial way. (You can later use those `.py` files yourself, without worrying about compilation to `.exe`)

<details>
<summary>ℹ️ Installing wt-tools without issues: ℹ️</summary>

1.  Open your terminal (on Windows, open the Start Menu and type `PowerShell` or `cmd`).

2.  Navigate to a directory where you want to store the tools (e.g., your Documents folder).

    ```bash
    cd C:\Users\YourWindowsLogin\Documents
    ```

3.  Clone the repository by running the following command:

    ```bash
    git clone https://github.com/kotiq/wt-tools.git
    ```

    This will create a new `wt-tools` folder in your current directory.

4.  Navigate into the newly created folder:

    ```bash
    cd wt-tools
    ```

5.  Now, install the tool as a Python package using `pip`:

    ```bash
    pip install .
    ```

    This command reads the setup files and correctly installs `wt-tools` and its dependencies.
</details>

### Step 3: Unpack Game Files

With `wt-tools` installed, you can now unpack the necessary War Thunder game files.

1.  Open a new terminal window.
2.  Run the following commands, one by one. Remember to replace `"$LOCALAPPDATA"` with the actual path to where your game is installed.
    ```bash
    python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\aces.vromfs.bin"
    python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\lang.vromfs.bin"
    python vromfs_unpacker.py "$LOCALAPPDATA\WarThunder\char.vromfs.bin"
    ```
3.  This process will create folders ending in `_u` (e.g., `aces.vromfs.bin_u`) inside your game directory. These contain the unpacked data.

## Script Usage

### Naval Weapons Table Generator (`naval_weapons_table.py`)

Script used to generate [War Thunder Naval Weapons Table](https://jareelskaj.github.io/wt-wiki-tools/naval_weapons_table). You can download your own copy of the [naval_weapons_table.html](https://github.com/JareelSkaj/wt-wiki-tools/blob/main/docs/naval_weapons_table.html) and update `<table><!-- (...) --></table>` block to get your own personal table. The script can generate output in HTML, JSON, CSV or (default) wikitext. It has its own thread on the War Thunder forums: [Research into the naval guns - the naval weapons table](https://forum.warthunder.com/t/research-into-the-naval-guns-the-naval-weapons-table/251222).

1.  **Configure Paths**: Open `naval_weapons_table.py` with your text editor (e.g., Notepad++).

2.  **Edit the "Paths to files and scripts" section** at the top. Replace the placeholder paths with the correct, full paths on your computer.

> [!TIP]
> A sample path to Steam installation of War Thunder would look like `C:\Program Files (x86)\Steam\steamapps\common\WarThunder`. You can find it by right-clicking the game in your Steam library, choosing Properties -> Installed Files and then Browse next to "Size of installation: XX.XX GB on ...".

3.  **Save** the naval_weapons_table.py

4.  **Run from the Terminal**: After navigating to the directory containing `naval_weapons_table.py`, run the script with your desired arguments.

    **Sample Command:**

    ```bash
    python naval_weapons_table.py --weaponspath "C:\Users\YourWindowsLogin\AppData\Local\WarThunder\aces.vromfs.bin_u\gamedata\weapons\navalmodels_weapons" --unitspath "C:\Users\YourWindowsLogin\AppData\Local\WarThunder\aces.vromfs.bin_u\gamedata\units\ships" --outputformat html --from 75 --to 138.6
    ```

### Wiki Article Checker (`wiki_check_articles.py`)

> [!CAUTION]
> Does not work for [Wiki 3.0](https://wiki.warthunder.com/326-introducing-war-thunder-wiki-3-0). As of 2025 it can be run only on the https://old-wiki.warthunder.com/

This script checks articles on the War Thunder Wiki for missing sections. It requires no configuration.

To use it, run it from your terminal with the URL of the wiki category:

```bash
python wiki_check_articles.py "https://old-wiki.warthunder.com/Category:Sixth_rank_ships"
```

#### test_check_articles.py

An old collection of unit tests made to ensure that nothing breaks when any modifications to the scripts are being made. Irrelevant since the [Wiki 3.0](https://wiki.warthunder.com/326-introducing-war-thunder-wiki-3-0) got released.

## Troubleshooting

If you encounter an error, check this list for a solution.

  * **Error:** `'git'`, `'python'`, or `'pip'` **is not recognized...**

      * **Cause**: The tool was not added to your system's PATH.
      * **Solution**: Re-install the program (Git or Python) and make sure to check the box that says **"Add to PATH"** during the installation process.

  * **Error:** `Invalid weapons folder path`

      * **Cause**: Either the path after `--weaponspath` is missing quotes, or you're providing an incorrect path.
      * **Solution**: Correct the command you are using to run `naval_weapons_table.py`.

  * **Error:** `FileNotFoundError: [Errno 2] No such file or directory...`

      * **Cause**: A path in the configuration section of `naval_weapons_table.py` is incorrect.
      * **Solution**: The script could not find a file at the specified location. Carefully re-check every path you edited in the script for typos or incorrect folder names.

  * **Error:** `SyntaxError: invalid syntax`

      * **Cause**: A typo was made while editing the `.py` script, like accidentally deleting a quote (`"`), comma (`,`), changing indentation or removing line breaks.
      * **Solution**: Open `naval_weapons_table.py` and compare the lines you edited to the examples in this guide to find and fix the mistake.

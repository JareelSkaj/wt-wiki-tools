# War Thunder Wiki / Datamining tools

This repository contains a few scripts that I use for War Thunder Wiki or some datamining in the game.

# wt-tools
These scripts assume that you have wt-tools extracted at C:\wt-tools\wt-tools. Most importantly, these tools allow you to exctract the .vromfs.bin files (Virtual ROM file system) that are used by War Thunder to pack the content of the game. For the tools see: https://github.com/kotiq/wt-tools/tree/new-format 

# wiki_check_articles.py

A script that allows you to check entire categories of units for articles missing specific sections.
It outputs a percentage of articles and a list of them for:

- New Description Project
- Articles that are completely empty (i.e., articles with none of the sections filled with content)
- Articles that have only one section filled in (with the remainder empty)
- Articles that are nearly complete, with all but one section filled

Check the text file for a sample output under the Category: First rank ships.
The script does not check for the Media, See Also, or External Links sections. This exclusion is intentional to avoid unnecessary noise.
The script is designed to scan only unit articles. It is unpredictable for all other article types (e.g., weapons, families) and has not been tested on those. Primarily created for naval vessels—my area of interest—the script also has limited support for ground and air units (including helicopters and UCAVs).

It supports both nested subcategories (so you can run it for all naval/air/ground categories, though it takes significant time and may encounter wiki stability issues, resulting in potential 503 errors) and individual articles (primarily for testing purposes).

# test_check_articles.py

Collection of unit tests made to ensure that nothing breaks when any modifications to the scripts are being made.

# naval_weapons_table.py

A script that extracts overview of the Navy shells for https://wiki.warthunder.com/User:U12017485/Navy_Shells#Data_comparison_of_an_individual_shells

## Setup
* unpack `aces.vromfs.bin` and `lang.vromfs.bin`
* Path to `units_weaponry.csv` has to be inputted into `UNITS_WEAPONRY_CSV = "path"` in the source code
* Path to `blk_unpack_ng.py` has to be inputted into `BLK_UNPACK_SCRIPT = "path"` in the source code, or you can just put `naval_weapons_table.py` in your `\wt-tools\src\wt_tools` folder
## Running
```bash
python naval_weapons_table.py
```

# .py files

The `.py` files are Python scripts, so you’ll need to install Python and run them through the terminal/command line, as follows:
```bash
python wiki_check_articles.py "https://wiki.warthunder.com/Category:First_rank_ships"
```
or
```bash
python3 wiki_check_articles.py "https://wiki.warthunder.com/Category:First_rank_ships"
```
(you can check if you already have python installed by running `python --version` / `python3 --version`)
I tested it only on Windows, but in theory it should work fine on Mac and Linux as well. I think it should run on all versions of Python 3 just fine. If you don't have the required packages installed, the script will automatically tell you what you are missing and how to install it.

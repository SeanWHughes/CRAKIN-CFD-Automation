# -*- coding: utf-8 -*-
"""

Validate File For OS Function

This helper function takes a string and checks whether it is a valid
file (or directory) name and filepath for UNIX-like OS and Windows OS.

    Parameters:
    - name_or_filepath: the file name or the filepath
    - platform: the OS to validate for
    - strict: whether to throw an error if invalid or not

"""

#%%     INITIALIZE

import re
import unicodedata
import warnings
import os

class InvalidNameError(ValueError):
    pass

# Buffers for file name length and filepath length 
# This ccounts for operations that modify the filepath and/or name (e.g. a 
# {name}.solveout file adds to name length)
name_len_buff = 55
fp_len_buff = 50

#%%     UNIVERSAL DIRECTORY VALIDATION
    
def validate_file_for_OS(name_or_filepath: str,
                       platform: str = "both",
                       strict: bool = True
                       )-> bool:
    
    def _fail(msg: str, strict: bool = True):
        if strict:
            raise InvalidNameError(msg)
        return False
    
    # CHECK 1: Empty variable
    # Includes the absence of a value (None)
    if name_or_filepath is None:
        return _fail("Input name or filepath is None")
    
    # CHECK 2: Filepath is a root directory
    if re.fullmatch(r"([a-zA-Z]:[\\/]{1,2}|\\|/)", name_or_filepath):
        return _fail("Input name or filepath is a root directory")

    # ========== NORMALIZATION ==========
    # Convert inputs to string if not already
    name_or_filepath = str(name_or_filepath)
    platform = str(platform)
    
    # Convert inputs to Unicode if not already
    name_or_filepath = unicodedata.normalize("NFKD", name_or_filepath)
    platform = unicodedata.normalize("NFKD", platform)
    
    # Remove trailing separator for explicit directory inputs
    seps = ("/", "\\")
    if name_or_filepath.endswith(seps):
        name_or_filepath = name_or_filepath.rstrip(seps)
    
    # Convert platform input string to lowercase
    platform = platform.lower()
    
    # Detect if input is a file/directory name or a filepath, and split if fp
    if any(s in name_or_filepath for s in seps):
        filepath, name = os.path.split(name_or_filepath)
        if not filepath:
            filepath = os.path.sep  # Default placeholder
    else:
        filepath = os.path.sep
        name = name_or_filepath
    # ===================================
    
    # CHECK 3: Supported platform name
    if platform not in ("unix-like", "unix", "linux", "windows", "both"):
        return _fail(f"Invalid platform: {platform}. Must be 'unix-like','unix', 'linux', 'windows', or 'both'")

    # CHECK 4: Empty string
    # Includes whitespace string, empty string, 
    name_nospace = name.strip()
    filepath_nospace = filepath.strip()
    if not name_nospace:
        return _fail("Name is empty", strict)
    if not filepath_nospace:
        return _fail("Filepath is empty", strict)

    # CHECK 5: General Pre-processing software Null condition
    nots = r"(n *[/\.]? *a\.?|none|null|nan|nat|nil|empty)"
    nodefs = r"(undefined|not defined|unspecified|TBD|TBC|to be determined|to be defined)"
    excel_errors = r"#(NULL|DIV/0|VALUE|REF|NAME\?|NUM|N/A|SPILL|CALC|FIELD|BUSY)!?"
    infinity = r"[+\-\u00B1]?(inf|\u221E)"
    misc = r"(-+|\?+|\.{3,}|_+)"
    
    if re.fullmatch(rf"({nots}|{nodefs}|{excel_errors}|{infinity}|{misc})", name_nospace, re.IGNORECASE):
        return _fail("Name is some Null condition within pre-processing software")
    
    # CHECK 6: Multiple periods (warning)
    if name.count(".") > 1:
        warnings.warn(
            "Directory name contains multiple periods; "
            "this may cause issues in some workflows.",
            UserWarning
        )

#%%     UNIX-LIKE DIRECTORY VALIDATION

    if platform in ("unix-like","unix", "linux", "both"):
        # CHECK 1: Length
        # Max byte length for UNIX-like names and filepaths
        unixlike_max_name_Blen = 255 - name_len_buff
        unixlike_max_fp_Blen = 4096 - fp_len_buff
        
        # Approximate number of bytes in name and filepath within unix-like OS
        name_Blen = len(name.encode("utf-8"))
        fp_Blen = len(filepath.encode("utf-8"))
    
        # Compare name and filepath to max bytes
        if name_Blen > unixlike_max_name_Blen:
            return _fail(f"UNIX-like: Name too long ({name_Blen} > {unixlike_max_name_Blen})")
        if fp_Blen > unixlike_max_fp_Blen:
            return _fail(f"UNIX-like: Filepath too long ({fp_Blen} > {unixlike_max_fp_Blen})")
    
        # CHECK 2: UNIX-like filesystem-forbidden characters
        # Includes "/" and null byte
        if re.search(r"[\/\0]", name):
            return _fail("UNIX-like: Name contains forbidden characters")
    
        # CHECK 3: Characters that often break UNIX-like shell commands
        # Includes ";", "&", "'", "$", "[", "]", "(", and ")"
        if re.search(r"[*?<>;&`$![\]()]", name):
            return _fail("UNIX-like: Name contains shell-sensitive characters")
    
        # CHECK 4: Whitespace characters
        # Includes spaces, new lines ("\n"), tabs ("\t"), and other misc.
        # whitespace characters ("\v", "\r", "\f")
        if re.search(r"\s", name):
            return _fail("UNIX-like: Name contains whitespace characters")
    
        # CHECK 5: Leading dash
        if name.startswith("-"):
            return _fail("UNIX-like: Name starts with '-'")
    
        # CHECK 6: Reserved UNIX-like directory names
        if name in [".", ".."]:
            return _fail("UNIX-like: Name is a reserved directory name")
    
        # CHECK 7: Whitelist --> Only allow safest characters
        # Includes alphanumerics, "_", "-", and "."
        if re.search(r"[^a-zA-Z0-9_\-\.]", name):
            return _fail("UNIX-like: Contains unrecognized, potentially unsafe character(s)")

#%%     WINDOWS DIRECTORY VALIDATION

    if platform in ("windows", "both"):

        # CHECK 1: Length
        # Max length for Windows names and filepaths
        win_max_name_len = 260 - name_len_buff
        win_max_fp_len = 260 - fp_len_buff
        
        # Calculate name length
        name_len = len(name)
        fp_len = len(filepath)
        
        # Compare name and filepath to max characters
        if name_len > win_max_name_len:
            return _fail(f"Windows: Name too long ({name_len} > {win_max_name_len})")      
        if fp_len > win_max_fp_len:
            return _fail(f"Windows: Filepath too long ({fp_len} > {win_max_fp_len})")   

        # CHECK 2: Windows Filesystem-forbidden characters
        # Includes the null byte, "\", "/", ":", "*", "?", quotation marks, 
        #          "<", ">", and "|"
        if re.search(r"[\0\\\/:*?\"<>|]", name):
            return _fail("Windows: Name contains forbidden characters")
    
        # CHECK 3: Trailing period
        if name.endswith("."):
            return _fail("Windows: Name ends with period")
        
        # CHECK 4: Trailing or leading whitespace
        if len(name_nospace) != len(name):
            return _fail("Windows: Name contains trailing or leading spaces")
    
        # CHECK 5: Reserved Windows directory names
        if re.search(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", name, re.IGNORECASE):
            return _fail("Windows: Name is a reserved directory name")
        
        # CHECK 6: Whitelist --> Only allow safest characters
        # Includes alphanumerics, "_", "-", and "."
        if re.search(r"[^a-zA-Z0-9_\-\.]", name):
            return _fail("Windows: Contains unrecognized, potentially unsafe characters")
    
    return True
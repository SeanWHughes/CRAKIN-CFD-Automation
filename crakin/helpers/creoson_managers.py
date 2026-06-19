# -*- coding: utf-8 -*-
"""

A collection of OS functions for managing Creo|SON and/or Creo Parametric
connections and instances.

"""

#%%     IMPORT MODULES

import creopyson
import os
import time
import signal
import logging
import subprocess
import psutil
import re
import requests

#%%     CREO RUNNING CHECK

def is_creo_running_os() -> bool:
    """

    Is Creo Running On OS Function

    Checks if any Creo Parametric process is running on the OS, independent of 
    Creo|SON connection.

    """
    
    main_exes = ["parametric.exe", "creo.exe"]  # list of exact main executables

    for proc in psutil.process_iter(["name"]):
            try:
                pname = proc.info["name"].lower()
                if pname and pname in main_exes:
                    return True
                elif pname and pname.startwith("parametric"):
                    print(f"Potential Creo process found: {pname}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return False

#%%     STARTUP INITIALIZATION

def creoson_startup(CREO_MODEL_FP = str,
                    CREO_BATCH_FP = str,
                    CREOSON_BATCH_FP = str,
                    wait_time = 30,
                    display_model=False,
                    silent=False):
    
    """

    Creo|SON Startup Routine

    This helper function starts Creo, connects to Creo|SON, then opens and 
    activates a particular Creo CAD file and returns the Creo|SON client object.

        Parameters:
        - CREO_MODEL_FP: Filepath to the Creo CAD model file
        - CREO_BATCH_FP: Filepath to a .bat startup file for Creo
        - CREOSON_BATCH_FP: Filepath to a .bat startup file for Creo|SON
        - display_model: True if displaying Creo CAD model during execution
        - silent: True if startup checkpoint messages should be silenced

    """
    
    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig()
    
    # Silence all checkpoint info logs if desired (warnings persist)
    if silent:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
    
    # Remove the Creo model version number if input in the filepath (e.g. part.prt.22 --> part.prt)
    CREO_MODEL_FP = re.sub(r"\.\d+$", "", CREO_MODEL_FP)
    
    # Check if input filepath has a file extension at the end (a period following a "\" or "/")
    ext_match = re.search(r"[\\\/][^\\\/]+(\.[^\\\/]+)$", CREO_MODEL_FP)
    if not ext_match:
        raise ValueError(f"The input Creo CAD file does not have a file extension (e.g. .prt, .asm): \n{CREO_MODEL_FP}")
    
    # Check if file extension is natively supported by Creo
    file_ext = ext_match.group(1).lower()
    if file_ext not in [".prt", ".asm"]:
        logger.warning(f"User input Creo CAD file format ({file_ext}) is not a native Creo 3D CAD format (.prt or .asm) and is likely not supported")

    # Split filepaths
    CREO_MODEL_DIR, CREO_MODEL_NAME = os.path.split(CREO_MODEL_FP)
    CREOSON_BATCH_DIR, CREOSON_BATCH_NAME = os.path.split(CREOSON_BATCH_FP)
    
    # Check that there is a CAD filename in filepath
    if not CREO_MODEL_NAME:
        raise ValueError("CAD filename is empty")
    
    # Check that CAD file directory exists (can't check for filepath directly because of Creo part file version numbers)
    if not os.path.isdir(CREO_MODEL_DIR):
        raise ValueError(f"The CAD file directory could not be found: \n{CREO_MODEL_DIR}")
        
    # Check that Creo startup file exists
    if not os.path.exists(CREO_BATCH_FP):
        raise ValueError(f"The Creo .bat startup filepath could not be found: \n{CREO_BATCH_FP}")
        
    # Check that Creo|SON startup file exists
    if not os.path.exists(CREOSON_BATCH_FP):
        raise ValueError(f"The Creo|SON .bat startup filepath could not be found: \n{CREOSON_BATCH_FP}")

    # Run Creo|SON startup file
    init_wd=os.getcwd()             # Current working directory
    os.chdir(CREOSON_BATCH_DIR)     # Change to Creo|SON working directory
    os.startfile(CREOSON_BATCH_FP)  # Execute startup file
    os.chdir(init_wd)               # Switch working directory back
    
    # Create Creo|SON client object
    client = creopyson.Client()
    
#%%     STARTUP ROUTINE

    # Connect your machine to Creo|SON microserver (does nothing if already connected)
    try:
        client.disconnect()
        client.connect()
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Creo|SON: \n{exc}")
    logger.info("Creo|SON CHECKPOINT 1: \nConnected successfully to Creo|SON")

    # Check if Creo is already running and connected to Creo|SON, and start up Creo if not
    if not client.is_creo_running():
        try:
            client.start_creo(CREO_BATCH_FP)
        except Exception as exc:
            raise RuntimeError(f"Failed to launch Creo instance: \n{exc}")
 
    # Wait for Creo session to connect to Creo|SON (MAY FAIL)
    time.sleep(wait_time)
    
    try:
        client.is_creo_running()
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Creo within {wait_time}, consider increasing wait_time: {exc}")
    logger.info("Creo|SON CHECKPOINT 2: \nCreo is running")

    # Force change working directory to specified CAD part folder
    try:
        client.creo_cd(CREO_MODEL_DIR)
    except Exception as exc:
        raise RuntimeError(f"Failed to change working directory to specified CAD file directory:\n{exc}")
    logger.info(f"Creo|SON CHECKPOINT 3: \nCreo working directory changed to: \n{CREO_MODEL_DIR}")
    
    # Verify working directory changed correctly
    wd = client.creo_pwd()
    if os.path.normpath(wd) != os.path.normpath(CREO_MODEL_DIR):
        raise RuntimeError(f"Creo working directory mismatch: \nExpected: {CREO_MODEL_DIR} \nActual: {wd}")

    # Open model and activate it
    client.file_open(file_=CREO_MODEL_NAME, 
                     display=display_model, 
                     activate=True)

    # Check that specified CAD part is open in Creo
    if not client.file_exists(CREO_MODEL_NAME):
        raise ValueError(f"CAD part file does not exist or can't be found in current working directory: \n{CREO_MODEL_DIR}")
    if client.file_open_errors(CREO_MODEL_NAME):
        raise RuntimeError(f"There was an error trying to open the Creo model: \n{CREO_MODEL_NAME}")
    logger.info(f"Creo|SON CHECKPOINT 4: \nCreo model opened successfully: \n{CREO_MODEL_NAME}")

    return client

#%%    SHUTDOWN INITIALIZATION

def creoson_shutdown(client,
                     shutdown_creo=True,
                     shutdown_creoson=False,
                     silent=False):

    """
    
    Creo|SON Shutdown Routine

    This helper function checks if Creo is running, saves any open files, and 
    disconnects both the Creo session from Creo|SON and the machine from 
    the Creo|SON microserver.

        Parameters:
        - client: Creo|SON client object
        - shutdown_creo: True if Creo should be shut down
        - shutdown_creoson: True if Creo|SON should be disconnected
        - silent: True if startup checkpoint messages should be silenced
        
    """
    
    # Initialize logger
    logger = logging.getLogger(__name__)

    # Silence all checkpoint info logs if desired (warnings persist)
    if silent:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)
    
    creorun_check = True
    creoexe_check = True

    # Check if client object exists
    if client is None:
        client = creopyson.Client()

    # Verify connection to Creo|SON microserver
    client.connect()

    # Check if Creo session is connected to Creo|SON
    if not client.is_creo_running():
        creorun_check = False
        if not is_creo_running_os():
            creoexe_check = False
    
    logger.info("Creo|SON SHUTDOWN CHECKPOINT 1: \nCreo <--> Creo|SON connection verified")
    
#%%     SHUTDOWN ROUTINE

    # If a Creo instance is being executed but Creo|SON has not connected yet, wait for the connection
    if creoexe_check and not creorun_check:
        time.sleep(30)
        if not client.is_creo_running():
            logger.error("Creo|SON and Creo could not shut down properly")
            exit()
        creorun_check = True
            
    # Save all open modified files if Creo is running and connected to Creo|SON
    if creorun_check:
        try:
            # Create list of all open CAD files in Creo
            files = client.file_list()
            saved_files = []
            
            # If there are open CAD files, save them
            if files:
                for file_data in files:
                    file_name = file_data.get("file")
                    
                    # Attempt to save file and add to list if successful, otherwise exit function
                    try:
                        client.file_save(file_name)
                        saved_files.append(file_name)
                    except Exception as exc:
                        logger.error(f"Failed to save Creo CAD file during shutdown: \n{file_name} \n{exc}")
                        exit()
                if saved_files:
                    logger.info(f"Creo|SON SHUTDOWN CHECKPOINT 2: \nSaved Creo CAD files: {saved_files}")
            else:
                logger.info("Creo|SON SHUTDOWN CHECKPOINT 2: \nThere were no open Creo CAD files")
        except Exception as exc:
            logger.warning(f"Failed to retrieve open Creo CAD file list:\n{exc}")
    else:
        shutdown_creo = False
        logger.info("There is no current Creo session and Creo is not running")
        
    # Terminate Creo session if requested
    if shutdown_creo:
        try:
            client.stop_creo()
        except Exception as exc:
            raise RuntimeError(f"Failed to shut down Creo session:\n{exc}")

    # Wait for Creo process to terminate
    time.sleep(30)
    logger.info("Creo|SON SHUTDOWN CHECKPOINT 3: \nCreo shut down successfully")

    # Disconnect Creo|SON client
    try:
        client.disconnect()
    except Exception as exc:
        logger.warning(f"Failed to disconnect Creo|SON client cleanly:\n{exc}")

    logger.info("Creo|SON SHUTDOWN CHECKPOINT 4: \nDisconnected successfully from Creo|SON")

    return

"""
    # Terminate Creo|SON microserver connection if requested
    if shutdown_creoson:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "java.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as exc:
            logger.warning(f"Failed to terminate Creo|SON microserver:\n{exc}")

        logger.info("Creo|SON SHUTDOWN CHECKPOINT 5: \nCreo|SON microserver terminated")
"""
    
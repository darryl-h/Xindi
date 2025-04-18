#!/usr/bin/env python3
"""
This script checks Transmission via its RPC API and removes stalled torrents.
It does the following:
 1. Uses addedDate to wait for STABILIZATION_DELAY minutes after a torrent is added (for downloads).
 2. For torrents still downloading:
    - If there are zero peers connected, remove the torrent.
    - If the download rate is below MIN_DOWNLOAD_RATE (in KB/s) for at least MIN_RATE_DURATION minutes,
      remove the torrent.
 3. For completed torrents:
    - Uses doneDate to determine if a torrent has been complete for more than POST_COMPLETION_DELAY minutes
      and, if so, removes the torrent (data is kept).
Actions are logged to both the console and a log file. A CSV file is used to store state for low-rate torrents.

Installation:
Something like this in crontab to run every 5 minutes:
*/5 * * * * cd /home/user/transmission_scripts && ./manage_transmission.py
"""

import sys
import csv
import os
import logging
from datetime import datetime, timedelta

# Attempt to import the transmission_rpc module
try:
    from transmission_rpc import Client, TransmissionError
except ImportError:
    print(
        "The Python module 'transmission_rpc' is not installed.\n"
        "Please install it using pip by running one of the following commands:\n\n"
        "   pip install transmission-rpc\n\n"
        "or if you're using Python 3:\n\n"
        "   pip3 install transmission-rpc\n\n"
        "Then rerun the script."
    )
    sys.exit(1)

# --- Configuration Variables ---

# Transmission RPC settings
TRANSMISSION_HOST = "TRANSMISSION_IP"
TRANSMISSION_PORT = 9091
# If authentication is required, set these:
TRANSMISSION_USER = ""
TRANSMISSION_PASS = ""

# Time (in minutes) to wait after torrent is added before checking its stats (for downloading torrents)
STABILIZATION_DELAY = 15

# For torrents still downloading: if download rate < MIN_DOWNLOAD_RATE (in KB/s)
# for at least MIN_RATE_DURATION minutes, remove torrent.
MIN_DOWNLOAD_RATE = 25      # in KB/s
MIN_RATE_DURATION = 30      # minutes

# For completed torrents: remove the torrent (but not the data) if complete for more than:
POST_COMPLETION_DELAY = 30  # minutes

# Labels which, if present on a torrent, cause it to be completely ignored
# (no stalled checks, no post‐completion removal)
IGNORE_LABELS = {"keep", "no-auto-remove"}

# Path to CSV file for storing torrent state (low-rate start time)
STATE_CSV = "/home/osimages/transmission_scripts/transmission_state.csv"

# Enable debug logging? (DEBUG messages will appear if True, INFO messages always appear)
DEBUG = False

# Path to log file
LOG_FILE = "/home/osimages/transmission_scripts/logfile_transmission_manage.log"

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a")
    ]
)

# --- Utility Functions for State CSV Management ---
def load_state(csv_path):
    state = {}
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # keys: torrent_id, low_rate_start
                state[row["torrent_id"]] = row
    return state

def save_state(csv_path, state):
    fieldnames = ["torrent_id", "low_rate_start"]
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tid, row in state.items():
            row_to_write = {
                "torrent_id": tid,
                "low_rate_start": row.get("low_rate_start", "")
            }
            writer.writerow(row_to_write)

# --- Torrent Management ---
def remove_torrent(tc, torrent, state):
    """
    Remove a torrent from Transmission using its hash string.
    Logs an error if the hash string is not available.
    Also removes the torrent entry from the state dictionary if present.
    """
    torrent_hash = torrent.fields.get("hashString")
    if not torrent_hash:
        logging.error(f"Torrent {torrent.id} '{torrent.name}' has no hashString; cannot remove.")
        return False
    try:
        tc.remove_torrent(torrent_hash, delete_data=False)
        logging.info(f"Torrent {torrent.id} '{torrent.name}' removed successfully.")
        if str(torrent.id) in state:
            del state[str(torrent.id)]
        return True
    except Exception as ex:
        logging.error(f"Error removing torrent {torrent.id} '{torrent.name}': {ex}")
        return False

# --- Main Script ---
def main():
    try:
        tc = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT,
                    username=TRANSMISSION_USER or None, password=TRANSMISSION_PASS or None)
    except TransmissionError as e:
        logging.error(f"Error connecting to Transmission: {e}")
        return

    # Get all torrents
    try:
        torrents = tc.get_torrents()
    except TransmissionError as e:
        logging.error(f"Error retrieving torrents: {e}")
        return

    if not torrents:
        logging.info("No torrents found, nothing to do.")
        return

    # Load previous state from CSV (only low_rate_start is tracked)
    state = load_state(STATE_CSV)
    now = datetime.utcnow()

    for torrent in torrents:
        try:
            tid = str(torrent.id)
            name = torrent.name

            # Ignore label check
            labels = set(torrent.fields.get("labels", []))
            if labels & IGNORE_LABELS:
                logging.info(f"Torrent {tid} '{name}' has label(s) {labels & IGNORE_LABELS}; ignoring.")
                continue
         
            # Get attributes from the torrent's fields
            added_timestamp = torrent.fields.get("addedDate")
            if added_timestamp is None:
                logging.error(f"Torrent {tid} '{name}' has no addedDate; skipping.")
                continue
            added = datetime.utcfromtimestamp(added_timestamp)
            elapsed = (now - added).total_seconds() / 60.0  # minutes elapsed
            percent_done = torrent.fields.get("percentDone", 0.0)  # 0.0 to 1.0
            rate_dl = torrent.fields.get("rateDownload", 0) / 1024.0  # KB/s
            peers = torrent.fields.get("peersConnected", 0)

            # Prepare start and end time strings for logging
            start_time_str = added.isoformat()
            end_time_str = "N/A"
            if percent_done == 1.0:
                done_date = torrent.fields.get("doneDate")
                if done_date:
                    end_time_str = datetime.utcfromtimestamp(done_date).isoformat()

            # Log a summary for each torrent including start and (if available) end time
            logging.info(f"Torrent {tid} '{name}': Start: {start_time_str}, End: {end_time_str}, "
                         f"Elapsed: {elapsed:.1f} min, {percent_done*100:.1f}% done, "
                         f"Download rate: {rate_dl:.1f} KB/s, Peers: {peers}")

            # If the torrent is complete, process it using doneDate
            if percent_done == 1.0:
                done_date = torrent.fields.get("doneDate")
                if done_date:
                    done_dt = datetime.utcfromtimestamp(done_date)
                    complete_duration = (now - done_dt).total_seconds() / 60.0
                    if complete_duration >= POST_COMPLETION_DELAY:
                        logging.info(f"Torrent {tid} '{name}' has been complete for {complete_duration:.1f} minutes (threshold: {POST_COMPLETION_DELAY} min); removing torrent.")
                        remove_torrent(tc, torrent, state)
                        continue
                    else:
                        logging.info(f"Torrent {tid} '{name}' is complete, but only for {complete_duration:.1f} minutes; waiting for {POST_COMPLETION_DELAY - complete_duration:.1f} more minutes before removal.")
                else:
                    logging.error(f"Torrent {tid} '{name}' has no doneDate; cannot determine completion time.")
                # Skip further processing for complete torrents
                continue

            # For torrents that are still downloading:
            # Check if still within stabilization delay
            if elapsed < STABILIZATION_DELAY:
                logging.info(f"Torrent {tid} '{name}' is within stabilization delay ({elapsed:.1f} min); waiting for network to stabilize.")
                continue

            # Check for zero peers
            if peers == 0:
                logging.info(f"Torrent {tid} '{name}' has 0 peers (threshold: >0); removing torrent.")
                remove_torrent(tc, torrent, state)
                continue

            # Check for low download rate condition
            if rate_dl < MIN_DOWNLOAD_RATE:
                if tid not in state or not state[tid].get("low_rate_start"):
                    state.setdefault(tid, {})["low_rate_start"] = now.isoformat()
                    logging.info(f"Torrent {tid} '{name}' download rate ({rate_dl:.1f} KB/s) is below threshold ({MIN_DOWNLOAD_RATE} KB/s). Marking low_rate_start.")
                else:
                    low_rate_start = datetime.fromisoformat(state[tid]["low_rate_start"])
                    low_rate_duration = (now - low_rate_start).total_seconds() / 60.0
                    if low_rate_duration >= MIN_RATE_DURATION:
                        logging.info(f"Torrent {tid} '{name}' has been below threshold for {low_rate_duration:.1f} minutes; removing torrent.")
                        remove_torrent(tc, torrent, state)
                        continue
                    else:
                        logging.info(f"Torrent {tid} '{name}' has been below threshold for {low_rate_duration:.1f} minutes; waiting for {MIN_RATE_DURATION - low_rate_duration:.1f} more minutes.")
            else:
                # Clear any low_rate_start flag if download rate improved
                if tid in state and state[tid].get("low_rate_start"):
                    logging.info(f"Torrent {tid} '{name}' download rate improved to {rate_dl:.1f} KB/s; clearing low_rate_start flag.")
                    state[tid]["low_rate_start"] = ""

        except Exception as ex:
            logging.error(f"Error processing torrent {torrent.id}: {ex}")

    # Save state back to CSV (only low_rate_start is persisted)
    save_state(STATE_CSV, state)

if __name__ == "__main__":
    main()

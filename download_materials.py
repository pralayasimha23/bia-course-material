"""
BIA SharePoint File Downloader
Opens a visible browser for 1-time Microsoft login to save session cookies,
then automatically downloads all class notes, slides, notebooks, and datasets
into lessons/<lesson_folder>/files/
"""

import os
import sys
import json
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"
AUTH_FILE = BASE_DIR / "sharepoint_auth.json"
DATA_FILE = BASE_DIR / "curriculum_data.json"

TARGET_SHAREPOINT_FOLDER = "https://bostoninstituteofanalyti399-my.sharepoint.com/personal/corporateofficeindia_bostoninstituteofanalytics_org/Documents/BIA%20-%20Default/Academics/HTC-AUG2026-DSAI-1"

def login_and_save_session():
    print("=" * 70)
    print("STEP 1: Microsoft SharePoint Authentication")
    print("A browser window will open.")
    print("Please log in to your Microsoft account if prompted.")
    print("Once SharePoint loads, the script will automatically continue.")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(f"Navigating to SharePoint directory: {TARGET_SHAREPOINT_FOLDER}")
        page.goto(TARGET_SHAREPOINT_FOLDER)

        # Wait for user to log in and reach SharePoint
        print("Waiting for login to complete (timeout: 3 minutes)...")
        max_wait = 180
        start = time.time()
        logged_in = False

        while time.time() - start < max_wait:
            curr_url = page.url
            title = page.title()
            # If we reached SharePoint and not in login.microsoftonline.com
            if "sharepoint.com" in curr_url and "login.microsoftonline.com" not in curr_url and "Sign in" not in title:
                print(f"Login detected! Page title: {title}")
                logged_in = True
                page.wait_for_timeout(3000)
                break
            time.sleep(2)

        if not logged_in:
            print("Login timed out or not completed. Please try again.")
            browser.close()
            return False

        # Save cookies / storage state
        context.storage_state(path=str(AUTH_FILE))
        print(f"Session saved successfully to {AUTH_FILE}")
        browser.close()
        return True


def download_all_materials():
    if not AUTH_FILE.exists():
        print(f"Auth file not found at {AUTH_FILE}. Running login first...")
        if not login_and_save_session():
            return

    if not DATA_FILE.exists():
        print(f"Data file not found at {DATA_FILE}!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    lectures = data.get("allLectures", [])
    print(f"\nProcessing {len(lectures)} lectures for file downloads...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(AUTH_FILE),
            accept_downloads=True
        )
        page = context.new_page()

        downloaded_count = 0
        total_files = 0

        for lec in lectures:
            lec_num = lec.get("lecNumber")
            topic = (lec.get("topic") or "Lesson").strip()
            materials = lec.get("lectureMaterial") or []

            if not materials:
                continue

            # Identify lesson folder
            clean_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in topic).strip().replace(" ", "_").upper()[:60]
            folder_name = f"{lec_num:02d}_{clean_name}" if lec_num is not None else clean_name
            lesson_dir = LESSONS_DIR / folder_name
            files_dir = lesson_dir / "files"
            files_dir.mkdir(parents=True, exist_ok=True)

            for m in materials:
                file_name = m.get("file")
                link = m.get("link")
                if not file_name:
                    continue

                total_files += 1
                dest_path = files_dir / file_name

                if dest_path.exists() and dest_path.stat().st_size > 0:
                    print(f"[{folder_name}] Already exists: {file_name} ({dest_path.stat().st_size} bytes)")
                    downloaded_count += 1
                    continue

                print(f"[{folder_name}] Downloading {file_name}...")
                
                # Determine download URL
                download_url = None
                if link and "Doc.aspx" in link:
                    download_url = link.replace("action=default", "action=download").replace("action=edit", "action=download")
                    if "action=download" not in download_url:
                        download_url += "&action=download"
                else:
                    # Construct direct URL from SharePoint folder
                    download_url = f"{TARGET_SHAREPOINT_FOLDER}/{urllib.parse.quote(file_name)}"

                try:
                    with page.expect_download(timeout=25000) as download_info:
                        page.goto(download_url)
                    dl = download_info.value
                    dl.save_as(str(dest_path))
                    print(f"  --> Saved: {file_name} ({dest_path.stat().st_size} bytes)")
                    downloaded_count += 1
                except Exception as e:
                    # Try navigating directly or clicking download if present
                    try:
                        resp = page.request.get(download_url)
                        if resp.status == 200 and len(resp.body()) > 500 and not resp.body().startswith(b"<!DOCTYPE"):
                            with open(dest_path, "wb") as out_f:
                                out_f.write(resp.body())
                            print(f"  --> Downloaded via direct request: {file_name} ({len(resp.body())} bytes)")
                            downloaded_count += 1
                        else:
                            print(f"  [WARN] Failed to download {file_name}: {e}")
                    except Exception as err2:
                        print(f"  [WARN] Could not download {file_name}: {err2}")

        browser.close()

    print("\n" + "=" * 70)
    print(f"Download Finished! Total files processed: {total_files} | Downloaded: {downloaded_count}")
    print("=" * 70)


if __name__ == "__main__":
    if not AUTH_FILE.exists() or "--login" in sys.argv:
        success = login_and_save_session()
        if success:
            download_all_materials()
    else:
        download_all_materials()

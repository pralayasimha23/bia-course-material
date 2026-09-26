"""
BIA CampusConnect Automated Curriculum & Session Archiver
Synchronizes all completed and scheduled lectures, class notes, SharePoint recording links,
and materials from Boston Institute of Analytics CampusConnect portal.
"""

import os
import re
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BIAArchiver")

# Environment configurations
BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"
LESSONS_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_URL = os.getenv("BIA_LOGIN_URL", "https://campusconnect.bostoninstituteofanalytics.org/")
CALENDAR_URL = os.getenv("BIA_CALENDAR_URL", "https://campusconnect.bostoninstituteofanalytics.org/academic-calendar")
EMAIL = os.getenv("BIA_EMAIL", "pralayasimha@yahoo.com")
PASSWORD = os.getenv("BIA_PASSWORD", "SrijaSimha@143")


def clean_filename(text: str) -> str:
    """Sanitize strings for folder and file names."""
    if not text:
        return "UNNAMED"
    clean = re.sub(r'[\/\\:\*\?"<>\|\n\r\t]+', '_', text).strip()
    clean = re.sub(r'[\s_]+', '_', clean)
    clean = clean.strip('_')
    return clean[:60] if clean else "UNNAMED"


def sync_curriculum(headless=True):
    logger.info("=" * 70)
    logger.info(f"Starting BIA Curriculum Sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"User Email: {EMAIL}")
    logger.info("=" * 70)

    intercepted_lectures = None
    intercepted_dashboard = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            nonlocal intercepted_lectures, intercepted_dashboard
            try:
                if "all_lecture_details" in response.url and response.status == 200:
                    data = response.json()
                    if data.get("success") and "allLectures" in data.get("data", {}):
                        intercepted_lectures = data["data"]["allLectures"]
                        logger.info(f"Intercepted {len(intercepted_lectures)} lectures from API.")
                elif "api/student/dashboard" in response.url and response.status == 200:
                    data = response.json()
                    if data.get("success"):
                        intercepted_dashboard = data.get("data", {})
                        logger.info("Intercepted student dashboard details from API.")
            except Exception:
                pass

        page.on("response", handle_response)

        try:
            # 1. Login
            logger.info(f"Navigating to {LOGIN_URL}...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            if "/student-dashboard" not in page.url:
                logger.info("Submitting credentials...")
                email_input = page.locator("#email, input[type='text'][placeholder*='Email' i], input[type='email']").first
                email_input.wait_for(state="visible", timeout=15000)
                email_input.fill(EMAIL)

                password_input = page.locator("#password, input[type='password']").first
                password_input.wait_for(state="visible", timeout=15000)
                password_input.fill(PASSWORD)

                submit_btn = page.locator("button[type='submit']:has-text('Sign In'), button:has-text('Sign In with Email')").first
                submit_btn.click()
                logger.info("Login submitted. Waiting for dashboard...")
                page.wait_for_timeout(4000)

            # 2. Navigate to Calendar page
            logger.info(f"Navigating to Academic Calendar: {CALENDAR_URL}...")
            page.goto(CALENDAR_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)

            # Wait if lectures not yet captured
            retries = 0
            while intercepted_lectures is None and retries < 5:
                logger.info("Waiting for all_lecture_details API response...")
                page.wait_for_timeout(3000)
                retries += 1

        except Exception as e:
            logger.error(f"Navigation or login error: {e}")
        finally:
            browser.close()

    if not intercepted_lectures:
        # Fallback to local cached data if available
        cache_file = BASE_DIR / "curriculum_data.json"
        if cache_file.exists():
            logger.warning(f"Using cached curriculum_data.json from {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
                intercepted_lectures = cached.get("allLectures", [])
                intercepted_dashboard = cached.get("dashboard", {})
        else:
            logger.error("Failed to fetch lecture data from BIA portal and no cache found.")
            sys.exit(1)

    # Save full raw dataset
    raw_payload = {
        "last_synced": datetime.now().isoformat(),
        "total_lectures": len(intercepted_lectures),
        "dashboard": intercepted_dashboard or {},
        "allLectures": intercepted_lectures
    }
    with open(BASE_DIR / "curriculum_data.json", "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2, ensure_ascii=False)
    logger.info("Saved raw dataset to curriculum_data.json")

    # Build lessons folders and files
    build_lessons(intercepted_lectures, intercepted_dashboard)


def build_lessons(all_lectures, dashboard_data):
    logger.info(f"Processing and organizing {len(all_lectures)} lessons...")

    completed_count = 0
    total_recordings_count = 0
    total_materials_count = 0
    index_rows = []

    # General class notes root link from dashboard
    general_class_notes_link = (dashboard_data or {}).get("classNotes", "https://bostoninstituteofanalyti399-my.sharepoint.com/")

    for lec in all_lectures:
        lec_num = lec.get("lecNumber")
        topic = (lec.get("topic") or "Lesson").strip()
        tag = (lec.get("session_tag") or "UNKNOWN").strip().upper()
        status = lec.get("status", 0)
        planned_date = lec.get("plannedDate") or lec.get("sessionplannedDate") or "Date not set"
        actual_date = lec.get("actualDate")
        trainer = lec.get("actualTrainerName") or lec.get("plannedTrainerName") or "To be assigned"
        hours = lec.get("hours") or "3 Hours"
        venue = lec.get("venue") or "To be announced"
        meeting_link = lec.get("meetingLink")
        raw_video_str = lec.get("videoLink") or ""
        video_links = [v.strip() for v in raw_video_str.split(",") if v.strip()]
        materials = lec.get("lectureMaterial") or []
        subtopics_raw = (lec.get("subTopic") or lec.get("subtopic") or "").strip()
        subtopics = [s.strip() for s in subtopics_raw.split("\n") if s.strip()]

        is_completed = tag in ["COMPLETED", "TODAY"] or status == 1 or len(video_links) > 0 or len(materials) > 0

        if is_completed:
            completed_count += 1
            total_recordings_count += len(video_links)
            total_materials_count += len(materials)

        # Folder name: e.g. "01_INDUCTION", "03_FUNDAMENTALS_OF_EXCEL"
        clean_topic_name = clean_filename(topic).upper()
        folder_name = f"{lec_num:02d}_{clean_topic_name}" if lec_num is not None else clean_topic_name
        lesson_folder = LESSONS_DIR / folder_name
        lesson_folder.mkdir(parents=True, exist_ok=True)

        # 1. Lesson README.md
        readme_lines = [
            f"# Lesson #{lec_num:02d}: {topic}",
            "",
            f"**Status:** `{tag}` | **Date:** {planned_date} | **Duration:** {hours}",
            "",
            "## 📌 Session Overview",
            "| Field | Details |",
            "| :--- | :--- |",
            f"| **Lesson Number** | #{lec_num} |",
            f"| **Topic** | {topic} |",
            f"| **Status** | `{tag}` |",
            f"| **Planned Date** | {planned_date} |",
            f"| **Actual Date** | {actual_date or planned_date} |",
            f"| **Trainer** | {trainer} |",
            f"| **Venue** | {venue} |",
        ]
        if meeting_link:
            readme_lines.append(f"| **Teams Meeting** | [Join Teams Meeting]({meeting_link}) |")
        readme_lines.append("")

        # Subtopics
        readme_lines.append("## 📚 Covered Subtopics")
        if subtopics:
            for s in subtopics:
                readme_lines.append(f"- {s}")
        else:
            readme_lines.append("*No subtopics outlined for this session.*")
        readme_lines.append("")

        # Lecture Recordings
        readme_lines.append("## 🎥 Lecture Recordings")
        if video_links:
            readme_lines.append(f"Total parts recorded: **{len(video_links)}**")
            readme_lines.append("")
            for idx, v in enumerate(video_links, 1):
                readme_lines.append(f"- [▶️ Watch Recording Part {idx}]({v})")
        else:
            readme_lines.append("*No recording links uploaded for this session yet.*")
        readme_lines.append("")

        # Class Notes & Materials
        readme_lines.append("## 📝 Class Notes & Lecture Materials")
        if materials:
            readme_lines.append("| Type | File Name | Link / Download |")
            readme_lines.append("| :--- | :--- | :--- |")
            for m in materials:
                m_file = m.get("file", "File")
                m_type = m.get("materialType", "Material")
                m_link = m.get("link", general_class_notes_link)
                m_ext = m.get("extension", "file").upper()
                readme_lines.append(f"| `{m_ext}` ({m_type}) | `{m_file}` | [Open in SharePoint]({m_link}) |")
        else:
            readme_lines.append(f"*No individual files attached. General batch materials can be viewed in the [SharePoint Academics Directory]({general_class_notes_link}).*")
        readme_lines.append("")

        with open(lesson_folder / "README.md", "w", encoding="utf-8") as f:
            f.write("\n".join(readme_lines) + "\n")

        # 2. recordings.md
        rec_lines = [
            f"# Lecture Recordings - #{lec_num:02d} {topic}",
            "",
            f"- **Date:** {planned_date}",
            f"- **Trainer:** {trainer}",
            f"- **Total Parts:** {len(video_links)}",
            "",
            "### Direct SharePoint Video Links",
        ]
        if video_links:
            for idx, v in enumerate(video_links, 1):
                rec_lines.append(f"{idx}. [Lecture Recording Part {idx}]({v})")
        else:
            rec_lines.append("*Recordings not yet published.*")
        with open(lesson_folder / "recordings.md", "w", encoding="utf-8") as f:
            f.write("\n".join(rec_lines) + "\n")

        # 3. materials.md
        mat_lines = [
            f"# Class Notes & Materials - #{lec_num:02d} {topic}",
            "",
            f"- **Batch Folder:** [BIA Academics SharePoint Directory]({general_class_notes_link})",
            "",
            "### Attached Documents",
        ]
        if materials:
            for m in materials:
                m_file = m.get("file")
                m_link = m.get("link")
                m_type = m.get("materialType")
                mat_lines.append(f"- **{m_file}** ({m_type}): [View / Download]({m_link})")
        else:
            mat_lines.append("*No files attached to this session.*")
        with open(lesson_folder / "materials.md", "w", encoding="utf-8") as f:
            f.write("\n".join(mat_lines) + "\n")

        # 4. lesson.json
        with open(lesson_folder / "lesson.json", "w", encoding="utf-8") as f:
            json.dump(lec, f, indent=2, ensure_ascii=False)

        # Add to index row
        relative_path = f"lessons/{folder_name}"
        status_badge = f"`{tag}`" if tag in ["COMPLETED", "TODAY"] else tag
        rec_col = f"[{len(video_links)} Videos]({relative_path}/recordings.md)" if video_links else "-"
        mat_col = f"[{len(materials)} Files]({relative_path}/materials.md)" if materials else "-"
        index_rows.append(
            f"| #{lec_num:02d} | {planned_date} | [{topic}]({relative_path}/README.md) | {trainer} | {status_badge} | {rec_col} | {mat_col} |"
        )

    # Master Root README.md
    master_readme = [
        "# 🎓 BIA CampusConnect - Academic Curriculum & Archive",
        "",
        "> Automated repository containing structured class notes, SharePoint lecture recordings, and syllabus tracking for Boston Institute of Analytics (BIA) **Data Science & Artificial Intelligence (DSAI)** program.",
        "",
        "## 📊 Curriculum Statistics",
        f"- **Batch:** `HTC-AUG2026-DSAI-1`",
        f"- **Total Curriculum Lectures:** {len(all_lectures)}",
        f"- **Completed / Active Lessons:** {completed_count}",
        f"- **Total Recorded Video Parts:** {total_recordings_count}",
        f"- **Total Attached Materials/Notes:** {total_materials_count}",
        f"- **Last Synchronized:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}`",
        "",
        "## 🗓️ Master Class Schedule & Archive Index",
        "",
        "| # | Date | Topic | Trainer | Status | Recordings | Notes/Materials |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    master_readme.extend(index_rows)
    master_readme.extend([
        "",
        "---",
        "",
        "## 🔄 Automation & GitHub Actions",
        "This archive is updated automatically **every Monday** using GitHub Actions (`.github/workflows/sync_curriculum.yml`).",
        "",
        "### Manual Run",
        "You can run the sync locally at any time:",
        "```bash",
        "pip install -r requirements.txt",
        "playwright install chromium",
        "python sync_curriculum.py",
        "```",
        "",
        "Or trigger it manually via the **GitHub Actions** tab in this repository by selecting `BIA Weekly Curriculum Sync` -> `Run workflow`.",
        "",
        "### Secrets Required for GitHub Actions",
        "- `BIA_EMAIL`: User login email (`pralayasimha@yahoo.com`)",
        "- `BIA_PASSWORD`: User login password",
    ])

    with open(BASE_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(master_readme) + "\n")

    logger.info("=" * 70)
    logger.info(f"Curriculum Sync Completed Successfully!")
    logger.info(f"Processed: {len(all_lectures)} lectures ({completed_count} completed/active)")
    logger.info(f"Total Video Recordings: {total_recordings_count}")
    logger.info(f"Total Materials: {total_materials_count}")
    logger.info("=" * 70)


if __name__ == "__main__":
    is_headless = "--headed" not in sys.argv
    sync_curriculum(headless=is_headless)

import os
import shutil
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"
ZIP_PATH = BASE_DIR / "materials_archive.zip"
ALL_MATERIALS_DIR = BASE_DIR / "all_materials"
ALL_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

# Map filenames to lesson folders
LESSON_MAPPING = {
    # Excel
    "IF_IFS_VLOOKUP_Practice.xlsx": "03_FUNDAMENTALS_OF_EXCEL",
    "Sales_Charts_Insights.xlsx": "04_ADVANCED_EXCEL",
    "Superstore-Final.xls": "04_ADVANCED_EXCEL",

    # SQL
    "08_INTRODUCTIONTOSQLBASICQUERYING.pptx": "07_INTRODUCTION_TO_SQL_&_BASIC_QUERYING",
    "Sales_Database.sql": "07_INTRODUCTION_TO_SQL_&_BASIC_QUERYING",
    "Login_Database.sql": "07_INTRODUCTION_TO_SQL_&_BASIC_QUERYING",
    "09_ADVANCEDSQLCONCEPTDATAMANUPULATION.pptx": "08_ADVANCED_SQL_CONCEPT_&_DATA_MANUPULATION",
    "Sales_SQL_Answer_Key.docx": "08_ADVANCED_SQL_CONCEPT_&_DATA_MANUPULATION",
    "Sales_SQL_Questionnaire.docx": "08_ADVANCED_SQL_CONCEPT_&_DATA_MANUPULATION",

    # BI
    "Meridian_Consulting_Sales_Pipeline_Data.xlsx": "11_POWER_BI",

    # Python Basics
    "01_INTRODUCTIONTOPYTHONBASICS.pptx": "13_INTRODUCTION_TO_PYTHON_BASICS",
    "IntroductiontoPython.ipynb": "13_INTRODUCTION_TO_PYTHON_BASICS",

    # Data Structures
    "03_DATASTRUCTURE-1-LISTANDTUPLE.pptx": "15_DATA_STRUCTURE_-_1_LIST_AND_TUPLE",
    "DataStructure1.ipynb": "15_DATA_STRUCTURE_-_1_LIST_AND_TUPLE",
    "04_DATASTRUCTURE-2-DICTIONARYANDSETS.pptx": "16_DATA_STRUCTURE_-_2_DICTIONARY_AND_SETS",
    "Datastructure2.ipynb": "16_DATA_STRUCTURE_-_2_DICTIONARY_AND_SETS",

    # NumPy
    "06_NUMPYFUNDAMENTALS.pptx": "17_INTRODUCTION_TO_NUMPY",
    "NUMPYFUNDAMENTALS.ipynb": "17_INTRODUCTION_TO_NUMPY",
    "NumPy-CaseStudyImageProcessing.ipynb": "17_INTRODUCTION_TO_NUMPY",
    "NumPy_Lecture_Notes.docx": "17_INTRODUCTION_TO_NUMPY",
    "beach.jpg": "17_INTRODUCTION_TO_NUMPY",
    "eagle.jpeg": "17_INTRODUCTION_TO_NUMPY",

    # Pandas & Data Visualization
    "07_DATAMANIPULATIONWITHPANDASDATAVISUALIZATION1.pptx": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "DataManipulationwithpandasandDataVisualization.ipynb": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "DataManipulationwithPandasVisualization.ipynb": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "data.csv": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "ny_weather.csv": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "professors.csv": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "students.csv": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
    "ecommerce_sales_analytics_5000.xlsx.csv": "18_INTRODUCTION_TO_PANDAS_AND_DATA_VISUALIZATION",
}

print(f"Extracting {ZIP_PATH}...")
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    for member in z.infolist():
        if member.is_dir():
            continue
        filename = Path(member.filename).name
        
        # 1. Save copy to all_materials
        target_all = ALL_MATERIALS_DIR / filename
        with z.open(member) as source, open(target_all, "wb") as target:
            shutil.copyfileobj(source, target)
        print(f"Saved to all_materials: {filename} ({target_all.stat().st_size} bytes)")

        # 2. Save copy to matching lesson folder
        lesson_folder_name = LESSON_MAPPING.get(filename)
        if lesson_folder_name:
            target_lesson_dir = LESSONS_DIR / lesson_folder_name / "files"
            target_lesson_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_lesson_dir / filename
            with z.open(member) as source, open(target_file, "wb") as target:
                shutil.copyfileobj(source, target)
            print(f"  -> Routed to {lesson_folder_name}/files/{filename}")

print("\nAll materials extracted and organized successfully!")

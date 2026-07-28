# These are all required utils for agent to execute main code

import os
import pandas as pd
import sys
import subprocess


def load_csv_safely(file_or_path):
    """Safely load a CSV file by trying multiple encodings (utf-8, latin1, cp1252, etc.)."""
    encodings_to_try = ["utf-8", "latin1", "cp1252", "utf-8-sig", "ISO-8859-1"]
    for enc in encodings_to_try:
        try:
            if hasattr(file_or_path, "seek"):
                file_or_path.seek(0)
            return pd.read_csv(file_or_path, encoding=enc)
        except Exception:
            continue

    # Final fallback replacing un-decodable bytes
    if hasattr(file_or_path, "seek"):
        file_or_path.seek(0)
    return pd.read_csv(file_or_path, encoding="utf-8", encoding_errors="replace")


def file_handler(action, path=None, content=None):
    """Centralized file I/O for the pipeline.
    
    Actions:
        'read_csv'   -> Reads a CSV safely and returns (df, profile_str)
        'save_code'  -> Writes generated Python code to a .py file
        'cleanup'    -> Removes a file if it exists
        'save_csv'   -> Saves a DataFrame to CSV (used by Streamlit download)
    """
    if action == "read_csv":
        try:
            df = load_csv_safely(path)
            profile_str = (
                f"Columns: {df.columns.tolist()}\n"
                f"Shape: {df.shape[0]} rows x {df.shape[1]} cols\n"
                f"Dtypes:\n{df.dtypes.to_string()}\n"
                f"Sample Data:\n{df.head(2).to_markdown()}"
            )
            return df, profile_str
        except Exception as e:
            return None, f"Error reading file: {e}"

    elif action == "save_code":
        filepath = path or "workspace_cleaner.py"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    elif action == "cleanup":
        if path and os.path.exists(path):
            os.remove(path)
            return True
        return False

    elif action == "save_csv":
        content.to_csv(path, index=False)
        return path

    else:
        raise ValueError(f"Unknown file_handler action: {action}")


def code_runner(script_path="workspace_cleaner.py", timeout=30):
    """Execute a Python script as a subprocess and return structured results."""
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"Script timed out after {timeout} seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }


def metrics(original_path, cleaned_path="final_cleaned_data.csv"):
    """Compare original vs cleaned data and return quality metrics."""
    try:
        df_original = load_csv_safely(original_path)
        df_cleaned = load_csv_safely(cleaned_path)

        return {
            "original": {
                "rows": len(df_original),
                "cols": len(df_original.columns),
                "nulls": int(df_original.isnull().sum().sum()),
                "duplicates": int(df_original.duplicated().sum()),
            },
            "cleaned": {
                "rows": len(df_cleaned),
                "cols": len(df_cleaned.columns),
                "nulls": int(df_cleaned.isnull().sum().sum()),
                "duplicates": int(df_cleaned.duplicated().sum()),
            },
            "delta": {
                "rows_removed": len(df_original) - len(df_cleaned),
                "nulls_fixed": int(df_original.isnull().sum().sum() - df_cleaned.isnull().sum().sum()),
                "duplicates_removed": int(df_original.duplicated().sum() - df_cleaned.duplicated().sum()),
                "columns_added": len(df_cleaned.columns) - len(df_original.columns),
            }
        }
    except Exception as e:
        print(f"Metrics error: {e}")
        return None
import os
import pandas as pd
from io import StringIO

# Build an absolute file path relative to this file's location.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "export.csv")

def load_data():
    """
    Load export CSV file while ignoring comment lines.
    """
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("//")]
    return pd.read_csv(StringIO("".join(filtered_lines)))

def filter_trips_by_attributes(filters):
    """
    Filter rows from export.csv based on a dictionary of filters.
    For each key (column), if a non-empty value is provided:
      - For numeric columns, an equality match is attempted.
      - Otherwise, a case-insensitive substring match is used.
    """
    data = load_data()
    for col, val in filters.items():
        if val:
            try:
                num_val = float(val)
                data = data[data[col] == num_val]
            except ValueError:
                data = data[data[col].astype(str).str.contains(val, case=False, na=False)]
    return data

def main():
    # Define the list of columns (attributes from export.csv) you want to filter.
    filter_columns = ["position", "title", "rating", "price", "type", "address",
                      "operating_hours", "phone", "website", "description"]
    filters = {}
    for col in filter_columns:
        user_input = input(f"Enter filter for '{col}' (press Enter to skip): ")
        filters[col] = user_input.strip()
    filtered_data = filter_trips_by_attributes(filters)
    print(filtered_data)

if __name__ == "__main__":
    main()

import pandas as pd
from io import StringIO

FILE_PATH = "Travel details dataset.csv"

def load_data():
    """
    Load travel details dataset while ignoring comment lines.
    """
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("//")]
    return pd.read_csv(StringIO("".join(filtered_lines)))

def filter_trips_by_attributes(filters):
    """
    Filter trips based on a dictionary of filters.
    For each key (column), if a non-empty value is provided, the rows will be filtered accordingly.
    For numeric columns, an equality match is attempted; for other types, a case-insensitive substring match is used.
    """
    data = load_data()
    for col, val in filters.items():
        if val:
            # Try numeric equality first
            try:
                num_val = float(val)
                data = data[data[col] == num_val]
            except ValueError:
                data = data[data[col].astype(str).str.contains(val, case=False, na=False)]
    return data

def main():
    df = load_data()
    filters = {}
    # Prompt user to enter filter criteria for every attribute
    for col in df.columns:
        user_input = input(f"Enter filter for '{col}' (press Enter to skip): ")
        filters[col] = user_input.strip()
    filtered_trips = filter_trips_by_attributes(filters)
    print(filtered_trips)

if __name__ == "__main__":
    main()

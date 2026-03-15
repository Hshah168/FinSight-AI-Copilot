import pandas as pd
import os

def load_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(filepath)
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f'Unsupported file type: {ext}')
    print(f'Loaded {len(df):,} rows from {os.path.basename(filepath)}')
    return df
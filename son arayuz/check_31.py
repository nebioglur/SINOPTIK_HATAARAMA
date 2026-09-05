import pandas as pd
import warnings
warnings.filterwarnings('ignore')

f = r"C:\Users\nebio\Desktop\check\SinTum ocak 2026.xls"
df = pd.read_excel(f, sheet_name=None, header=None)

for sheet_name, data in df.items():
    # Only 31.01 sheet which might be "Sheet62" or "31.01.2026"
    if "31" in sheet_name or sheet_name == "Sheet62":
        print(f"--- SHEET {sheet_name} ---")
        print(data.head(20))

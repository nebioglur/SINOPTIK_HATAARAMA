import sys
import os
import datetime
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mgm_monitor.readers.selenium_reader import fetch_and_parse_xls_with_selenium

def p_callback(progress, msg):
    print(f"[{progress}%] {msg}")

try:
    bas = datetime.datetime.now() - datetime.timedelta(days=1)
    bit = datetime.datetime.now()
    
    print("Testing fetch_and_parse_xls_with_selenium...")
    df_sin, df_metar = fetch_and_parse_xls_with_selenium(17244, 'KONYA MEYDAN', bas, bit, p_callback=p_callback)
    
    print(f"Sinoptik DataFrame: {type(df_sin)}")
    print(f"Metar DataFrame: {type(df_metar)}")
except Exception as e:
    traceback.print_exc()

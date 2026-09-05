import sys
import tkinter as tk
import traceback
import os

sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
os.chdir(r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")

import arayuz

root = tk.Tk()
# Mute tkinter error popups if possible or just let them show.
# Try calling the function
try:
    arayuz.aylik_rapor_olustur(run_async=False)
except Exception as e:
    print("ERROR CAUGHT:")
    traceback.print_exc()

# Exit immediately
sys.exit(0)

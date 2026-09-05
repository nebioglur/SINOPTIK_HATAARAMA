import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

options = webdriver.EdgeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
options.add_argument("--disable-features=msSmartScreenProtection,msEdgeInsecureDownloadProtection")
base_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(base_dir, "check_test")
if not os.path.exists(temp_dir): os.makedirs(temp_dir)
prefs = {
    "download.default_directory": temp_dir,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": False,
    "safebrowsing.disable_download_protection": True,
    "smartscreen.enabled": False,
}
options.add_experimental_option("prefs", prefs)

try:
    driver = webdriver.Edge(options=options)
    driver.get('http://kardelen.mgm.gov.tr/bultenler/Sinoptik/SinGoster.aspx?ist=17244&istIsim=KARAPINAR')
    driver.find_element(By.NAME, 'ctl00$cBody$btnYukle').click()
    
    wait = WebDriverWait(driver, 15)
    time.sleep(3)
    
    print('Clicking Export...')
    export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@title='Export' or @title='export' or @alt='Export' or @alt='export' or contains(@title, 'Export') or contains(@title, 'export') or contains(@title, 'Aktar') or contains(@title, 'aktar')]")))
    export_btn.click()
    
    time.sleep(2)
    driver.save_screenshot('screenshot_export_menu.png')
    
    print('Clicking Excel...')
    excel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Excel') or contains(text(), 'excel') or contains(@title, 'Excel') or contains(@title, 'excel') or contains(., 'Excel') or contains(., 'excel')]")))
    excel_btn.click()
    
    print('Waiting for download...')
    time.sleep(10)
    print('Files in temp_dir:', os.listdir(temp_dir))
    driver.quit()
except Exception as e:
    traceback.print_exc()

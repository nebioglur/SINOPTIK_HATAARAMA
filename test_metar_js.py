import traceback
from selenium import webdriver
import time
import os

options = webdriver.EdgeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
options.add_argument("--disable-features=msSmartScreenProtection,msEdgeInsecureDownloadProtection")
base_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(base_dir, "check_test2")
if not os.path.exists(temp_dir): os.makedirs(temp_dir)
prefs = {
    "download.default_directory": temp_dir,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)

try:
    driver = webdriver.Edge(options=options)
    print("Navigating...")
    driver.get('http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx?ist=17244&istIsim=KONYA+MEY')
    
    time.sleep(2)
    from selenium.webdriver.common.by import By
    print("Clicking btnYukle...")
    driver.find_element(By.NAME, 'ctl00$cBody$btnYukle').click()
    
    print("Waiting 5s for table to load...")
    time.sleep(5)
    
    js_script = """
    try {
        var rv = $find('ctl00_cBody_rpw');
        if (!rv) return "Error: ReportViewer not found";
        if (rv.get_isLoading()) return "Error: Still loading";
        var exportBtn = document.getElementById('ctl00_cBody_rpw_ctl05_ctl04_ctl00_ButtonImg');
        if (!exportBtn) return "Error: Export button not found in DOM";
        if (exportBtn.src.indexOf('ExportDisabled') !== -1) return "Error: Export button disabled";
        rv.exportReport('Excel');
        return "Success";
    } catch(e) {
        return "Exception: " + e.toString();
    }
    """
    print("Executing JS...")
    res = driver.execute_script(js_script)
    print("JS Result:", res)
    
    print('Waiting 30s for download...')
    time.sleep(30)
    print('Files in temp_dir:', os.listdir(temp_dir))
    driver.quit()
except Exception as e:
    traceback.print_exc()

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1280,1024')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    url = "http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx?ist=17020&istIsim=ADANA"
    driver.get(url)
    
    # Dates
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasGun")).select_by_value("1")
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasAy")).select_by_value("7")
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasYil")).select_by_value("2026")
    
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddBitisGun")).select_by_value("28")
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisAy")).select_by_value("7")
    Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisYil")).select_by_value("2026")
    
    # Metar Turu: Tum
    try:
        driver.find_element(By.XPATH, "//input[@name='ctl00$cBody$rdList' and @value='tum']").click()
    except:
        pass
        
    driver.find_element(By.NAME, "ctl00$cBody$btnYukle").click()
    time.sleep(5)
    
    driver.save_screenshot("adana_metar.png")
    
    print("Screenshot saved to adana_metar.png")
    
finally:
    driver.quit()

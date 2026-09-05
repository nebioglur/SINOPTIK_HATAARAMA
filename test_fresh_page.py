import sys
sys.path.append(r'c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA')
from selenium import webdriver
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=options)

driver.get('http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx?ist=17244&istIsim=KONYA+MEY')

try:
    lbl = driver.find_element(By.ID, 'cBody_lblGoster')
    print('lblGoster text:', lbl.text)
except Exception as e:
    print('Not found')

try:
    print('JS Result:', driver.execute_script("return typeof ('ctl00_cBody_rpw')"))
except Exception as e:
    print('JS Error')

driver.quit()

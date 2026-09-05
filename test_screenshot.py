import sys, time
sys.path.append(r'c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=options)

driver.get('http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx?ist=17244&istIsim=KONYA+MEY')

Select(driver.find_element(By.NAME, 'ctl00$cBody$ddBasGun')).select_by_value('1')
Select(driver.find_element(By.NAME, 'ctl00$cBody$ddBasAy')).select_by_value('7')
Select(driver.find_element(By.NAME, 'ctl00$cBody$ddBasYil')).select_by_value('2026')

Select(driver.find_element(By.NAME, 'ctl00$cBody$ddBitisGun')).select_by_value('15')
Select(driver.find_element(By.NAME, 'ctl00$cBody$ddbitisAy')).select_by_value('7')
Select(driver.find_element(By.NAME, 'ctl00$cBody$ddbitisYil')).select_by_value('2026')

driver.find_element(By.XPATH, "//input[@name='ctl00$cBody$rdList' and @value='tum']").click()
driver.find_element(By.NAME, 'ctl00$cBody$btnYukle').click()

print('Clicked Yukle, waiting 20s...')
for i in range(20):
    time.sleep(1)
    print(f'Waiting... {i+1}s')

driver.save_screenshot('metar_screenshot.png')
print('Screenshot saved as metar_screenshot.png')
driver.quit()

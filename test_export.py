from selenium import webdriver
from selenium.webdriver.common.by import By
import time

options = webdriver.EdgeOptions()
options.add_argument('--headless=new')
driver = webdriver.Edge(options=options)
driver.get('http://kardelen.mgm.gov.tr/bultenler/Sinoptik/SinGoster.aspx?ist=17244&istIsim=KARAPINAR')

print("Clicking Yukle...")
driver.find_element(By.NAME, 'ctl00$cBody$btnYukle').click()
time.sleep(5)

print("Searching for Export button...")
elements = driver.find_elements(By.XPATH, '//*[@title]')
for e in elements:
    if 'Export' in e.get_attribute('title') or 'Excel' in e.get_attribute('title'):
        print('TITLE MATCH:', e.get_attribute('title'), e.tag_name, e.get_attribute('id'))

selects = driver.find_elements(By.TAG_NAME, 'select')
for s in selects:
    print('SELECT:', s.get_attribute('id'), s.text.replace('\n', '|'))

links = driver.find_elements(By.TAG_NAME, 'a')
for a in links:
    if 'Excel' in a.text or 'Export' in a.text or 'Dışa Aktar' in a.text or 'xls' in a.text.lower():
        print('LINK:', a.text, a.get_attribute('id'), a.get_attribute('href'))

html = driver.page_source
with open('singoster_full_rendered.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done!')
driver.quit()

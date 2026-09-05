from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get("http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx")
    select_element = driver.find_element(By.NAME, "ctl00$cBody$ddIstasyonlar")
    options = select_element.find_elements(By.TAG_NAME, "option")
    for opt in options:
        text = opt.text
        if 'ADANA' in text.upper():
            print(f"FOUND ADANA: {text} - {opt.get_attribute('value')}")
        if 'KONYA' in text.upper():
            print(f"FOUND KONYA: {text} - {opt.get_attribute('value')}")
finally:
    driver.quit()

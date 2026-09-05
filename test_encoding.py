import requests
from bs4 import BeautifulSoup

url = 'http://kardelen.mgm.gov.tr/bultenler/Sinoptik/SinGoster.aspx?ist=17244&istIsim=KONYA+MEYDAN'
s = requests.Session()
r = s.get(url)
soup = BeautifulSoup(r.content, 'html.parser', from_encoding='windows-1254')

vs = soup.find('input', {'name': '__VIEWSTATE'})['value']
vsg = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
ev = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
btn = soup.find('input', {'name': 'ctl00$cBody$btnYukle'})['value']

payload = {
    '__VIEWSTATE': vs,
    '__VIEWSTATEGENERATOR': vsg,
    '__EVENTVALIDATION': ev,
    'ctl00$cBody$ddBasGun': '1',
    'ctl00$cBody$ddBasAy': '7',
    'ctl00$cBody$ddBasYil': '2026',
    'ctl00$cBody$ddBitisGun': '15',
    'ctl00$cBody$ddbitisAy': '7',
    'ctl00$cBody$ddbitisYil': '2026',
    'ctl00$cBody$btnYukle': btn
}

r2 = s.post(url, data=payload)
print(r2.headers)

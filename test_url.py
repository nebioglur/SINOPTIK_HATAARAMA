import requests
import re
url = 'http://kardelen.mgm.gov.tr/bultenler/Sinoptik/SinGoster.aspx?ist=17244&istIsim=KONYA+MEYDAN'
s = requests.Session()
r = s.get(url)
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, 'html.parser')
vs = soup.find('input', {'name': '__VIEWSTATE'})['value']
vsg = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
ev = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

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
    'ctl00$cBody$btnGoster': 'Göster'
}
r2 = s.post(url, data=payload)
print(re.findall(r'/Reserved\.ReportViewerWebControl\.axd\?[^\"\'\s]+', r2.text))

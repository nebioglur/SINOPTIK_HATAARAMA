import urllib.request
import re
html = urllib.request.urlopen('http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx').read().decode('utf-8')
matches = re.findall(r'<option value=\"(.*?)\">(.*?)</option>', html)
for m in matches:
    print(f'{m[0]} - {m[1]}')

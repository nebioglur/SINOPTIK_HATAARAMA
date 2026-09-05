import glob, os

files = glob.glob('c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\*.py')
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.readlines()
            for i, line in enumerate(content):
                if 'Sonuülar' in line or ('Sonu' in line and 'ülar' in line):
                    print(f'{os.path.basename(f)}:{i} - {line.strip()}')
                
                # Check for other insert values
                if 'insert' in line and 'BİLGİ' in line:
                    print(f'{os.path.basename(f)}:{i} - {line.strip()}')
    except:
        pass

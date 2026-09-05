# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('arayuz_tavsiye.txt', 'w', encoding='utf-8') as out:
    for i in range(760, 785):
        out.write(repr(lines[i]) + '\n')

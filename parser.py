import pandas as pd
import csv
import re

# Read and parse csv
# Encoding in utf-8 to solve back to line probleme in champ 11742
df = []
with open('Export_stutzmann_horae_t65_Work.csv', newline='', encoding='utf-8') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        #print(', '.join(row))
        df.append(row)

# Extraction of useful text whithout blank for text_reuse
d1 = [item[5] for item in df]
d1plus = []
for x in d1:
    if x:
        d1plus.append(x)

# faire des statistiques descriptives:
# nombre de textes,
nb_texte = len(d1plus)-1 #-1 pour la ligne de titre
print("Number of texts : ", nb_texte)

# longueur moyenne,
compt = 0

for d in d1plus:
    #compt+=len(d.split())#.split() to compt word and not char
    res = len(re.findall(r'\w+', d))
    for i in d.split():
        if i == "<p>" or i == "/>" or i == "<br/>": # not counting tag as words
            res -= 1
    compt += res

mn_word = compt/nb_texte
print("Mean of the words :", mn_word)

# longueur mini,
min = len(d1plus[2].split())

for d in d1plus:
    res = len(re.findall(r'\w+', d))
    for i in d.split():
        if i == "<p>" or i == "/>" or i == "<br/>":  # not counting tag as words
            res -= 1

    if res < min : min = res

print("The minimal length :", min)

# longueur max,
max = len(d1plus[2].split())
save = 0

for d in d1plus:
    res = len(re.findall(r'\w+', d))
    for i in d.split():
        if i == "<p>" or i == "/>" or i == "<br/>":  # not counting tag as words
            res -= 1

    if res > max : max = res

print("Th maximum length :", max)




#print(len(save))
#print(d1plus[8108])

s = "Miserere, quaeso, clementissime </p>deus<p> , <p> <br /> <br/>"
#print(len(s.split()))
li = ['<p>','</p>']
#r = s.split('<p>')
#r = r.split('</p>')
#r = r.split('<br/>')
#r = r.split('<br />')
r = re.split(' <p> | </p> | /> | <br | <br/> | , | . ', s)
print(r)
"""
res = len(re.findall(r'\w+', s))
for i in s.split():
    if i == "<p>" or i == "/>" or i == "<br/>":
        res -= 1
print(res)
#print(len(d1plus[345]))
#print(len(d1plus[345].split()))
# variance de la longueur en nombre de mots,
# nombre de mots différents,
# liste des 100 mots les plus fréquents
# 100 mots les moins fréquents

# print(type(df))"""



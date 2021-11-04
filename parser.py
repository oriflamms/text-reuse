# Importation of the library
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

#parse the file
df = pd.read_csv('Export_stutzmann_horae_t65_Work.csv')


#extract useful reference texts for text_reuse
df_text = df[["Text"]]


#refraction of the text
df_text = df_text.dropna()
df_text = df_text.reset_index()

for index, row in df_text.iterrows():
    row['Text'] = row['Text'].replace("</p>", " ")
    row['Text'] = row['Text'].replace("<p>", " ")
    row['Text'] = row['Text'].replace("<br/>", " ")
    row['Text'] = row['Text'].replace("<br />", " ")
    row['Text'] = row['Text'].replace("...", " ")
    row['Text'] = row['Text'].replace(",", " ")


#descriptive statistics:
# number of texts,
nb_text = len(df_text)
print("Number of text : ", nb_text)


# average length,
df_text['new'] = df_text['Text'].str.split().str.len()
avg_length = df_text['new'].sum()/nb_text
print("Average of words :", avg_length)


# minimum length,
min_length = df_text["new"].min()
print("Minimum length : ", min_length)


# maximum length,
max_length = df_text["new"].max()
print("Maximum length : ", max_length)


# variance of the length in number of words,
var_length = df_text["new"].var()
print("Variance of length : ", var_length)


# number of different words,
df_text['Text'].str.lower().str.split()
list_word = set()
df_text['Text'].str.lower().str.split().apply(list_word.update)
nb_diff_word = len(list_word)
print("Number of different word : ", nb_diff_word)


# list of the 100 most frequent words and 100 least frequent words
most_freq_word = Counter(" ".join(df_text["Text"]).split()).most_common(100)
print("Most frequent word : ", most_freq_word)


# list of the 100 least frequent words
least_freq_word = Counter(" ".join(df_text["Text"]).split()).most_common(100)[:-100-1:-1]
print("Least frequent word : ", least_freq_word)


# distribution graph
df_text.boxplot(column='new')
#df_text.hist(column='new')
plt.show()

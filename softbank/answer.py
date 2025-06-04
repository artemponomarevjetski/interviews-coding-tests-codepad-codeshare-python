example = "neural network deep neural network deep learning network"
sentence = "Repeating a word, any word in English is incorrect syntactically."
empty=""

import regex
def find_frequent_words(sen):
    delimiters= ['.', ',', '!', '?']
    if sen=='':
        print("Empty sentence.")
        return {}

    arr_str=re.func_delimit(sen, delimiters)
    cleaned=[]
    for word in arr_str:
        if '.' == list(word)[-1]:
            word=word[:len(word)-1]
            cleaned.append(word)
        elif ',' == list(word)[-1]:
            word=word[:len(word)-1]
            cleaned.append(word)
        else:
            cleaned.append(word)
    hist={}
    for word in cleaned:
        if word not in hist.keys():
            hist[word]=1
        else:
            hist[word]+=1
    hist1 = {}
    for key, val in hist.items():
        hist1[key]=val/len(cleaned)

    return hist1


print(find_frequent_words(sentence))
print()
print()

dict1=find_frequent_words(example)
print(dict1)

print(sorted(dict1.values()))

threshold=0.25
for word, freq in dict1.items():
    if freq>threshold:
        print(word)

print()
print()

print(find_frequent_words(empty))

O(len_s)

~O(n)
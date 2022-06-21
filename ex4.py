def convert_to_piglatin(string ):
    word_arr=string.split(' ')
    for w in word_arr:
        if len(str.strip(w)):
            ch=w[0]
            if(ch == 'a' or ch == 'e' or ch == 'i' 
               or ch == 'o' or ch == 'u' or ch == 'A' or ch == 'E' or ch == 'I' or ch == 'O' 
               or ch == 'U'):
                piglatin=w+"-way"  
                print(piglatin)
            else:
                piglatin=w[1:]
                piglatin+="-"+ch+"ay"
                print(piglatin, end = ' ')
            
    
for i in range(5):
    # read word
    convert_to_piglatin(input())
    print()

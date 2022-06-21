def validate_brackets(code):  
    stemp=''
    i=0
    for s in code:
        if i==0:
            stemp+=s
        else:
            if s in ['<', '{', '}', '>', '(' , ')', '[', ']']:
                if s=='<':
                    stemp+=s
                elif s=='>': 
                    if len(stemp)>0:
                        if stemp[-1]=='<':
                            stemp=stemp[:-1]
                        else:
                            stemp+=s
                elif s=='(':
                    stemp+=s
                elif s==')': 
                    if len(stemp)>0:
                        if stemp[-1]=='(':
                            stemp=stemp[:-1]
                        else:
                            stemp+=s
                elif s==']': 
                    if len(stemp)>0:
                        if stemp[-1]=='[':
                            stemp=stemp[:-1]
                        else:
                            stemp+=s
                elif s=='[':
                    stemp+=s
                elif s=='}': 
                    if len(stemp)>0:
                        if stemp[-1]=='{':
                            stemp=stemp[:-1]
                        else:
                            stemp+=s
                else:
                    stemp+=s
        i+=1

    if len(stemp)!=0:
        print('Java code is invalid')
    else:
        print('Java code is valid')

while True:
    validate_brackets(input())

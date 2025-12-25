import random

complexity = 1.0
try:
    while True:
        a = 0
        b = 100
        x = random.randint(a, b)
        y = random.randint(a, b)
        
        print(f"{x} * {y} = ?")
        
        z = input()
        correct_answer = x * y
        
        if z.isdigit() and int(z) == correct_answer:
            print('correct')
        else:
            print('incorrect')
            print(f'it should be {correct_answer}')
            
except (EOFError, KeyboardInterrupt):
    print("\nGoodbye!")
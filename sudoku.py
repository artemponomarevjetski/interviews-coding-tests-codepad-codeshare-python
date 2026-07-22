# Determine if a 9 x 9 Sudoku board is valid. Only the filled cells need to be validated according to the following rules:

#  Each row must contain the digits 1-9 without repetition.

#  Each column must contain the digits 1-9 without repetition.

#  Each of the nine 3 x 3 sub-boxes of the grid must contain the digits 1-9 without repetition.

#  Note:

#  A Sudoku board (partially filled) could be valid but is not necessarily solvable.

#  Only the filled cells need to be validated according to the mentioned rules.

board =[["5","3","3",".","7",".",".",".","."]
 ,["6",".",".","1","9","5",".",".","."]
 ,[".","9","8",".",".",".",".","6","."]
 ,["8",".",".",".","6",".",".",".","3"]
 ,["4",".",".","8",".","3",".",".","1"]
 ,["7",".",".",".","2",".",".",".","6"]
 ,[".","6",".",".",".",".","2","8","."]
 ,[".",".",".","4","1","9",".",".","5"]
 ,[".",".",".",".","8",".",".","7","9"]]


print(board)

board1 =[["8","3",".",".","7",".",".",".","."]
 ,["6",".",".","1","9","5",".",".","."]
 ,[".","9","8",".",".",".",".","6","."]
 ,["8",".",".",".","6",".",".",".","3"]
 ,["4",".",".","8",".","3",".",".","1"]
 ,["7",".",".",".","2",".",".",".","6"]
 ,[".","6",".",".",".",".","2","8","."]
 ,[".",".",".","4","1","9",".",".","5"]
 ,[".",".",".",".","8",".",".","7","9"]]

print(board1)

def is_valid_sudoku(board):
    # rows
    rows = [set() for _ in range(9)]
    # cols
    cols = [set() for _ in range(9)]
    # subcells
    subcells = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val == '.':
                continue
            if val in rows[r]:
                return False
            if val in cols[c]:
                return False
            box_index = (r // 3) * 3 + (c // 3)
            if val in subcells[box_index]:
                return 
            rows[r].add(val)
            cols[c].add(val)
            subcells[box_index].add(val)
    return True

string = "True" if is_valid_sudoku(board) else "False"
print(string)

string = "True" if is_valid_sudoku(board1) else "False"
print(string)

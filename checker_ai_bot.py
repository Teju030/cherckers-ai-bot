from copy import deepcopy
from random import randint
import time
import os.path

num = ""
INPUT_FILE = "input" + str(num) + ".txt"
OUTPUT_FILE = "output" + str(num) + ".txt"
PLAYDATA_FILE = "playdata.txt"
ROW_MAP = {0: 8, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}
COL_MAP = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
UP = [(-2, -2), (-2, 2)]  # for white players
DOWN = [(2, -2), (2, 2)]  # for black players


class GameType:
    SINGLE = 0
    GAME = 1 


class Player:
    WHITE = 0
    BLACK = 1


class Piece:
    def __init__(self, row, col, color):
        self.color = color
        self.row = row
        self.col = col
        self.player = 0  # If player is White
        self.up = False
        self.down = False
        if self.color == 'B' or self.color == 'b':
            self.player = Player.BLACK
            self.down = True
        else:
            self.up = True   # for white players

        if self.color == 'B' or self.color == 'W':
            self.up = True
            self.down = True

    def __repr__(self):
        return str(self.color) + " " + str(self.player)

    def isKing(self):
        if self.color == 'B' or self.color == 'W':
            return True
        return False

    def make_king(self):
        if self.color == 'b':
            self.color = 'B'
        elif self.color == 'w':
            self.color = 'W'
        self.up = True
        self.down = True

    def get_opponent_player(self):
        opponent = Player.WHITE if self.player == Player.BLACK else Player.BLACK
        return opponent


class Board:
    def __init__(self):
        self.board = []
        self.white_left = 0
        self.black_left = 0
        self.white_kings = 0
        self.black_kings = 0
        self.rows = 8
        self.cols = 8

    # get all pieces of given color
    def get_all_pieces(self, player):
        pieces = []
        for row in self.board:
            for p in row:
                if p is not None and p.player == player:
                    pieces.append(p)
        return pieces

    def make_move(self, piece, r, c):
        self.board[piece.row][piece.col] = None
        self.board[r][c] = piece
        piece.row = r
        piece.col = c

        # check if row or column is king line
        if not piece.isKing() and (r == 0 or r == self.rows - 1):
            piece.make_king()
            if piece.color == 'W':
                self.white_kings += 1
            else:
                self.black_kings += 1

    def remove_captured_pieces(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = None
            if piece is not None:
                if piece.player == Player.BLACK:
                    self.black_left -= 1
                    if piece.isKing():
                        self.black_kings -= 1
                else:
                    self.white_left -= 1
                    if piece.isKing():
                            self.white_kings -= 1

    def create_board(self, boardState):
        self.board = []
        for r in range(self.rows):
            self.board.append([])
            for c in range(self.cols):
                if boardState[r][c] != ".":
                    piece = Piece(r, c, boardState[r][c])
                    self.board[r].append(piece)
                    self.update_piece_count(piece)
                else:
                    self.board[r].append(None)

    def update_piece_count(self, piece):
        if piece.color == 'b' or piece.color == 'B':
            self.black_left += 1
            if piece.color == 'B':
                self.black_kings += 1
        else:
            self.white_left += 1
            if piece.color == 'W':
                self.white_kings += 1

    def get_board_state(self):
        return self.board

    def is_game_over(self):
        if self.black_left <= 0 or self.white_left <= 0:
            return True
        return False

    def print_board(self):
        print("*********** BOARD *************")
        for i in range(self.cols):
            if i == 0:
                print("{:2}|".format("\\").rjust(2), end=" ")
            print("{:2d}|".format(i), end=" ")
        print()

        i = 0
        for row in self.board:
            print("-"*35)
            print("{:2d}|".format(i), end=" ")
            i+=1
            for p in row:
                if p:
                    print("{:2}|".format(p.color).rjust(2), end=" ")
                else:
                    print("{:2}|".format(" ").rjust(2), end=" ")

            print()
        print()
        print("Board data: ")
        print("Black checkers: ", self.black_left)
        print("Black checkers: ", self.black_kings)
        print("White checkers: ", self.white_left)
        print("White checkers: ", self.white_kings)
        print("*********** END *************")

    def get_evaluation(self, maxPlayer, player):
        random_num = randint(1, 5)
        if maxPlayer == player:
            return self.get_board_pieces_valuation(player) + self.king_row_dist(player) + random_num
        else:
            val = self.get_board_pieces_valuation(player) + self.king_row_dist(player)
            val = -val + random_num
            return val

    def get_board_pieces_valuation(self, player):
        result = 0
        opponent = Player.BLACK if player == Player.WHITE else Player.WHITE

        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if not piece:
                    continue

                # safe at conrners
                if i == 0 or j == 0 or i == 7 or j == 7:
                    result += 7

                if piece.player == opponent:
                    jumps = self.get_jump_directions(piece)
                    if len(jumps) == 0:
                        result += 3
                    result -= len(jumps)*10
                    normal_moves = self.get_diagonal_directions(piece)
                    if len(normal_moves) == 0:
                        result += 3

                if piece.player == player:
                    jumps = self.get_jump_directions(piece)
                    result += len(jumps)*10

        total = self.black_left + self.white_left
        if player == Player.BLACK:
            total += (self.black_left - self.white_left) * 5
            total += (self.black_kings - self.white_kings) * 7
        else:
            total += (self.white_left - self.black_left) * 5
            total += (self.white_kings - self.black_kings) * 7

        result += total
        return result

    def king_row_dist(self, player):
        val = 0
        if player == Player.BLACK:
            for r in range(self.rows):
                for c in range(self.cols):
                    # King rows
                    piece = self.board[r][c]
                    if not piece:
                        continue
                    if piece.color == 'b':
                        val += piece.row
                    if r == 6 and piece.color == 'b':
                        val += 3
            if self.black_left > 0:
                val = val//self.black_left
                return val
            else:
                return 0

        else:
            for r in range(self.rows):
                for c in range(self.cols):
                    # King rows
                    piece = self.board[r][c]
                    if not piece:
                        continue
                    if piece.color == 'w':
                        val += 7 - piece.row
                    if r == 1 and piece.color == 'w':
                        val += 3
            if self.white_left > 0:
                val = val//self.white_left
                return val
            else:
                return 0

    def get_diagonal_directions(self, piece):
        directions = []
        left = piece.col - 1
        right = piece.col + 1
        if piece.up:
            to = (piece.row - 1, left)
            if self.is_valid_diagonal_move(piece, to):
                directions.append(to)
            to = (piece.row - 1, right)
            if self.is_valid_diagonal_move(piece, to):
                directions.append(to)
        if piece.down:
            to = (piece.row + 1, left)
            if self.is_valid_diagonal_move(piece, to):
                directions.append(to)
            to = (piece.row + 1, right)
            if self.is_valid_diagonal_move(piece, to):
                directions.append(to)
        return directions

    def get_jump_directions(self, piece):
        directions = {}
        # left = piece.col - 1
        # right = piece.col + 1
        if piece.up:
            for dir in UP:
                to = (piece.row+dir[0], piece.col+dir[1])
                via = (piece.row+(dir[0]//2), piece.col + (dir[1]//2))
                if self.is_valid_jump(piece, to, via):
                    directions[to] = via
        if piece.down:  # piece is moving down
            for dir in DOWN:
                to = (piece.row+dir[0], piece.col+dir[1])
                via = (piece.row+(dir[0]//2), piece.col + (dir[1]//2))
                if self.is_valid_jump(piece, to, via):
                    directions[to] = via
        return directions

    def within_boundries(self, row, col):
        if row > 7 or row < 0 or col > 7 or col < 0:
            return False
        return True

    def get_piece(self, row, col):
        return self.board[row][col]

    def is_valid_jump(self, piece, to, via):
        if self.within_boundries(to[0], to[1]) and \
           self.get_piece(to[0], to[1]) is None and \
           self.get_piece(via[0], via[1]) is not None and \
           self.get_piece(via[0], via[1]).player == piece.get_opponent_player():
            return True
        return False

    def is_valid_diagonal_move(self, piece, to):
        if self.within_boundries(to[0], to[1]) and self.get_piece(to[0], to[1]) is None:
            return True
        return False


class Game:
    def __init__(self):
        self.gameType = GameType.SINGLE
        self.turn = Player.BLACK
        self.remaining_time = 100
        self.gameBoard = Board()
        self.min_depth = 3
        self.max_depth = 6
        self.TimeLimitExceeded = False
        self.allowed_time = 3
        self.start_time = 0

    # jump sequence for a player
    def get_jump_sequences(self, board, player):
        jump_sequences = []
        for piece in board.get_all_pieces(player):
            # print("Getting jump sequences")
            # get possible jumps of piece
            possible_jumps = self.get_all_possible_jumps(board, piece, piece)
            # print("possible jumps : ",possible_jumps)
            # board.print_board()
            if possible_jumps is not None:
                for jump in possible_jumps:
                    jump_sequences.append(jump)
        return jump_sequences

    # jump sequence for a piece
    def get_all_possible_jumps(self, board, piece, from_piece, jumps=[], skipped=[]):
        moves = []
        flag = False
        directions = board.get_jump_directions(piece)
        if len(directions) > 0:
            flag = False
            # print("Directions: ",directions)
            for to, via in directions.items():
                temp_board = deepcopy(board)
                temp_piece = temp_board.get_piece(piece.row, piece.col)
                # print(to, via)
                # piece, move, board, captured_pieces
                flag = temp_piece.isKing()
                temp_board = self.play_move(temp_piece, to, temp_board, [temp_board.get_piece(via[0], via[1])])
                # get double or multijumps of piece
                # If piece is converted to king so end the move
                if not flag and temp_piece.isKing():
                    #  print("Flag1")
                    flag = True
                    moves.append((temp_board, jumps+[to], skipped+[via], from_piece))
                    return moves
                j = self.get_all_possible_jumps(temp_board, temp_piece,  from_piece, jumps+[to], skipped+[via])
                # print(j)
                if j:
                    moves = moves + j
        elif jumps:
            moves.append((board, jumps, skipped, from_piece))
            return moves

        return moves

    def get_diagonal_moves(self, board, player):
        # print("Get dignoal moves for player : ", player)
        moves = []
        for piece in board.get_all_pieces(player):
            directions = board.get_diagonal_directions(piece)
            if directions:
                for to in directions:
                    temp_board = deepcopy(board)
                    temp_piece = temp_board.get_piece(piece.row, piece.col)
                    temp_board = self.play_move(temp_piece, to, temp_board, [])
                    moves.append((temp_board, [to], [], piece))
        return moves

    # if jump moves are not availbale then get normal diagonal moves
    def get_all_moves(self, board, player, both=False):
        # print("[get_all_moves] Get all moves for player :", player)
        all_jumps = self.get_jump_sequences(board, player)
        if all_jumps and not both:
            # print("[get_all_moves] Printing jump moves")
            # for j in all_jumps:
                # print("Jump : ", j)
            return all_jumps
        # print("[get_all_moves] No jump sequence found.")
        diagonal_moves = self.get_diagonal_moves(board, player)
        if diagonal_moves and not both:
            # print("[get_all_moves] Diagonal moves: ")
            # for m in diagonal_moves:
            #     print(m)
            return diagonal_moves
        if both:
            # print("[get_all_moves]")
            if all_jumps and not diagonal_moves:
                return all_jumps
            if not all_jumps and diagonal_moves:
                return diagonal_moves
            all_jumps.extend(diagonal_moves)
            return all_jumps

    # just move the piece to destination
    def play_move(self, piece, move, board, captured_pieces):
        # print("play_move:")
        board.make_move(piece, move[0], move[1])
        if captured_pieces:
            board.remove_captured_pieces(captured_pieces)
        return board

    def print_game_data(self):
        print("Game Type     :", self.gameType)
        print("Turn          :", self.turn)
        print("Remaining Time:", self.remaining_time)
        print("Start Time    :", self.start_time)
        print("allowed Time  :", self.allowed_time)
        print("Min depth     :", self.min_depth)
        print("Max depth     :", self.max_depth)
        self.gameBoard.print_board()

    # Calculate move time
    def update_allowed_move_time(self):
        if self.gameType == GameType.SINGLE:
            self.allowed_time = self.start_time + (self.remaining_time * 0.9)
        else:
            if self.remaining_time > 200:
                self.allowed_time = self.start_time + (self.remaining_time * 0.15)
            elif self.remaining_time > 100:
                self.allowed_time = self.start_time + (self.remaining_time * 0.13)
            elif self.remaining_time > 50:
                self.allowed_time = self.start_time + (self.remaining_time * 0.11)
            elif self.remaining_time > 30:
                self.allowed_time = self.start_time + (self.remaining_time * 0.1)
            elif self.remaining_time > 10:
                self.allowed_time = self.start_time + (self.remaining_time * 0.09)
            elif self.remaining_time >= 5:
                self.allowed_time = self.start_time + (self.remaining_time * 0.08)
            elif self.remaining_time < 5:
                self.allowed_time = self.start_time + min(self.remaining_time, 0.3)

    def play(self):
        # returns J FROM_POS TO_POS format tuples
        best_move = None
        # if only one jump available then take that move 
        all_moves = self.get_all_moves(self.gameBoard, self.turn)
        # print("[play] length of moves: ", all_moves)
        if len(all_moves) == 1:
            best_move = all_moves[0]
        elif len(all_moves) == 0:
            print("No moves available")
        else:
            best_move = all_moves[0]
            self.TimeLimitExceeded = False

            if (self.gameBoard.black_left + self.gameBoard.white_left) >= 15:
                self.min_depth = 3
                self.max_depth = 7

            if (self.gameBoard.black_left + self.gameBoard.white_left) <= 10:
                self.min_depth +=1
                self.max_depth +=1

            if self.allowed_time - self.start_time < 3:
                self.min_depth = 2
                self.max_depth = 4

            if self.allowed_time - self.start_time < 10:
                self.min_depth = 2
                self.max_depth = 6

            if (self.gameBoard.black_left + self.gameBoard.white_left) <= 5:
                self.min_depth +=1
                self.max_depth +=1

            # print("[play] Min Depth  :", self.min_depth)
            # print("[play] Max Depth  :", self.max_depth)
            for depth in range(self.min_depth, self.max_depth):
                # print("For depth:", depth)
                # there is less than second remaining 
                if self.allowed_time - self.start_time < 0.3:
                    break

                move = self.minimax(self.gameBoard, depth, float('-inf'), float('inf'), self.turn, self.turn)[1]

                if not self.TimeLimitExceeded and move:

                    best_move = move

                elif self.TimeLimitExceeded:
                    break
                t = time.time() + (self.allowed_time - self.start_time)/2
                if t >= self.allowed_time:
                    # print("[play] : Ooopz.. Cannot run next depth within time Depth: ", depth)
                    self.TimeLimitExceeded = True
                    break
        # print("[play] print best move: ", best_move)
        # print("[play] print best move board")
        # best_move[0].print_board()
        from_pos = (best_move[3].row, best_move[3].col) # self.get_from_position(best_move)
        res = self.map_moves(from_pos, best_move[1], best_move[2])
        # print("[play] move:\n", res)
        # print("[play] print original board")
        # self.gameBoard.print_board()
        return res

    def get_opening_move(self, move_num):
        # print("[get_opening_move]: getting opening move")
        if move_num == 1:
            if self.turn == Player.BLACK:
                return "E f6 e5"
            else:
                # check if black moved sequence
                moves = { 0: "E c3 d4", 2:"E e3 f4", 4:"E c3 b4", 6: "E c3 d4"}
                for col in [0, 2, 4, 6]:
                    piece = self.gameBoard.get_piece(3, col)
                    if piece is not None and piece.player == Player.BLACK:
                        return moves[col]

    def map_moves(self,from_pos, moves, jumped):
        result = ""
        from_pos = str(COL_MAP[from_pos[1]]) + str(ROW_MAP[from_pos[0]])
        if jumped:
            result += "J {} {}\n".format(from_pos, str(COL_MAP[moves[0][1]]) + str(ROW_MAP[moves[0][0]]))
            for i in range(len(moves)-1):
                frm = ""+ str(COL_MAP[moves[i][1]]) + str(ROW_MAP[moves[i][0]])
                to = ""+ str(COL_MAP[moves[i+1][1]]) + str(ROW_MAP[moves[i+1][0]])
                result += "J {} {}\n".format(frm, to)
        elif moves:
            result += "E {} {}\n".format(from_pos, str(COL_MAP[moves[0][1]]) + str(ROW_MAP[moves[0][0]]))
        return result.rstrip()

    def create_board_from_input(self, boardState):
        self.gameBoard.create_board(boardState)

    # minimax using alpha beta pruning
    def minimax(self, board, depth, alpha, beta, maxPlayer, player):
        if depth == 0 or board.is_game_over():
            return board.get_evaluation(maxPlayer, player), board

        if self.TimeLimitExceeded:
            # print("[minimax] :  Time limit exceeded")
            return 0, board

        if self.allowed_time <= (time.time()):
            # print("[minimax] : Ooopz.. Time limit exceeded depth: ", depth)
            self.TimeLimitExceeded = True
            return 0 , board

        if maxPlayer == player:
            val = float('-inf')
            best_move = None
            for sequence in self.get_all_moves(board, player):
                #print("Sequence", sequence)
                jumped_board = sequence[0]
                opponent = Player.WHITE if maxPlayer == Player.BLACK else Player.BLACK
                tmp = self.minimax(jumped_board, depth-1, alpha, beta, opponent, player)[0]
                if self.TimeLimitExceeded:
                    # print("[minimax] : max player Time limit exceeded")
                    return 0, board
                val = max(val, tmp)
                if val == tmp:
                    best_move = sequence
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return val, best_move
        else:
            # for min player 
            val = float('inf')
            best_move = None
            for sequence in self.get_all_moves(board, player):
                jumped_board = sequence[0]

                opponent = Player.WHITE if maxPlayer == Player.BLACK else Player.BLACK
                tmp = self.minimax(jumped_board, depth-1, alpha, beta,  opponent, player)[0]
                if self.TimeLimitExceeded:
                    # print("[minimax] : min player Time limit exceeded")
                    return 0, board
                val = min(beta, tmp)
                if val == tmp:
                    best_move = sequence
                beta = min (beta, val )
                if beta <= alpha:
                    break
            return val, best_move

####################### Driver Function ##############################################
def driver(start):
    game = None
    with open(INPUT_FILE, 'r') as f:
        game = Game()

        if f.readline().rstrip() == "GAME":
            game.gameType = GameType.GAME
        else:
            game.turn = GameType.SINGLE

        if f.readline().rstrip() =="BLACK":
            game.turn = Player.BLACK
        else:
            game.turn = Player.WHITE

        game.remaining_time = float(f.readline().rstrip())
        # Read the Board state
        game.start_time = start
        game.update_allowed_move_time()

        boardState = []
        for i in range(8):
            boardState.append(list(f.readline().rstrip()))

        game.create_board_from_input(boardState)
        # game.print_game_data()
        f.close()

    if os.path.isfile(OUTPUT_FILE):
        f = open(OUTPUT_FILE, 'w')
        f.truncate()
    else:
        f = open(OUTPUT_FILE, "w")

    # Get Moves of the player  E FROM_POS TO_POS  J FROM_POS TO_POS format
    moves = None
    if game.gameType == GameType.SINGLE:
        moves = game.play()
    else:
        moves_so_far = 0
        if os.path.isfile(PLAYDATA_FILE):
            fs = open(PLAYDATA_FILE, 'r')
            moves_so_far = int(fs.readline().rstrip())
            fs.close()
        # initial game
        if moves_so_far < 1:
            moves = game.get_opening_move(moves_so_far+1)

            if os.path.isfile(PLAYDATA_FILE):
                fs = open(PLAYDATA_FILE, 'w')
                fs.truncate()
            else:
                fs = open(PLAYDATA_FILE, 'w')

            fs.write(str(moves_so_far+1))
            fs.close()

        else:
            moves = game.play()

    f.write(moves)
    f.close()
    return game.remaining_time


#######################  Calling Driver  ###########################################
# All program calling
start = time.time()
# proces_s = time.process_time()
# datetime_start = datetime.datetime.now()

t = driver(start)

# end = time.time()
# time_taken = (end - start)
# print("Total time taken : " , time_taken)
# print("Remaining time taken : " , t - time_taken)


# process_e = time.process_time()
# datetime_end  = datetime.datetime.now()

# datetime_time_taken = datetime_end - datetime_start
# process_taken = process_e - proces_s
# print("Process time taken : " , process_taken)

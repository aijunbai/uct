# This is a very simple implementation of the uct Monte Carlo SearchTree Search algorithm in Python 2.7.
# The function uct(root_state, __iter_max) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# Example GameState classes for Nim, Gobang, and Othello are included to give some idea of how you
# can write your own GameState use uct in your 2-player game. Change the game to be played in 
# the uct_play_game() function at the bottom of the code.
# 
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo SearchTree Search check out our web site at www.mcts.ai

import optparse
import random
import sets
import math

ITER_MAX = 100

try:
    import java.lang
    PARALLEL_COUNT = java.lang.Runtime.getRuntime().availableProcessors()
except ImportError:
    import multiprocessing
    PARALLEL_COUNT = multiprocessing.cpu_count()

class GameState:
    """ A state of the game, i.e. the game __board. These are the only functions which are
        absolutely necessary to implement uct in any 2-player complete information deterministic 
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self):
            self.player_just_moved = 2 # At the root pretend the player just moved is player 2 - player 1 has the first move
        
    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = GameState()
        st.player_just_moved = self.player_just_moved
        return st

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update player_just_moved.
        """
        self.player_just_moved = 3 - self.player_just_moved
        
    def get_moves(self):
        """ Get all possible moves from this state.
        """
    
    def get_result(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """

    def __repr__(self):
        """ Don't need this - but good style.
        """
        pass


class NimState:
    """ A state of the game Nim. In Nim, players alternately take 1,2 or 3 __chips with the 
        winner being the player to take the last chip. 
        In Nim any initial state of the form 4n+k for k = 1,2,3 is a win for player 1
        (by choosing k) __chips.
        Any initial state of the form 4n is a win for player 2.
    """
    def __init__(self, chips):
        self.player_just_moved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.__chips = chips
        
    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = NimState(self.__chips)
        st.player_just_moved = self.player_just_moved
        return st

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update player_just_moved.
        """
        assert move >= 1 and move == int(move)
        self.__chips -= move
        self.player_just_moved = 3 - self.player_just_moved
        
    def get_moves(self):
        """ Get all possible moves from this state.
        """
        return range(1, min([4, self.__chips + 1]))
    
    def get_result(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        assert self.__chips == 0
        return 1.0 if self.player_just_moved == playerjm else 0.0

    def __repr__(self):
        s = "Chips:" + str(self.__chips) + " JustPlayed:" + str(self.player_just_moved)
        return s

class OthelloState:
    """ A state of the game of Othello, i.e. the game __board.
        The __board is a 2D array where 0 = empty (.), 1 = player 1 (X), 2 = player 2 (O).
        In Othello players alternately place pieces on a square __board - each piece played
        has to sandwich opponent pieces between the piece played and pieces already on the 
        __board. Sandwiched pieces are flipped.
        This implementation modifies the rules to allow variable sized square boards and
        terminates the game as soon as the player about to move cannot make a move (whereas
        the standard game allows for a pass move). 
    """
    
    __positions = [[(x, y) for x in range(s) for y in range(s)] for s in range(32)]
    
    def __init__(self, size = 8):
        assert size == int(size) and size % 2 == 0 # __size must be integral and even
        self.player_just_moved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.__board = [] # 0 = empty, 1 = player 1, 2 = player 2
        self.__size = size
        for y in range(size):
            self.__board.append([0]*size)
        self.__board[size/2][size/2] = self.__board[size/2-1][size/2-1] = 1
        self.__board[size/2][size/2-1] = self.__board[size/2-1][size/2] = 2
        
    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = OthelloState()
        st.player_just_moved = self.player_just_moved
        st.__board = [self.__board[i][:] for i in range(self.__size)]
        st.__size = self.__size
        return st

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update playerToMove.
        """
        (x,y) = (move[0],move[1])
        assert x == int(x) and y == int(y) and self.is_on_board(x,y) and self.__board[x][y] == 0
        m = self.get_all_sandwiched_counters(x,y)
        self.player_just_moved = 3 - self.player_just_moved
        self.__board[x][y] = self.player_just_moved
        for (a,b) in m:
            self.__board[a][b] = self.player_just_moved
    
    def get_moves(self):
        """ Get all possible moves from this state.
        """
        return [(x,y) for (x, y) in self.__positions[self.__size] if self.__board[x][y] == 0 and self.exists_sandwiched_counter(x,y)]

    def adjacent_enemy_directions(self,x,y):
        """ Speeds up get_moves by only considering squares which are adjacent to an enemy-occupied square.
        """
        return [(dx, dy) for (dx, dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)] if self.is_on_board(x+dx,y+dy) and self.__board[x+dx][y+dy] == self.player_just_moved]
    
    def exists_sandwiched_counter(self,x,y):
        """ Does there exist at least one counter which would be flipped if my counter was placed at (x,y)?
        """
        for (dx,dy) in self.adjacent_enemy_directions(x,y):
            if self.sandwiched_counters(x,y,dx,dy):
                return True
        return False
    
    def get_all_sandwiched_counters(self, x, y):
        """ Is (x,y) a possible move (i.e. opponent counters are sandwiched between (x,y) and my counter in some direction)?
        """
        sandwiched = []
        for (dx,dy) in self.adjacent_enemy_directions(x,y):
            sandwiched.extend(self.sandwiched_counters(x,y,dx,dy))
        return sandwiched

    def sandwiched_counters(self, x, y, dx, dy):
        """ Return the coordinates of all opponent counters sandwiched between (x,y) and my counter.
        """
        x += dx
        y += dy
        sandwiched = []
        while self.is_on_board(x,y) and self.__board[x][y] == self.player_just_moved:
            sandwiched.append((x,y))
            x += dx
            y += dy
        if self.is_on_board(x,y) and self.__board[x][y] == 3 - self.player_just_moved:
            return sandwiched
        else:
            return [] # nothing sandwiched

    def is_on_board(self, x, y):
        return x >= 0 and x < self.__size and y >= 0 and y < self.__size
    
    def get_result(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        jmcount = 0
        notjmcount = 0
        for (x, y) in self.__positions[self.__size]:
            jmcount += self.__board[x][y] == playerjm
            notjmcount += self.__board[x][y] == 3 - playerjm

        if jmcount > notjmcount: return 1.0
        elif notjmcount > jmcount: return 0.0
        else: return 0.5 # draw

    def __repr__(self):
        Xs = 0
        Os = 0
        s = "JustPlayed:" + str(self.player_just_moved) + "\n"
        
        for (x, y) in self.__positions[self.__size]:
            s += ".XO"[self.__board[x][y]]
            s += " "
            s += ("\n" if y == self.__size - 1 else "")
            Xs += self.__board[x][y] == 1
            Os += self.__board[x][y] == 2
        
        s += "Xs:" + str(Xs) + " Os:" + str(Os) + "\n"
        return s
    
class GobangState:
    """ A state of the game of Gobang, i.e. the game __board.
        The __board is a 2D array where 0 = empty (.), 1 = player 1 (X), 2 = player 2 (O).
    """
    
    __positions = [[(x, y) for x in range(s) for y in range(s)] for s in range(32)]
    
    def __init__(self, size = 8, inrow = 5):
        assert size == int(size) # __size must be integral
        self.player_just_moved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.__board = [] # 0 = empty, 1 = player 1, 2 = player 2
        self.__size = size
        self.__inrow = inrow
        self.__terminated = False
        for y in range(size):
            self.__board.append([0]*size)
        
    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = GobangState()
        st.player_just_moved = self.player_just_moved
        st.__board = [self.__board[i][:] for i in range(self.__size)]
        st.__size = self.__size
        st.__inrow = self.__inrow
        st.__terminated = self.__terminated
        return st

    def do_move(self, move):
        """ update a state by carrying out the given move.
            Must update playerToMove.
        """
        (x,y) = (move[0],move[1])
        assert x == int(x) and y == int(y) and self.is_on_board(x,y) and self.__board[x][y] == 0
        self.player_just_moved = 3 - self.player_just_moved
        self.__board[x][y] = self.player_just_moved
        self.__terminated = self.check_termination(x, y)
        
    def check_termination(self, x, y):
        assert self.__board[x][y] == self.player_just_moved
        
        for (dx, dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1)]:
            if self.count_stones_in_direction(x, y, dx, dy) + self.count_stones_in_direction(x, y, -dx, -dy) + 1 >= self.__inrow:
                return True
        return False 
                    
    def count_stones_in_direction(self, x, y, dx, dy):
        ret = 0
        x += dx
        y += dy
        while self.is_on_board(x,y) and self.__board[x][y] == self.player_just_moved:
            ret += 1
            x += dx
            y += dy
        
        return ret
    
    def get_moves(self):
        """ Get all possible moves from this state.
        """
        return [(x,y) for (x, y) in self.__positions[self.__size] if self.__board[x][y] == 0] if not self.__terminated else []

    def is_on_board(self, x, y):
        return x >= 0 and x < self.__size and y >= 0 and y < self.__size
    
    def get_result(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        if self.__terminated:
            return 1.0 if self.player_just_moved == playerjm else 0.0
        else:
            return 0.5

    def __repr__(self):
        s = "JustPlayed:" + str(self.player_just_moved) + "\n"
        for (x, y) in self.__positions[self.__size]:
            s += ".XO"[self.__board[x][y]]
            s += " "
            s += ("\n" if y == self.__size - 1 else "")
        
        return s
    
def uct_play_game(uct, search_tree):
    """ Play a sample game between two uct players
    """
    state = [NimState(15), OthelloState(8), GobangState(8, 5)][1]
    
    while state.get_moves():
        print str(state)
        print
        
        if search_tree is not None:
            m = uct(state, ITER_MAX, search_tree)
        else:
            m = uct(state, ITER_MAX)
        
        print ">> Best move: " + str(m) + "\n"
        state.do_move(m)
   
    print "Game finished!\n\n" + str(state)
   
    if state.get_result(state.player_just_moved) == 1.0:
        print "Player " + str(state.player_just_moved) + " wins!"
    elif state.get_result(state.player_just_moved) == 0.0:
        print "Player " + str(3 - state.player_just_moved) + " wins!"
    else: print "Nobody wins!"


class TreeNode:
    """
    A tree node will be stored in a tree structure constantly during process running
    """
    def __init__(self, state):
        self.__wins = 0.0
        self.__visits = 1.0;
        
        self.__state = state.clone()
        self.__child_nodes = {}                
        self.__untried_moves = state.get_moves() # future child nodes
        
    def state(self):
        return self.__state
    
    def child_nodes(self):
        return self.__child_nodes
    
    def untried_moves(self):
        return self.__untried_moves
    
    def player_just_moved(self):
        return self.__state.player_just_moved
        
    def value(self):
        return self.__wins / self.__visits
        
    def ucb(self, parent, constant):
        return self.value() + constant * math.sqrt(2 * math.log(parent.__visits) / self.__visits)
                           
    def update(self, get_result):
        self.__visits += 1.0
        self.__wins += float(get_result)        
        
    def add_child(self, fm, n):
        if fm in self.__untried_moves:
            self.__untried_moves.remove(fm)
        
        if fm not in self.__child_nodes:
            self.__child_nodes[fm] = n
       
    def traverse(self, fun):
        for c in self.child_nodes().values():
            c.traverse(fun)
        fun(self)

    def tree2string(self, indent):
        s = self.indent_string(indent) + str(self)
        for c in self.child_nodes().values():
            s += c.tree2string(indent+1)
        return s

    def indent_string(self, indent):
        s = "\n"
        for i in range (1, indent+1):
            s += "| "
        return s
        
    def __repr__(self):
        return "W/V:" + str(self.__wins) + "/" + str(self.__visits) + "(" + str(int(1000 * self.value()) / 1000.0) + ")" + " U:" + str(self.__untried_moves)
    
class SearchTree:
    def __init__(self):
        self.__pool = {}
    
    def get_node(self, state, tree_node_creator=None):
        key = str(state)
        
        creator = tree_node_creator if tree_node_creator is not None else TreeNode
        if key not in self.__pool:
            self.__pool[key] = creator(state)
                    
        return self.__pool[key]

    def clean_sub_tree(self, root_node, ignored_node):
        ignore_set = sets.Set()
        ignored_node.traverse(lambda n: ignore_set.add(n))

        for (k, n) in self.__pool.items():
            if n not in ignore_set:
                del self.__pool[k]
        ignore_set.clear()
    
    def size(self):
        return len(self.__pool)

class SearchNode:
    """ A node in the game tree. Note wins is always from the viewpoint of player_just_moved.
        Crashes if state not specified.
    """
    def __init__(self, move=None, parent=None, tree_node=None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parent_node = parent # "None" for the root node
        if parent:
            self.depth = parent.depth + 1
        else:
            self.depth = 0
        self.__tree_node = tree_node
        
    def player_just_moved(self):
        return self.__tree_node.player_just_moved()
    
    def state(self):
        return self.__tree_node.state()
        
    def untried_moves(self):
        return self.__tree_node.untried_moves()
    
    def child_nodes(self):
        return self.__tree_node.child_nodes()

    def clean_sub_tree(self, ignored_node, tree):
        tree.clean_sub_tree(self.__tree_node, ignored_node.__tree_node)

    def uct_select_child(self, constant, search_node_creator=None):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        assert self.child_nodes()        
        creator = search_node_creator if search_node_creator is not None else SearchNode        
        (move, child) = max(self.child_nodes().items(), key=lambda (m, n): n.ucb(self.__tree_node, constant))
        node = creator(move, self, child)
        return node
    
    def add_child(self, move, tree_node, search_node_creator=None):
        """ Remove move from __untried_moves and add a new child node for this move.
            Return the added child node
        """
        creator = search_node_creator if search_node_creator is not None else SearchNode
        self.__tree_node.add_child(move, tree_node)        
        node = creator(move, self, tree_node)
        return node
    
    def update(self, get_result):
        """ update this node - one additional visit and get_result additional wins. get_result must be from the viewpoint of playerJustmoved.
        """
        self.__tree_node.update(get_result)

    def __repr__(self):
        return "[M:" + str(self.move) + " " + str(self.__tree_node) + "]"

    def tree2string(self, indent):
        return self.__tree_node.tree2string(indent)

    def children2string(self):
        s = ""
        for (k, v) in self.child_nodes().items():
            s += "[M:" + str(k) + " " + str(v) + "]\n"
        return s
    
def uct(root_state, iter_max, search_tree=None, verbose=True):
    """ Conduct a uct search for __iter_max iterations starting from root_state.
        Return the best move from the root_state.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
    
    should_clean = True
    
    if search_tree is None:
        search_tree = SearchTree()
        should_clean = False

    max_depth = 0
    node_count = search_tree.size()
    
    root_node = SearchNode(tree_node=search_tree.get_node(root_state))
    
    for i in range(iter_max):
        node = root_node

        # Select
        while not node.untried_moves() and node.child_nodes():  # node is fully expanded and non-terminal
            node = node.uct_select_child(1.0)
            
        state = node.state().clone()
        
        # Expand
        m = random.choice(node.untried_moves()) if node.untried_moves() else None
        if m is not None:  # if we can expand (i.e. state/node is non-terminal)
            state.do_move(m)
            node = node.add_child(m, search_tree.get_node(state))  # add child and descend search_tree
        max_depth = max(node.depth, max_depth)
       
        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        moves = state.get_moves()
        while moves:  # while state is non-terminal
            state.do_move(random.choice(moves))
            moves = state.get_moves()
        
        # Backpropagate
        while node != None:  # backpropagate from the expanded node and work back to the root node
            node.update(state.get_result(node.player_just_moved()))  # state is terminal. update node with get_result from POV of node.player_just_moved
            node = node.parent_node

    selected_node = root_node.uct_select_child(0.0)

    if verbose:
        print "Max search depth:", max_depth
        print "Nodes generated:", str(search_tree.size() - node_count)
        print
        print root_node.children2string()

    if should_clean:
        root_node.clean_sub_tree(selected_node, search_tree)
        if verbose:
            print "Nodes remainning:", str(search_tree.size())
        
    if verbose:
        print

    return selected_node.move

def main(uct, search_tree=None):
    """ Play a single game to the end using uct for both players. 
    """
    
    global ITER_MAX
    global PARALLEL_COUNT

    usage = "Usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-i", "--itermax", type="int", dest="__iter_max", help="max iteration times")
    parser.add_option("-p", "--parallel", type="int", dest="parallel_count", help="parallel count")
    (options, args) = parser.parse_args()
    
    ITER_MAX = options.__iter_max if options.__iter_max is not None else ITER_MAX
    PARALLEL_COUNT = options.parallel_count if options.parallel_count is not None else PARALLEL_COUNT

    print "Max iterations:", ITER_MAX
    print "Parallel count:", PARALLEL_COUNT
    print
    
    uct_play_game(uct, search_tree)


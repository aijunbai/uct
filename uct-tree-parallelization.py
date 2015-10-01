#!/usr/bin/env jython

import threading
import random
import math
import sets
import common
    
class TreeNode(common.TreeNode):
    def __init__(self, state):
        self.__lock = threading.Lock()
        self.__lock.acquire()
        common.TreeNode.__init__(self, state)
        self.__lock.release()

    def acquire_lock(self):
        self.__lock.acquire()

    def release_lock(self):
        self.__lock.release()
        
    def update(self, result):
        self.__lock.acquire()
        common.TreeNode.update(self, result)
        self.__lock.release()
        
    def add_child(self, fm, n):
        self.__lock.acquire()
        common.TreeNode.add_child(self, fm, n)        
        self.__lock.release()
    
class SearchTree(common.SearchTree):
    def __init__(self):
        common.SearchTree.__init__(self)
        self.__lock = threading.Lock()
    
    def get_node(self, state):
        self.__lock.acquire()
        node = common.SearchTree.get_node(self, state, TreeNode)
        self.__lock.release()
        return node

    def clean_sub_tree(self, root_node, ignored_node):
        self.__lock.acquire()
        common.SearchTree.clean_sub_tree(self, root_node, ignored_node)
        self.__lock.release()

class SearchNode(common.SearchNode):
    def __init__(self, move=None, parent=None, tree_node=None):
        common.SearchNode.__init__(self, move, parent, tree_node)
        
    def acquire_lock(self):
        self.__tree_node.acquire_lock()

    def release_lock(self):
        self.__tree_node.release_lock()
        
    def uct_select_child(self, constant):
        return common.SearchNode.uct_select_child(self, constant, SearchNode)

        
class SearchThread (threading.Thread):
    def __init__(self, root_state, iter_max, search_tree):
        threading.Thread.__init__(self)
        self.__root_state = root_state
        self.__iter_max = iter_max
        self.__search_tree = search_tree
        
    def run(self):
        root_node = SearchNode(tree_node=self.__search_tree.get_node(self.__root_state))

        for i in range(self.__iter_max):
            node = root_node

            # Select
            while not node.untried_moves() and node.child_nodes():  # node is fully expanded and non-terminal
                node = node.uct_select_child(1.0)

            state = node.state().clone()

            # Expand
            node.acquire_lock()
            m = random.choice(node.untried_moves()) if node.untried_moves() else None
            node.release_lock()
            if m is not None:  # if we can expand (i.e. state/node is non-terminal)
                state.do_move(m)
                node = node.add_child(m, self.__search_tree.get_node(state))  # add child and descend tree

            # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
            moves = state.get_moves()
            while moves:  # while state is non-terminal
                state.do_move(random.choice(moves))
                moves = state.get_moves()

            # Backpropagate
            while node != None:  # backpropagate from the expanded node and work back to the root node
                node.update(state.get_result(node.player_just_moved()))  # state is terminal. update node with result from POV of node.player_just_moved
                node = node.parent_node
                 
def uct(root_state, iter_max, search_tree):
    """ Conduct a uct search for __iter_max iterations starting from __root_state.
        Return the best move from the __root_state.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    node_count = search_tree.size()
    threads = []
    
    for i in range(common.PARALLEL_COUNT):
        threads.append(SearchThread(root_state, iter_max / common.PARALLEL_COUNT, search_tree))
    
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
    
    root_node = SearchNode(tree_node=search_tree.get_node(root_state))
    selected_node = root_node.uct_select_child(0.0)

    print "Nodes generated:", str(search_tree.size() - node_count)
    print
    print root_node.children2string()

    root_node.clean_sub_tree(selected_node, search_tree)

    print "Nodes remainning:", str(search_tree.size())
    print

    return selected_node.move

if __name__ == "__main__":
    common.main(uct, SearchTree())

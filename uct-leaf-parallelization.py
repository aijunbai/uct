#!/usr/bin/env jython

import threading
import common
import random
    
class SimulationThread(threading.Thread):
    def __init__(self, state):
        self.__state = state.clone()
        threading.Thread.__init__(self)
        
    def get_result(self, playerjm):
        return self.__state.get_result(playerjm)        
        
    def run(self):
        moves = self.__state.get_moves()
        while moves:  # while state is non-terminal
            self.__state.do_move(random.choice(moves))
            moves = self.__state.get_moves()

def uct(root_state, iter_max, search_tree):
    """ Conduct a uct search for iter_max iterations starting from root_state.
        Return the best move from the root_state.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    max_depth = 0
    node_count = search_tree.size()
    root_node = common.SearchNode(tree_node=search_tree.get_node(root_state))
    
    for i in range(iter_max):
        node = root_node

        # Select
        while not node.untried_moves() and node.child_nodes():  # node is fully expanded and non-terminal
            node = node.uct_select_child(1.0)
            
        state = node.state().clone()
        
        # Expand
        if node.untried_moves():  # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untried_moves())
            state.do_move(m)
            node = node.add_child(m, search_tree.get_node(state))  # add child and descend tree
        max_depth = max(node.depth, max_depth)
        
        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        threads = []
        
        for i in range(common.PARALLEL_COUNT):
            threads.append(SimulationThread(state))
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
       
        # Backpropagate
        while node != None:  # backpropagate from the expanded node and work back to the root node
            result = sum([t.get_result(node.player_just_moved()) for t in threads]) / common.PARALLEL_COUNT
            node.update(result)  # state is terminal. update node with result from POV of node.player_just_moved
            node = node.parent_node

        del threads[:]
        del threads

    selected_node = root_node.uct_select_child(0.0)

    print "Max search depth:", max_depth
    print "Nodes generated:", str(search_tree.size() - node_count)
    print
    print root_node.children2string()

    root_node.clean_sub_tree(selected_node, search_tree)

    print "Nodes remainning:", str(search_tree.size())
    print

    return selected_node.move

if __name__ == "__main__":
    common.main(uct, common.SearchTree())

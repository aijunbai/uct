#!/usr/bin/env pypy

import collections
import multiprocessing
import common

class SearchTree(common.SearchTree):
    def __init__(self):
        common.SearchTree.__init__(self) 
        
    def clean_sub_tree(self, root_node, ignore_node):
        pass

class SearchWorker (multiprocessing.Process):
    def __init__(self, root_state, iter_max, queue):
        multiprocessing.Process.__init__(self)
        self.__root_state = root_state
        self.__iter_max = iter_max
        self.__queue = queue
        
    def run(self):
        tree = SearchTree()
        common.uct(self.__root_state, self.__iter_max, search_tree=tree, verbose=False)
        root_node = common.SearchNode(tree_node=tree.get_node(self.__root_state))        
        values = dict([(m, c.value()) for (m, c) in root_node.child_nodes().items()])
        self.__queue.put((values, tree.size()))
                
    def get_result(self):
        return self.__queue.get()
 
def uct(root_state, iter_max):
    """ Conduct a uct search for __iter_max iterations starting from __root_state.
        Return the best move from the __root_state.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
        
    workers = []
    
    for i in range(common.PARALLEL_COUNT):
        w = SearchWorker(root_state, iter_max / common.PARALLEL_COUNT, multiprocessing.Queue());
        workers.append(w);
    
    for w in workers:
        w.start()
        
    for w in workers:
        w.join()
        
    results = [w.get_result() for w in workers]
    
    values = collections.defaultdict(float)    
    for r in results:
        for (move, value) in r[0].items():
            values[move] += value
    
    print "Nodes generated:", sum([r[1] for r in results])
    print
    for (k, v) in values.items():
        print "%s: %.3f" % (str(k), v / common.PARALLEL_COUNT)
    print
    
    return max(values.items(), key=lambda (k, v): v)[0]

if __name__ == "__main__":
    common.main(uct, None)

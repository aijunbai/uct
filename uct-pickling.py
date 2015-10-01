#!/usr/bin/env pypy

import common
import os
import cPickle as pickle

class SearchTree(common.SearchTree):
    file_name = "search_tree.pkl"
    
    def __init__(self):
        common.SearchTree.__init__(self) 
               
        if os.path.exists(self.file_name):
            try:
                with open(self.file_name, "r") as f:
                    self.__pool = pickle.load(f)
            except pickle.PickleError:
                self.__pool = {}
        else:
            self.__pool = {}
    
    def dump(self):
        with open(self.file_name, "w") as f:
            pickle.dump(self.__pool, f)
            
    def clean_sub_tree(self, root_node, ignore_node):
        pass

if __name__ == "__main__":
    tree = SearchTree()
    common.main(common.uct, tree)
    tree.dump()
    
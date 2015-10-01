#! /bin/bash

LOG="log"

TESTS="
    uct.py
    uct-root-parallelization.py 
    uct-tree-parallelization.py 
    uct-leaf-parallelization.py
    uct-pickling.py
"

for i in $TESTS; do
    echo "Running $i... @ `date`" | tee -a $LOG

    if [ ! -z $1 ]; then
        ./run.sh $i -i $1
    else
        ./run.sh $i
    fi
done


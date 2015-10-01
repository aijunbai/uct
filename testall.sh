#! /bin/bash

LOG="log"

rm -f $LOG

for i in `seq 10 30`; do
    ITER_MAX=`echo 2^$i | bc -l`

    echo "Max iterations:" $ITER_MAX | tee -a $LOG
    ./test.sh $ITER_MAX
done

#! /bin/bash

set -e

ALOG="$1"
RUNTIME="$2"

analys() {
    FILE="$1"

    ITER_MAX=`grep "iterations" $FILE | awk '{print $3}'`
    TIME=`grep "User time" $FILE | awk '{print $4}'`
    CPU=`grep "CPU" $FILE | awk '{print $7}' | sed -e "s/%//g"`
    DEPTH=`grep "depth" $FILE | awk 'f += $4 {print f/NR}' | tail -1`

    if [ ! -z $ITER_MAX ] && [ ! -z $CPU ] && [ ! -z $DEPTH ]; then
        echo $ALOG \& $RUNTIME \& $ITER_MAX \& $CPU\\% \& `echo "scale=3; $TIME/$CPU*100" | bc -l` \& $DEPTH \\\\ \\hline
    fi
}

for i in *.log; do
    analys "$i"
done

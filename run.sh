#! /bin/bash

TIME=`which time`

$TIME -v ./$* 2>&1 | tee $1_`date +%s`.log

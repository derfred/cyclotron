#!/bin/sh
ulimit -v 10000000

$MYSLICE=expr $SGE_TASK_ID - 1
/usr/nld/python-2.7.2/bin/python ${@:2} $MYSLICE

xs=$?
if [ $xs -gt 127 ]; then
  echo "failed on $@" 1>&2
fi

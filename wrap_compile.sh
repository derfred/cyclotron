#!/bin/sh
ulimit -v 10000000

/usr/nld/python-2.7.2/bin/python ${@:2} $SGE_TASK_ID

xs=$?
if [ $xs -gt 127 ]; then
  echo "failed on $@" 1>&2
fi

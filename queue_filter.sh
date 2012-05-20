#!/bin/sh

# make sure env variables are all set and shit
source ~/.bashrc

BASE=$1
PROBLEM=$2
MAXLEN=$3
JOBSUFFIX=$4

QSUB="qsub -cwd -V -q frigg.q,skadi.q -b y -o /dev/null -e $BASE/$PROBLEM/stderrs/"

# step six, filter incomplete cliques
for d in `ls $BASE/$PROBLEM/unique_cliques`
do
  for i in {0..399}
  do
    $QSUB -N filter_cliques$JOBSUFFIX bash wrap_compile.sh sage filter_cliques.sage $PROBLEM.problem $BASE/$PROBLEM $MAXLEN ${d/.pickle/} $i
  done
done

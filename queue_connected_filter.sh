#!/bin/sh

# make sure env variables are all set and shit
source ~/.bashrc

BASE=$1
PROBLEM=$2
MAXLEN=$3
JOBSUFFIX=$4

mkdir -p $BASE/$PROBLEM/stderrs
rm $BASE/$PROBLEM/stderrs/filter_connected_cliques*

QSUB="qsub -cwd -V -q frigg.q,skadi.q -b y -o /dev/null -e $BASE/$PROBLEM/stderrs/"

# step six, filter incomplete cliques
for d in `ls $BASE/$PROBLEM/unique_cliques`
do
  mkdir -p $BASE/$PROBLEM/connected_cliques/${d/.pickle/}
  mkdir -p $BASE/$PROBLEM/potentially_connected_cliques/${d/.pickle/}
  mkdir -p $BASE/$PROBLEM/unique_potentially_connected_cliques/${d/.pickle/}
  $QSUB -t 1-400 -N filter_${d/.pickle/}_connected_cliques$JOBSUFFIX bash wrap_compile.sh filter_connected_cliques.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN ${d/.pickle/}
  $QSUB -hold_jid filter_${d/.pickle/}_connected_cliques$JOBSUFFIX bash wrap_compile.sh deduplicate_cliques.py $BASE/$PROBLEM potentially_connected_cliques/${d/.pickle/} unique_potentially_connected_cliques/${d/.pickle/}
done

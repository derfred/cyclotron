#!/bin/sh

# make sure env variables are all set and shit
source ~/.bashrc

BASE=$1
PROBLEM=$2
MAXLEN=$3
JOBSUFFIX=$4

mkdir -p $BASE/$PROBLEM/stderrs
rm $BASE/$PROBLEM/stderrs/filter_potentially_connected_cliques*

QSUB="qsub -cwd -V -q frigg.q,skadi.q -b y -o /dev/null -e $BASE/$PROBLEM/stderrs/"

# step six, filter incomplete cliques
for d in `ls $BASE/$PROBLEM/unique_cliques`
do
  mkdir -p $BASE/$PROBLEM/connected_cliques/${d/.pickle/}
  mkdir -p $BASE/$PROBLEM/potentially_connected_cliques/${d/.pickle/}
  mkdir -p $BASE/$PROBLEM/collated_potentially_connected_cliques/${d/.pickle/}
  $QSUB -t 1-400 -N filter_${d/.pickle/}_potentially_connected_cliques$JOBSUFFIX bash wrap_compile.sh filter_potentially_connected_cliques.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN ${d/.pickle/}
  $QSUB -N deduplicate_potentially_connected$JOBSUFFIX -hold_jid filter_${d/.pickle/}_potentially_connected_cliques$JOBSUFFIX bash wrap_compile.sh deduplicate_cliques.py $BASE/$PROBLEM potentially_connected_cliques/${d/.pickle/} collated_potentially_connected_cliques/${d/.pickle/}
done

$QSUB -N collate_potentially_connected$JOBSUFFIX -hold_jid deduplicate_potentially_connected$JOBSUFFIX bash wrap_compile.sh collate_potentially_connected.py $BASE/$PROBLEM

# now queue the connectedness check
$QSUB -N queue_filter_connected$JOBSUFFIX -hold_jid collate_potentially_connected$JOBSUFFIX bash queue_connected_filter.sh $BASE $PROBLEM $MAXLEN $JOBSUFFIX

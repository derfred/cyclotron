#!/bin/sh

# make sure env variables are all set and shit
source ~/.bashrc


BASE=$1
PROBLEM=$2
MAXLEN=$3
JOBSUFFIX=$4

echo "Queueing $PROBLEM in $BASE"

# create output directories used later
for dir in stderrs neighbours graphs pruned_graphs cliques unique_cliques filtered_cliques
do
  mkdir -p $BASE/$PROBLEM/$dir
done

rm $BASE/$PROBLEM/stderrs/*

QSUB="qsub -cwd -V -q frigg.q,skadi.q -b y -o /dev/null -e $BASE/$PROBLEM/stderrs/"

# first step, building association graph
$QSUB -t 0-399 -N build_associations$JOBSUFFIX bash wrap_compile.sh build_graph.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN

# second step, induce subgraphs
$QSUB -t 0-399 -N induce_subgraphs$JOBSUFFIX -hold_jid build_associations$JOBSUFFIX bash wrap_compile.sh induce_subgraphs.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN

# third step, remove nodes which are not part of a valid clique
$QSUB -t 0-399 -N prune_subgraphs$JOBSUFFIX -hold_jid induce_subgraphs$JOBSUFFIX bash wrap_compile.sh prune_subgraphs.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN

# fourth step, enumerate valid and consistent cliques
$QSUB -t 0-399 -N extract_cliques$JOBSUFFIX -hold_jid prune_subgraphs$JOBSUFFIX bash wrap_compile.sh extract_cliques.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN

# fifth step, deduplicate and sort cliques by size
$QSUB -N dedup_cliques$JOBSUFFIX -hold_jid extract_cliques$JOBSUFFIX bash wrap_compile.sh deduplicate_cliques.py $BASE/$PROBLEM cliques unique_cliques

# queue sixth step, find complete cliques
$QSUB -N queue_filter$JOBSUFFIX -hold_jid dedup_cliques$JOBSUFFIX bash queue_connected_filter.sh $BASE $PROBLEM $MAXLEN $JOBSUFFIX

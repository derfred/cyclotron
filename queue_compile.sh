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
for i in {0..399}
do
 $QSUB -N build_associations$JOBSUFFIX bash wrap_compile.sh sage build_graph.sage $PROBLEM.problem $BASE/$PROBLEM $MAXLEN $i
done

# second step, induce subgraphs
for i in {0..399}
do
 $QSUB -N induce_subgraphs$JOBSUFFIX -hold_jid build_associations$JOBSUFFIX bash wrap_compile.sh python induce_subgraphs.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN $i
done

# third step, remove nodes which are not part of a valid clique
for i in {0..399}
do
  $QSUB -N prune_subgraphs$JOBSUFFIX -hold_jid induce_subgraphs$JOBSUFFIX bash wrap_compile.sh python prune_subgraphs.py $PROBLEM.problem $BASE/$PROBLEM $MAXLEN $i
done

# fourth step, enumerate valid and consistent cliques
for i in {0..399}
do
  $QSUB -N extract_cliques$JOBSUFFIX -hold_jid prune_subgraphs$JOBSUFFIX bash wrap_compile.sh sage_pure extract_cliques.sage $PROBLEM.problem $BASE/$PROBLEM $MAXLEN $i
done

# fifth step, deduplicate and sort cliques by size
$QSUB -N dedup_cliques$JOBSUFFIX -hold_jid extract_cliques$JOBSUFFIX bash wrap_compile.sh python deduplicate_cliques.py $BASE/$PROBLEM

# queue sixth step, find complete cliques
$QSUB -N queue_filter$JOBSUFFIX -hold_jid dedup_cliques$JOBSUFFIX bash queue_complete_filter.sh $BASE $PROBLEM $MAXLEN $JOBSUFFIX

Cyclotron
=========

The scripts in this repository implement association graph matching to solve the combinatorial problem necessary when building heteroclinic networks classifying discrete inputs.

The compiler is written to be run on a computing cluster using a queueing system (only SGE). The individual steps of the solution pipeline are summarized at the end of this document.

Usage
=====

The classification problem is to be specified in a problem file. See *.problem for examples.

To place the individual tasks in a processing queue run the following command:
```ruby
bash queue_compile.sh <output_directory> <problem_file> <max_len> <compile_id>
```

Parameters:
 * output_directory: Intermediate and output files will be placed in the <problem_file> directory under this directory. This must be read/writable from all elements of the processing cluster
 * problem_file: Specification of the classification problem. Leave out the .problem extension
 * max_len: maximum length of cycles to use for solving the problem
 * compile_id: (optional) when running multiple concurrent compiles this parameter is necessary for deconflicting the individual tasks


Pipeline for finding decoding
=============================

1. Build association graph (build_graph.sage)                  -> neighbours
2. Induce node centered sub graphs (induce_subgraphs.py)       -> graphs
3. Prune sub graphs (prune_subgraphs.py)                       -> pruned_graphs
4. Extract valid and consistent cliques (extract_cliques.sage) -> cliques
5. Deduplicate cliques (deduplicate_cliques.py) (serial)       -> unique_cliques
6. Filter cliques (filter_cliques.sage)                        -> filtered_cliques

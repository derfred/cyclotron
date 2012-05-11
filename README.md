Pipeline for finding decoding
=============================

1. Build association graph (build_graph.sage)                  -> neighbours
2. Induce node centered sub graphs (induce_subgraphs.py)       -> graphs
3. Prune sub graphs (prune_subgraphs.py)                       -> pruned_graphs
4. Extract valid and consistent cliques (extract_cliques.sage) -> cliques
5. Deduplicate cliques (deduplicate_cliques.py) (serial)       -> unique_cliques
6. Filter cliques (filter_cliques.sage)                        -> filtered_cliques

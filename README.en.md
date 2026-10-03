# DSI Studio → HCP-MMP connectome: a short, illustrated workflow

[Türkçe README → README.md](README.md)

A step-by-step guide plus small Python scripts to go from the **Step T3 `.qsdr.fz`** file in DSI Studio to **99 named tract bundles**, a **360-region (HCP-MMP) connectivity matrix**, and the **coloured balls + edges inside the brain** view (Visualize Graph) by the shortest route.

![Final view: Region Rendering on, Tract Rendering off](docs/images/12_son_gorunum.jpg)

> **Scope:** guide + Python scripts. DSI Studio command-line automation is **out of scope**; DSI Studio steps are done in the GUI.
> **Data:** this repository contains no patient/subject data and must never receive any (see [Privacy](#privacy)).

## Outputs

Example prefix `s05` (use your own).

| # | File | How it is produced |
|---|------|--------------------|
| 1 | `s05_autotrack_99bundles.tt.gz` | DSI Studio: *Recognize and Cluster* → *Tracts > Save All Tracts As* |
| 2 | `s05_autotrack_99bundles.tt.gz.txt` | Written **automatically** by DSI Studio next to the `.tt.gz` (bundle names/indices) |
| 3 | `s05_connectome_HCP-MMP_ntracts.mat` | DSI Studio: *Tracts > Connectivity matrix* → *Save matrix* |
| 4 | `s05_HCP-MMP_connectivity_for_graph.mat` | **Script** (`graphmat`) — contains the matrix named `connectivity` that Visualize Graph requires |
| 5 | `s05_connectome_nodes_edges_2D.png` | **Script** (`plot`) — 3 views, nodes + edges |
| 6 | `s05_connectome_nodes_edges_3D.png` | **Script** (`plot`) |

Optional: `s05_..._t2r.txt` (Tract-To-Region), `s05_node_metrics.csv` (`metrics`).

## Requirements

- DSI Studio — written against the *Hou, Jul 25 2026* build (Sun 2026.7.25 also recommended): <https://dsi-studio.labsolver.org>. **Not distributed here.**
- HCP-MMP ships with DSI Studio: `<dsi_studio>/atlas/human/HCP-MMP.nii.gz` and `HCP-MMP.txt`.
- Python ≥ 3.10: `pip install -r requirements.txt`

## Full route (verified end-to-end)

Tested with 175,693 tracts → 99 bundles → 360×360 matrix. Screenshots are in the Turkish README (same order).

1. Open `…_s05.qsdr.fz` in Step T3 (atlas `human` in Step T3a).
2. **Fiber Tracking** (Step T3d): whole-brain tractography.
3. **Tracts Misc > Recognize and Cluster** → 99 named bundles.
4. *(optional)* **Regions > Tract-To-Region Connectome (T2R)** → save `_t2r.txt`.
5. **Tracts > Save All Tracts As…** → `s05_autotrack_99bundles.tt.gz` (the `.tt.gz.txt` sidecar appears automatically). Do this *before* merging.
6. **Tracts > Merge All** → one row. *The connectivity matrix is computed from the selected row only*; without merging you get a very sparse matrix from a few hundred tracts.
7. **Tracts > Connectivity matrix:** *Parcellation Atlas* = **HCP-MMP** (the drop-down is easy to mis-click — verify), *pass region*, *value: number of tracts* → **Recalculate** → **Save matrix** → `s05_connectome_HCP-MMP_ntracts.mat`.
8. **Run the script** (below) → graph `.mat` + 2D/3D PNGs.
9. **Tracts > Visualize Graph…** → pick `s05_HCP-MMP_connectivity_for_graph.mat`. In *Step T3c: Options* tick **Region Rendering**, untick **Tract Rendering**.

**Why the script?** In this build the saved matrix file lacks the `connectivity` matrix that Visualize Graph needs ("Cannot find a matrix named connectivity"). `graphmat` rewrites `number of tracts r2r` under that name in DSI Studio's MATLAB v4 format (it matched a hand-made file byte-for-value on real data).

## Fast route (shorter)

Skip steps 3–6 and compute the matrix directly from the `whole_brain` row.

- **Why it should give the same matrix:** in `s05`, Recognize and Cluster assigned **all** 175,693 tracts to one of the 99 bundles (the `cluster` field in the `.tt.gz` is 0–98, none unassigned), and Merge All puts them back together, so the tract set is the same as `whole_brain`.
- **Verification status:** worked directly on `whole_brain` with the Brainnectome atlas; **not tested separately in the GUI with HCP-MMP** (the equivalence above is logical). Please report results via an issue.
- **What you lose:** files 1–2 (the 99-bundle `.tt.gz` + `.tt.gz.txt`), which the `qc` command and bundle-level analyses need.

## Script usage

```bash
python scripts/connectome_tools.py all --mat s05_connectome_HCP-MMP_ntracts.mat \
    --atlas-dir "C:/dsi_studio_win/atlas/human" --prefix s05
python scripts/connectome_tools.py inspect --mat X.mat
python scripts/connectome_tools.py graphmat --mat X.mat --prefix s05
python scripts/connectome_tools.py plot    --mat X.mat --atlas-dir ... --top-edges 400
python scripts/connectome_tools.py metrics --mat X.mat --atlas-dir ... --prefix s05
python scripts/connectome_tools.py qc --tt s05_autotrack_99bundles.tt.gz
```

Nodes = atlas-region centroids (MNI), size = strength, orange = left, blue = right; lines = strongest `--top-edges` connections. Tests: `pytest -q`.

## What next?

1. **QC first.** `python scripts/connectome_tools.py qc --tt s05_autotrack_99bundles.tt.gz` reports tract lengths, the commissural share and, per bundle, the share of tracts whose two ends lie in **different hemispheres**. In the example `s05`:
   - Commissural bundles are 19.8 % of tracts, yet left↔right edges make up only **2.3 %** of the matrix weight.
   - This is not a matrix-computation error: recomputing the matrix independently from the `.tt.gz` (pass mode) correlated 0.98 with DSI Studio's and gave the same 2.3 %.
   - The cause is short, fragmented streamlines: median 52 mm for Corpus Callosum Body, and only 19 % of its tracts end in the opposite hemisphere. Callosal streamlines stop before reaching the contralateral cortical labels, so interhemispheric connections are **under-represented**.
   - Do not interpret interhemispheric connection strengths from this dataset; intrahemispheric edges are more trustworthy. Tracking parameters (min/max length, QA/angular threshold, step size, seed count) and data quality (b-value, resolution) may matter; their effect was **not tested** here.
2. **Normalise.** Raw streamline counts depend on region size, total streamlines and tracking parameters.
3. **Graph metrics** (strength, clustering, efficiency, modularity, hubs) with [bctpy](https://github.com/aestrivex/bctpy) or [networkx](https://networkx.org); report robustness across thresholds.
4. **Bundle-level statistics** from the `.tt.gz` in DSI Studio (QA/FA/length per bundle).
5. **Group comparison:** FDR or NBS; include age/sex/motion covariates.
6. **Interpretation limits:** streamline count ≠ axon count; false positives/negatives exist. Call results tractography-based connectivity estimates.

## Troubleshooting

See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

## Privacy

`.fz`, `.tt.gz`, `.mat`, `.nii.gz` are git-ignored. **Never commit patient/subject data**; file names and screenshot title bars can contain identifiers. Crop/blur your own screenshots.

## License & citations

Scripts/text: **MIT**. **DSI Studio** is CC BY-NC-SA 4.0 and not redistributed — cite Yeh F.-C. (2025) doi:10.1038/s41592-025-02762-8. **HCP-MMP** has its own terms and is not redistributed — cite Glasser et al. (2016) *Nature* 536:171–178.

# DSI Studio → HCP-MMP connectome: a short, illustrated workflow

[Türkçe README → README.md](README.md)

A step-by-step guide plus small Python scripts to go from the **Step T3 `.qsdr.fz`** file in DSI Studio to **99 named tract bundles**, a **360-region (HCP-MMP) connectivity matrix**, and the **coloured balls + edges inside the brain** view (Visualize Graph) by the shortest route.

![Final view: Region Rendering on, Tract Rendering off](docs/images/12_son_gorunum.jpg)

> **Scope:** guide + Python scripts. DSI Studio command-line automation is **out of scope**; DSI Studio steps are done in the GUI.
> **Data:** this repository contains no patient/subject data and must never receive any (see [Privacy](#privacy)).

## Short route (fastest)

1. Open the `.qsdr.fz`, run **Fiber Tracking** (`whole_brain`).
2. **Step T3a > Atlas… > HCP-MMP > Select All > Add** (360 regions).
3. **Tracts > Connectivity matrix** > metric **number of tracts** > **Recalculate** > **Save matrix**.
4. **Tracts > Visualize Graph…** and pick the file you just saved (**Region Rendering ✔, Tract Rendering ☐**).
5. Optional: the [script](#script-usage) (`all`) for 2D/3D pictures and metrics.

This route was tried with the current DSI Studio build (downloaded 3 October 2026); if an older build gives *"Cannot find a matrix named connectivity"* at step 4, see the note under step 10 of the [Full route](#full-route-verified-end-to-end) ("Why the script?"). If you also need the 99-bundle `.tt.gz`, follow the [Full route](#full-route-verified-end-to-end). That the short route gives the same matrix as the full route was tested on one subject only; see the [Fast route](#fast-route-shorter) section.

## Outputs

Example prefix `s05` (use your own).

| # | File | How it is produced |
|---|------|--------------------|
| 1 | `s05_autotrack_99bundles.tt.gz` | DSI Studio: *Recognize and Cluster* → *Tracts > Save All Tracts As* |
| 2 | `s05_autotrack_99bundles.tt.gz.txt` | Written **automatically** by DSI Studio next to the `.tt.gz` (bundle names/indices) |
| 3 | `s05_connectome_HCP-MMP_ntracts.mat` | DSI Studio: *Tracts > Connectivity matrix* → *Save matrix* |
| 4 | `s05_HCP-MMP_connectivity_for_graph.mat` | **Not needed** with the new DSI Studio build (*Save matrix* already writes `connectivity`). With an older build the **script** (`graphmat`) creates it |
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
3. **Load the HCP-MMP regions** (*Step T3a: Assign Regions*): click **Atlas…** → pick **HCP-MMP** (1) → **Select All** (2) → **Add** (3). 360 regions (`L_V1` … `R_p24`) appear in the left panel. Use **Add**, not *Merge&Add* (that merges everything into one region). Needed for the T2R step. See `docs/images/03b_atlas_hcp_mmp_select_all.jpg`.
4. **Tracts Misc > Recognize and Cluster** → 99 named bundles.
5. *(optional)* **Regions > Tract-To-Region Connectome (T2R)** → save `_t2r.txt`.
6. **Tracts > Save All Tracts As…** → `s05_autotrack_99bundles.tt.gz` (the `.tt.gz.txt` sidecar appears automatically). Do this *before* merging.
7. **Tracts > Merge All** → one row. *The connectivity matrix is computed from the selected row only*; without merging you get a very sparse matrix from a few hundred tracts.
8. **Tracts > Connectivity matrix:** *Parcellation Atlas* = **HCP-MMP** (the drop-down is easy to mis-click — verify), *pass region*, *value: number of tracts* → **Recalculate** → **Save matrix** → `s05_connectome_HCP-MMP_ntracts.mat`. DSI Studio's save dialog may suggest its own name (e.g. `Commissure_CorpusCallosum_Body_HCP-MMP.mat`); it comes from the name of the merged row and the matrix is still computed from all tracts. Rename it if you like, and use whatever name you saved under in `--mat` in step 9.
9. **Run the script** (below) → 2D/3D PNGs (and, on an older DSI Studio build, the graph `.mat` for Visualize Graph).
10. **Tracts > Visualize Graph…** → on the new build pick the `.mat` you saved in step 8 **directly**; on an older build pick `s05_HCP-MMP_connectivity_for_graph.mat`. In *Step T3c: Options* tick **Region Rendering**, untick **Tract Rendering**.

**Why the script?** In the Hou Jul 25 2026 build the saved matrix file lacks the `connectivity` matrix that Visualize Graph needs ("Cannot find a matrix named connectivity"). `graphmat` rewrites `number of tracts r2r` under that name in DSI Studio's MATLAB v4 format (it matched a hand-made file byte-for-value on real data).

> **Fixed upstream.** We reported this to the DSI Studio developer ([frankyeh/DSI-Studio#131](https://github.com/frankyeh/DSI-Studio/issues/131)). Root cause, as explained there: the save format was extended to write every per-metric `r2r`/`t2r` matrix, and the legacy `connectivity` entry that Visualize Graph reads was dropped. The fix is on `master`: newer builds also write the **currently selected metric** under the name `connectivity` when you press *Save matrix*, so Visualize Graph opens the file directly. **Verified with the build downloaded on 3 October 2026:** the raw *Save matrix* file opened in Visualize Graph without running the script. It contains 137 matrices (136 in the older build) and `connectivity` is identical to `number of tracts r2r`, the selected metric. Make sure the metric you want (*number of tracts*) is selected before saving. If an older build gives you the error, use the script. The script is still needed for the **2D/3D pictures** (side, front, top views), node metrics and comparisons.
>
> Convenience: `graphmat-surukle-birak.bat` — drag the `.mat` onto it and `<name>_for_graph.mat` appears next to it (needs Python on PATH; not yet widely tested on Windows).

## Fast route (shorter)

Skip steps 4–7 and compute the matrix directly from the `whole_brain` row (steps 8–10). Step 3 should not be needed for the matrix, but I have not tried skipping it.

- **Why it should give the same matrix:** in `s05`, Recognize and Cluster assigned **all** 175,693 tracts to one of the 99 bundles (the `cluster` field in the `.tt.gz` is 0–98, none unassigned), and Merge All puts them back together, so the tract set is the same as `whole_brain`.
- **Verification status:** tested in the GUI with HCP-MMP on the same `s05` data (steps 4–7 skipped; step 3 done). The full-route and fast-route matrices come from **two separate tracking runs**, so they are not identical; `compare` gave: total-weight ratio 0.996, Pearson r = 0.995, 93 % overlap of the strongest 400 edges, interhemispheric share 2.43 % vs 2.36 %. Spearman (0.89) and edge Jaccard (0.74) were lower; the difference sits in weak (low-streamline-count) edges. **Test-retest control:** running the fast route a second time with fresh tracking (on a different DSI Studio build) gave a difference between the two fast matrices of the same size as between full and fast route (Pearson 0.9955 / 0.9952; Spearman 0.888 / 0.889; Jaccard 0.735 / 0.736; strongest-400 overlap 0.935 / 0.932). So the difference seems to come from tracking randomness rather than from the skipped steps, and the fast route gave the same result as the full route on this data. Limits: one subject; the second run used a different build, so a build effect cannot be separated from a tracking effect; many weak edges change from run to run, so be careful with binary (present/absent) graph metrics.
- **What you lose:** files 1–2 (the 99-bundle `.tt.gz` + `.tt.gz.txt`), which the `qc` command and bundle-level analyses need.

## Script usage

The script turns the `.mat` saved by DSI Studio into 2D/3D images (and, for older builds, the graph file). **In Windows PowerShell**, first edit only the paths in the 4 lines below (`USER` and the file name), then paste the commands **as they are**.

```powershell
# 1) Edit these 4 lines for your machine
$repo  = "C:\Users\USER\Desktop\son_dti_kurs\dsistudio-connectome-guide"
$mat   = "C:\Users\USER\Desktop\son_dti_kurs\YOUR_SAVED_FILE.mat"
$atlas = "C:\Users\USER\Desktop\son_dti_kurs\dsi_studio_win\atlas\human"
$tt    = "C:\Users\USER\Desktop\son_dti_kurs\s05_autotrack_99bundles.tt.gz"
```

```powershell
# 2) Paste these unchanged
cd $repo
pip install -r requirements.txt
python scripts\connectome_tools.py all --mat $mat --atlas-dir $atlas --prefix s05
```

`$mat` must be the full path of the file **you** saved with *Save matrix* in DSI Studio (e.g. `...\Commissure_CorpusCallosum_Body_HCP-MMP.mat`). If it is wrong, the script lists the `.mat` files in that folder. Run the commands inside this repository's folder, not the DSI Studio folder (`cd $repo` does that).

`all` is enough. The following are optional, each doing one part of `all` or an extra analysis; paste them unchanged with the same variables:

```powershell
python scripts\connectome_tools.py inspect  --mat $mat                                  # list matrices in the .mat
python scripts\connectome_tools.py graphmat --mat $mat --prefix s05                      # only the Visualize Graph .mat
python scripts\connectome_tools.py plot     --mat $mat --atlas-dir $atlas --prefix s05   # only the 2D/3D images
python scripts\connectome_tools.py metrics  --mat $mat --atlas-dir $atlas --prefix s05   # node metrics CSV
python scripts\connectome_tools.py qc       --tt $tt                                     # tract/bundle QC
python scripts\connectome_tools.py compare  --mat $mat --mat2 $mat2 --atlas-dir $atlas    # compare two matrices ($mat2: second .mat)
```

**Linux / macOS / Git Bash** (a trailing `\` is bash syntax):

```bash
python scripts/connectome_tools.py all --mat ~/YOUR_SAVED_FILE.mat \
    --atlas-dir "<dsi_studio>/atlas/human" --prefix s05
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

#!/usr/bin/env python3
"""DSI Studio konnektom yardimcilari.

Alt komutlar
------------
inspect   .mat dosyasindaki matrisleri listeler (boyut, toplam, dolu hucre sayisi).
graphmat  "Visualize Graph" icin 'connectivity' adli matris iceren uyumlu bir .mat yazar.
plot      Bolge merkezlerini top, baglantilari cizgi olarak 2B (3 gorunum) ve 3B PNG'ye cizer.
all       graphmat + plot (en kisa yol).
qc        .tt.gz uzerinden kalite kontrol (uzunluk, komisural demetler, karsi yariküreye ulasma).
metrics   Dugum (bolge) bazinda derece/guc ve genel ozet metrikleri CSV'ye yazar.

Ornek
-----
python scripts/connectome_tools.py all \
    --mat  C:/Users/ben/Desktop/s05_connectome_HCP-MMP_ntracts.mat \
    --atlas-dir "C:/dsi_studio_win/atlas/human" \
    --prefix s05
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsi_mat import read_mat4, square_matrices, write_mat4  # noqa: E402

DEFAULT_MEASURE = "number of tracts r2r"


# --------------------------------------------------------------------------- inspect
def cmd_inspect(args) -> int:
    recs = read_mat4(args.mat)
    print(f"{args.mat}: {len(recs)} matris")
    print(f"{'ad':50s} {'boyut':>10s} {'toplam':>14s} {'dolu':>8s}")
    for name, r in recs.items():
        print(f"{name:50s} {r.rows:>4d}x{r.cols:<5d} {r.data.sum():>14.4g} {int((r.data != 0).sum()):>8d}")
    sq = square_matrices(recs)
    if sq:
        n = next(iter(sq.values())).rows
        print(f"\nBolge sayisi (n x n matrislerden): {n}")
        if DEFAULT_MEASURE in sq:
            print(f"'{DEFAULT_MEASURE}' mevcut -> graphmat/plot icin hazir.")
    return 0


# --------------------------------------------------------------------------- graphmat
def make_graph_mat(src: Path, dst: Path, measure: str = DEFAULT_MEASURE) -> int:
    recs = read_mat4(src)
    if measure not in recs:
        raise SystemExit(f"'{measure}' bulunamadi. Mevcut kare matrisler: {list(square_matrices(recs))[:8]} ...")
    r = recs[measure]
    if r.rows != r.cols:
        raise SystemExit(f"'{measure}' kare degil ({r.rows}x{r.cols}); '... r2r' matrisini secin.")
    write_mat4(dst, {"connectivity": r.data})
    return r.rows


def cmd_graphmat(args) -> int:
    dst = Path(args.out) if args.out else Path(args.mat).with_name(f"{args.prefix}_HCP-MMP_connectivity_for_graph.mat")
    n = make_graph_mat(Path(args.mat), dst, args.measure)
    print(f"tamam: {dst}  ({n} x {n}, '{args.measure}' -> 'connectivity')")
    print("DSI Studio: Tracts > Visualize Graph... ile bu dosyayi secin.")
    return 0


# --------------------------------------------------------------------------- plot
def load_atlas(atlas_dir: Path, atlas: str):
    import nibabel as nib

    nii = atlas_dir / f"{atlas}.nii.gz"
    txt = atlas_dir / f"{atlas}.txt"
    if not nii.exists() or not txt.exists():
        raise SystemExit(
            f"Atlas dosyalari yok: {nii} / {txt}\n"
            "--atlas-dir DSI Studio klasoru icindeki atlas/human klasorunu gostermeli."
        )
    img = nib.load(str(nii))
    lab = np.asarray(img.dataobj).astype(int)
    names = {}
    for line in txt.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            names[int(parts[0])] = parts[1].strip()
    return img, lab, names


def region_centroids(img, lab, n):
    import nibabel as nib

    cent = np.full((n, 3), np.nan)
    for i in range(1, n + 1):
        idx = np.argwhere(lab == i)
        if len(idx):
            cent[i - 1] = nib.affines.apply_affine(img.affine, idx.mean(0))
    return cent


def plot_connectome(mat: Path, atlas_dir: Path, atlas: str, outdir: Path, prefix: str,
                    measure: str = DEFAULT_MEASURE, top_edges: int = 400, dpi: int = 140):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from scipy import ndimage as ndi

    recs = read_mat4(mat)
    if measure not in recs:
        raise SystemExit(f"'{measure}' bulunamadi (mevcut: {list(recs)[:6]} ...)")
    M = recs[measure].data.copy()
    n = M.shape[0]
    M = (M + M.T) / 2
    np.fill_diagonal(M, 0)

    img, lab, names = load_atlas(atlas_dir, atlas)
    if lab.max() != n:
        raise SystemExit(
            f"Atlas {int(lab.max())} bolgeli, matris {n} x {n}. DSI Studio'da matrisi hesaplarken "
            f"'Parcellation Atlas' kutusunda {atlas} secili olmali."
        )
    names_l = [names.get(i, f"R{i}") for i in range(1, n + 1)]
    C = region_centroids(img, lab, n)

    strength = M.sum(1)
    iu = np.triu_indices(n, 1)
    w = M[iu]
    order = np.argsort(w)[::-1]
    order = order[w[order] > 0][:top_edges]
    I, J, W = iu[0][order], iu[1][order], w[order]
    left = C[:, 0] < 0  # MNI: x < 0 sol
    col = np.where(left, "#e8743b", "#2f7fd1")
    size = 20 + 260 * (strength / max(strength.max(), 1)) ** 0.7

    # beyin siluet: atlas doluluk maskesi
    mask = ndi.binary_closing(ndi.binary_dilation(lab > 0, iterations=3), iterations=4)
    aff = img.affine
    o, s = aff[:3, 3], aff[0, 0]
    sh = mask.shape
    ext = {
        0: (o[1], o[1] + s * sh[1], o[2], o[2] + s * sh[2]),
        1: (o[0], o[0] + s * sh[0], o[2], o[2] + s * sh[2]),
        2: (o[0], o[0] + s * sh[0], o[1], o[1] + s * sh[1]),
    }
    views = [("Sagittal", (1, 2), 0), ("Koronal", (0, 2), 1), ("Aksiyel", (0, 1), 2)]
    lw = 0.3 + 2.6 * (W / W.max()) ** 0.6 if len(W) else []

    fig, axs = plt.subplots(1, 3, figsize=(18, 6.4), facecolor="white")
    for ax, (title, (a, b), pa) in zip(axs, views):
        e = ext[pa]
        sil = mask.any(pa).T.astype(float)
        ax.imshow(sil, origin="lower", extent=e, cmap="Greys", alpha=0.25, vmin=0, vmax=1.2)
        ax.contour(np.linspace(e[0], e[1], sil.shape[1]), np.linspace(e[2], e[3], sil.shape[0]),
                   sil, levels=[0.5], colors="#555", linewidths=1)
        segs = [[(C[i, a], C[i, b]), (C[j, a], C[j, b])] for i, j in zip(I, J)]
        ax.add_collection(LineCollection(segs, linewidths=lw, colors=[(0.2, 0.2, 0.2, 0.45)], zorder=2))
        ax.scatter(C[:, a], C[:, b], s=size, c=col, edgecolors="white", linewidths=0.4, zorder=3, alpha=0.9)
        ax.set_title(title, fontsize=14)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(f"{atlas} ({n}) traktografi konnektomu: dugum = bolge (boyut = guc, turuncu = sol, mavi = sag); "
                 f"baglanti = en guclu {len(W)} kenar", fontsize=13)
    plt.tight_layout()
    outdir.mkdir(parents=True, exist_ok=True)
    f2 = outdir / f"{prefix}_connectome_nodes_edges_2D.png"
    fig.savefig(f2, dpi=dpi)
    plt.close(fig)

    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")
    for i, j, wv in zip(I, J, W):
        ax.plot([C[i, 0], C[j, 0]], [C[i, 1], C[j, 1]], [C[i, 2], C[j, 2]],
                color=(0.25, 0.25, 0.25, 0.3), lw=0.3 + 2.2 * (wv / W.max()) ** 0.6)
    ax.scatter(C[:, 0], C[:, 1], C[:, 2], s=size, c=col, edgecolors="white", linewidths=0.3, depthshade=True)
    ax.view_init(elev=25, azim=-60)
    ax.set_axis_off()
    ax.set_box_aspect((1, 1.25, 0.9))
    plt.title(f"3B konnektom ({atlas})")
    plt.tight_layout()
    f3 = outdir / f"{prefix}_connectome_nodes_edges_3D.png"
    fig.savefig(f3, dpi=dpi)
    plt.close(fig)

    top = np.argsort(strength)[::-1][:10]
    print("En guclu 10 dugum:", ", ".join(f"{names_l[i]} ({int(strength[i])})" for i in top))
    return f2, f3


def cmd_plot(args) -> int:
    f2, f3 = plot_connectome(Path(args.mat), Path(args.atlas_dir), args.atlas,
                             Path(args.outdir) if args.outdir else Path(args.mat).parent,
                             args.prefix, args.measure, args.top_edges, args.dpi)
    print(f"tamam:\n  {f2}\n  {f3}")
    return 0


def cmd_all(args) -> int:
    outdir = Path(args.outdir) if args.outdir else Path(args.mat).parent
    dst = outdir / f"{args.prefix}_HCP-MMP_connectivity_for_graph.mat"
    outdir.mkdir(parents=True, exist_ok=True)
    n = make_graph_mat(Path(args.mat), dst, args.measure)
    print(f"[1/2] {dst}  ({n} x {n})")
    f2, f3 = plot_connectome(Path(args.mat), Path(args.atlas_dir), args.atlas, outdir,
                             args.prefix, args.measure, args.top_edges, args.dpi)
    print(f"[2/2] {f2}\n      {f3}")
    print("\nSimdi DSI Studio: Tracts > Visualize Graph... > " + dst.name)
    return 0


# --------------------------------------------------------------------------- qc
def cmd_qc(args) -> int:
    from dsi_tt import qc_report, read_tt

    t = read_tt(args.tt)
    r = qc_report(t)
    ln = r["length_mm"]
    print(f"Trakt sayisi: {r['n_tracts']}")
    print(f"Uzunluk (mm): ort {ln['mean']:.0f}, medyan {ln['median']:.0f}, p10 {ln['p10']:.0f}, p90 {ln['p90']:.0f}")
    print(f"Iki ucu farkli yarikurede olan trakt: %{r['ends_opposite_hemispheres_pct']:.1f}")
    print(f"Komisural demetlerin payi: %{r['commissure_share_pct']:.1f}")
    print(f"\n{'demet':55s} {'n':>7s} {'pay%':>6s} {'med.uz.':>8s} {'karsi%':>7s}")
    shown = [b for b in r["bundles"] if b["name"].startswith("Commissure")] + \
            [b for b in r["bundles"] if not b["name"].startswith("Commissure")][:args.top]
    for b in shown:
        print(f"{b['name']:55s} {b['n']:7d} {b['share_pct']:6.1f} {b['median_length_mm']:8.0f} {b['ends_opposite_pct']:7.0f}")
    print("\nYorum: callosal demetlerde 'karsi%' dusukse izler karsi yarikureye ulasamadan bitiyor "
          "(kisa/parcali) -> konnektomda sol-sag baglanti payi dusuk cikar.")
    return 0


# --------------------------------------------------------------------------- metrics
def node_metrics(M: np.ndarray, names: list[str]):
    """Temel agirlikli graf metrikleri (yalniz numpy). Dondurur: (satirlar, ozet sozlugu)."""
    M = (M + M.T) / 2
    np.fill_diagonal(M, 0)
    n = len(M)
    strength = M.sum(1)
    degree = (M > 0).sum(1)
    left = np.array([nm.startswith("L_") for nm in names])
    right = np.array([nm.startswith("R_") for nm in names])
    inter = float(M[np.ix_(left, right)].sum()) if left.any() and right.any() else float("nan")
    total = float(M[np.triu_indices(n, 1)].sum())
    rows = []
    for i in range(n):
        rows.append((names[i], "L" if left[i] else "R" if right[i] else "?", int(degree[i]),
                     float(strength[i]), float(strength[i] / strength.sum()) if strength.sum() else 0.0))
    summary = {
        "n_regions": n,
        "n_edges_nonzero": int((np.triu(M, 1) > 0).sum()),
        "density": float((np.triu(M, 1) > 0).sum() / (n * (n - 1) / 2)),
        "total_weight": total,
        "interhemispheric_fraction": inter / total if total else float("nan"),
    }
    return rows, summary


def cmd_metrics(args) -> int:
    import csv

    recs = read_mat4(args.mat)
    if args.measure not in recs:
        raise SystemExit(f"'{args.measure}' bulunamadi.")
    M = recs[args.measure].data.copy()
    _, _, names = load_atlas(Path(args.atlas_dir), args.atlas)
    nl = [names.get(i, f"R{i}") for i in range(1, len(M) + 1)]
    rows, summ = node_metrics(M, nl)
    out = Path(args.outdir) if args.outdir else Path(args.mat).parent
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"{args.prefix}_node_metrics.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["region", "hemisphere", "degree", "strength", "strength_fraction"])
        w.writerows(rows)
    for k, v in summ.items():
        print(f"{k:28s} {v}")
    print(f"tamam: {f}")
    return 0


# --------------------------------------------------------------------------- cli
def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, plot=False):
        sp.add_argument("--mat", required=True, help="DSI Studio 'Save matrix...' ile kaydedilen .mat")
        sp.add_argument("--measure", default=DEFAULT_MEASURE, help=f"Matris adi (varsayilan: '{DEFAULT_MEASURE}')")
        sp.add_argument("--prefix", default="subj", help="Cikti dosya on eki (ornek: s05)")
        if plot:
            sp.add_argument("--atlas-dir", required=True,
                            help="DSI Studio klasoru icindeki atlas/human yolu (HCP-MMP.nii.gz ve HCP-MMP.txt burada)")
            sp.add_argument("--atlas", default="HCP-MMP")
            sp.add_argument("--top-edges", type=int, default=400, help="Cizilecek en guclu baglanti sayisi")
            sp.add_argument("--dpi", type=int, default=140)
            sp.add_argument("--outdir", help="Cikti klasoru (varsayilan: .mat ile ayni klasor)")

    sp = sub.add_parser("inspect", help=cmd_inspect.__doc__ or "matrisleri listele")
    sp.add_argument("--mat", required=True)
    sp.set_defaults(fn=cmd_inspect)

    sp = sub.add_parser("graphmat", help="Visualize Graph icin uyumlu .mat")
    common(sp)
    sp.add_argument("--out", help="Cikti dosyasi (varsayilan: <prefix>_HCP-MMP_connectivity_for_graph.mat)")
    sp.set_defaults(fn=cmd_graphmat)

    sp = sub.add_parser("plot", help="2B/3B PNG")
    common(sp, plot=True)
    sp.set_defaults(fn=cmd_plot)

    sp = sub.add_parser("all", help="graphmat + plot")
    common(sp, plot=True)
    sp.set_defaults(fn=cmd_all)

    sp = sub.add_parser("qc", help=".tt.gz kalite kontrol")
    sp.add_argument("--tt", required=True, help="DSI Studio .tt.gz (yaninda .tt.gz.txt varsa demet adlari okunur)")
    sp.add_argument("--top", type=int, default=8, help="komisural olmayan en buyuk N demet de listelenir")
    sp.set_defaults(fn=cmd_qc)

    sp = sub.add_parser("metrics", help="dugum metrikleri CSV")
    common(sp, plot=True)
    sp.set_defaults(fn=cmd_metrics)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())

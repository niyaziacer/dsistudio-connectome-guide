import nibabel as nib
import numpy as np
import pytest

import connectome_tools as ct
from dsi_mat import read_mat4, write_mat4

N = 8


@pytest.fixture()
def data(tmp_path):
    rng = np.random.default_rng(1)
    A = np.triu(rng.integers(0, 30, (N, N)).astype(float), 1)
    A = A + A.T
    mat = tmp_path / "s_ntracts.mat"
    write_mat4(mat, {"number of tracts t2r": A.sum(1), "number of tracts r2r": A})

    # kucuk sentetik atlas: 8 kup bolge, 2 mm, x ekseni ters (MNI benzeri)
    lab = np.zeros((20, 20, 20), np.int16)
    k = 1
    for x in (2, 12):
        for y in (2, 12):
            for z in (2, 12):
                lab[x:x + 5, y:y + 5, z:z + 5] = k
                k += 1
    aff = np.diag([2.0, 2.0, 2.0, 1.0])
    aff[:3, 3] = [-20, -20, -20]
    ad = tmp_path / "atlas"
    ad.mkdir()
    nib.save(nib.Nifti1Image(lab, aff), str(ad / "TEST.nii.gz"))
    (ad / "TEST.txt").write_text("\n".join(f"{i} R{i}" for i in range(1, N + 1)))
    return A, mat, ad


def test_graphmat_has_connectivity(data, tmp_path):
    A, mat, _ = data
    out = tmp_path / "g.mat"
    assert ct.make_graph_mat(mat, out) == N
    recs = read_mat4(out)
    assert list(recs) == ["connectivity"]
    assert np.allclose(recs["connectivity"].data, A)


def test_graphmat_missing_measure(data, tmp_path):
    _, mat, _ = data
    with pytest.raises(SystemExit):
        ct.make_graph_mat(mat, tmp_path / "g.mat", "yok")


def test_inspect_runs(data, capsys):
    _, mat, _ = data
    assert ct.main(["inspect", "--mat", str(mat)]) == 0
    assert "number of tracts r2r" in capsys.readouterr().out


def test_all_creates_outputs(data, tmp_path):
    _, mat, ad = data
    out = tmp_path / "out"
    rc = ct.main(["all", "--mat", str(mat), "--atlas-dir", str(ad), "--atlas", "TEST",
                  "--prefix", "s05", "--outdir", str(out), "--dpi", "40"])
    assert rc == 0
    for name in ("s05_HCP-MMP_connectivity_for_graph.mat",
                 "s05_connectome_nodes_edges_2D.png",
                 "s05_connectome_nodes_edges_3D.png"):
        assert (out / name).stat().st_size > 0


def test_atlas_region_count_mismatch(data, tmp_path):
    _, mat, ad = data
    A = np.ones((5, 5))
    bad = tmp_path / "bad.mat"
    write_mat4(bad, {"number of tracts r2r": A})
    with pytest.raises(SystemExit):
        ct.plot_connectome(bad, ad, "TEST", tmp_path / "o", "x", dpi=40)


def test_node_metrics_basic():
    M = np.zeros((4, 4))
    M[0, 1] = M[1, 0] = 5   # L-L
    M[0, 2] = M[2, 0] = 3   # L-R
    M[2, 3] = M[3, 2] = 2   # R-R
    rows, s = ct.node_metrics(M, ["L_a", "L_b", "R_a", "R_b"])
    assert s["n_edges_nonzero"] == 3 and s["total_weight"] == 10
    assert abs(s["interhemispheric_fraction"] - 0.3) < 1e-9
    assert rows[0][2] == 2 and rows[0][3] == 8


def test_metrics_cli(data, tmp_path):
    _, mat, ad = data
    # sentetik atlas adlari "R1".. -> hemisfer '?' olur, yine de calismali
    rc = ct.main(["metrics", "--mat", str(mat), "--atlas-dir", str(ad), "--atlas", "TEST",
                  "--prefix", "s05", "--outdir", str(tmp_path)])
    assert rc == 0 and (tmp_path / "s05_node_metrics.csv").exists()

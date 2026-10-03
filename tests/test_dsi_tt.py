import gzip
import struct

import numpy as np

from dsi_tt import qc_report, read_tt


def _rec(name, mtype, rows, cols, raw):
    nb = name.encode() + b"\0"
    return struct.pack("<5i", mtype, rows, cols, 0, len(nb)) + nb + raw


def make_tt(path, tracts_vox, cluster, names=None):
    """tracts_vox: list of (n,3) voxel koordinat dizileri; trans_to_mni: x ters, 2 mm."""
    stream = b""
    for pts in tracts_vox:
        q = np.rint(np.asarray(pts) * 32).astype(np.int32)
        d = np.diff(q, axis=0).astype(np.int8)
        stream += struct.pack("<I", 3 * len(q)) + q[0].astype("<i4").tobytes() + d.tobytes()
    T = np.array([[-2, 0, 0, 80], [0, -2, 0, 80], [0, 0, 2, -70], [0, 0, 0, 1]], float)
    raw = (_rec("dimension", 20, 1, 3, np.array([80, 100, 80], "<i4").tobytes())
           + _rec("voxel_size", 10, 1, 3, np.array([2, 2, 2], "<f4").tobytes())
           + _rec("trans_to_mni", 10, 1, 16, T.reshape(-1).astype("<f4").tobytes())
           + _rec("cluster", 40, 1, len(cluster), np.array(cluster, "<u2").tobytes())
           + _rec("track", 50, len(stream), 1, stream))
    with gzip.open(path, "wb") as f:
        f.write(raw)
    if names:
        open(str(path) + ".txt", "w").write("\n".join(names))


def test_read_and_qc(tmp_path):
    # voxel x=40 -> MNI 0. Trakt A: 30 -> 50 (karsi taraflar), Trakt B: ayni yarikure
    a = np.c_[np.linspace(30, 50, 21), np.full(21, 50.0), np.full(21, 40.0)]
    b = np.c_[np.linspace(45, 55, 11), np.full(11, 50.0), np.full(11, 40.0)]
    f = tmp_path / "x.tt.gz"
    make_tt(f, [a, b], [0, 1], ["Commissure_CorpusCallosum_Body", "Association_ArcuateFasciculusL"])
    t = read_tt(f)
    assert t.n == 2
    assert np.allclose(t.points_mni[t.starts[0]], [-2 * 30 + 80, -2 * 50 + 80, 2 * 40 - 70], atol=0.05)
    assert abs(t.lengths()[0] - 40.0) < 0.5      # 20 voxel * 2 mm
    r = qc_report(t)
    assert r["n_tracts"] == 2
    assert r["ends_opposite_hemispheres_pct"] == 50.0
    assert r["commissure_share_pct"] == 50.0
    body = [x for x in r["bundles"] if x["name"].endswith("Body")][0]
    assert body["ends_opposite_pct"] == 100.0


def test_not_a_tt(tmp_path):
    import pytest
    f = tmp_path / "bad.tt.gz"
    with gzip.open(f, "wb") as g:
        g.write(b"\xff" * 80)
    with pytest.raises(ValueError):
        read_tt(f)

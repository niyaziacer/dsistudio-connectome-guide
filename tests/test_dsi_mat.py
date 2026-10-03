import numpy as np
import pytest

from dsi_mat import read_mat4, square_matrices, write_mat4


def test_roundtrip_square_and_vector(tmp_path):
    rng = np.random.default_rng(0)
    A = rng.integers(0, 50, (6, 6)).astype(float)
    v = rng.random(6)
    f = tmp_path / "x.mat"
    write_mat4(f, {"number of tracts r2r": A, "number of tracts t2r": v})
    recs = read_mat4(f)
    assert list(recs) == ["number of tracts r2r", "number of tracts t2r"]
    assert np.allclose(recs["number of tracts r2r"].data, A)
    assert recs["number of tracts t2r"].data.shape == (6, 1)
    assert np.allclose(recs["number of tracts t2r"].data[:, 0], v, atol=1e-6)
    assert list(square_matrices(recs)) == ["number of tracts r2r"]


def test_non_symmetric_orientation_preserved(tmp_path):
    A = np.arange(12, dtype=float).reshape(3, 4)  # column-major hatasi yakalansin
    f = tmp_path / "r.mat"
    write_mat4(f, {"a": A})
    assert np.array_equal(read_mat4(f)["a"].data, A)


def test_garbage_file_rejected(tmp_path):
    f = tmp_path / "bad.mat"
    f.write_bytes(b"\xff" * 64)
    with pytest.raises(ValueError):
        read_mat4(f)


def test_truncated_file_rejected(tmp_path):
    f = tmp_path / "t.mat"
    write_mat4(f, {"a": np.ones((4, 4))})
    f.write_bytes(f.read_bytes()[:-10])
    with pytest.raises(ValueError):
        read_mat4(f)

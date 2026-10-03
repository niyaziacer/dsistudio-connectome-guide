"""DSI Studio'nun yazdigi MATLAB v4 (.mat) dosyalarini okuma/yazma yardimcilari.

DSI Studio "Save matrix..." ile MATLAB Level 4 bicimi kullanir. Her kayit:
    5 x int32 baslik: tip, satir, sutun, karmasik_mi, ad_uzunlugu
    ad (NUL ile biter), sonra sutun-oncelikli (Fortran sirali) veri.
tip = M*1000 + O*100 + P*10 + T; bizim icin P (veri tipi) ve T (0 = tam matris) onemli.
Yalnizca numpy gerekir (scipy gerekmez).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# P rakami -> (numpy dtype, bayt)
_DTYPES = {
    0: np.dtype("<f8"),
    1: np.dtype("<f4"),
    2: np.dtype("<i4"),
    3: np.dtype("<i2"),
    4: np.dtype("<u2"),
    5: np.dtype("<u1"),
}


@dataclass
class Record:
    name: str
    mtype: int
    rows: int
    cols: int
    data: np.ndarray  # (rows, cols) float64


def read_mat4(path: str | Path) -> dict[str, Record]:
    """Dosyadaki tum matrisleri {ad: Record} olarak dondurur."""
    buf = Path(path).read_bytes()
    pos, out = 0, {}
    while pos + 20 <= len(buf):
        mtype, mrows, ncols, imagf, namlen = struct.unpack("<5i", buf[pos:pos + 20])
        p_digit = (mtype // 10) % 10
        if mtype < 0 or p_digit not in _DTYPES or imagf not in (0, 1) or namlen <= 0:
            raise ValueError(
                f"{path}: pozisyon {pos}'de MATLAB v4 basligi tanimlanamadi "
                f"(tip={mtype}). Dosya DSI Studio .mat'i mi?"
            )
        name = buf[pos + 20:pos + 20 + namlen - 1].decode("utf-8", "replace")
        dt = _DTYPES[p_digit]
        n = mrows * ncols * (2 if imagf else 1)
        start = pos + 20 + namlen
        end = start + n * dt.itemsize
        if end > len(buf):
            raise ValueError(f"{path}: '{name}' kaydi dosya sonundan tasiyor (bozuk/kesik dosya).")
        arr = np.frombuffer(buf[start:end], dtype=dt)
        if imagf:  # gercek kismi al
            arr = arr[: mrows * ncols]
        mat = arr.reshape(ncols, mrows).T.astype(np.float64)  # sutun-oncelikli
        out[name] = Record(name, mtype, mrows, ncols, mat)
        pos = end
    return out


def write_mat4(path: str | Path, matrices: dict[str, np.ndarray]) -> None:
    """{ad: 2B dizi} sozlugunu float32 MATLAB v4 olarak yazar (DSI Studio ile ayni tip: 10)."""
    chunks = []
    for name, m in matrices.items():
        m = np.asarray(m, dtype="<f4")
        if m.ndim == 1:
            m = m[:, None]
        nb = name.encode("utf-8") + b"\0"
        chunks.append(struct.pack("<5i", 10, m.shape[0], m.shape[1], 0, len(nb)) + nb + m.T.tobytes())
    Path(path).write_bytes(b"".join(chunks))


def square_matrices(recs: dict[str, Record]) -> dict[str, Record]:
    """Yalniz n x n (bolge-bolge, 'r2r') matrisleri."""
    return {k: v for k, v in recs.items() if v.rows == v.cols and v.rows > 1}

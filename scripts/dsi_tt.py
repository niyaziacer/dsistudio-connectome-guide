"""DSI Studio .tt.gz (TT) dosyasi okuyucu ve basit kalite kontrol (QC) istatistikleri.

Biçim (DSI Studio .tt.gz = gzip'li MATLAB v4): dimension, voxel_size, trans_to_mni, color,
cluster (trakt basina demet indeksi, uint16), track (uint8 akis).
'track' akisi trakt basina: uint32 L (= 3 * nokta sayisi), 3 x int32 ilk nokta (voxel * 32),
sonra (L-3) adet int8 fark (onceki noktaya gore, 1/32 voxel).
Koordinatlar 'trans_to_mni' (3x4) ile MNI mm'ye cevrilir.
Dogrulama: 175.693 trakt, ortalama adim 2.0 mm, ortalama uzunluk ~62 mm (DSI Studio'nun
'mean length' matrisiyle uyumlu).
"""
from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_DT = {0: "<f8", 1: "<f4", 2: "<i4", 3: "<i2", 4: "<u2", 5: "<u1"}


@dataclass
class Tracts:
    points_mni: np.ndarray   # (N, 3) mm
    starts: np.ndarray       # her traktin ilk nokta indeksi
    ends: np.ndarray         # son nokta indeksi
    cluster: np.ndarray      # (n_tract,) demet indeksi (yoksa tek demet)
    names: list[str]         # demet adlari (varsa)

    @property
    def n(self) -> int:
        return len(self.starts)

    def lengths(self) -> np.ndarray:
        step = np.linalg.norm(np.diff(self.points_mni, axis=0), axis=1)
        csum = np.r_[0.0, np.cumsum(step)]
        return csum[self.ends] - csum[self.starts]


def _read_records(buf: bytes) -> dict[str, np.ndarray]:
    pos, out = 0, {}
    while pos + 20 <= len(buf):
        t, r, c, imagf, nl = struct.unpack("<5i", buf[pos:pos + 20])
        p = (t // 10) % 10
        if t < 0 or p not in _DT or nl <= 0:
            raise ValueError(f"TT basligi taninamadi (pozisyon {pos}); DSI Studio .tt.gz dosyasi mi?")
        name = buf[pos + 20:pos + 20 + nl - 1].decode("utf-8", "replace")
        s = pos + 20 + nl
        e = s + r * c * np.dtype(_DT[p]).itemsize
        if e > len(buf):
            raise ValueError("TT dosyasi kesik/bozuk.")
        out[name] = np.frombuffer(buf[s:e], dtype=_DT[p])
        pos = e
    return out


def read_tt(path: str | Path) -> Tracts:
    path = Path(path)
    rec = _read_records(gzip.open(path).read())
    for k in ("track", "trans_to_mni"):
        if k not in rec:
            raise ValueError(f"'{k}' kaydi yok; {path} bir TT dosyasi degil.")
    tr = rec["track"]
    offs, npts, p = [], [], 0
    while p < len(tr):
        L = int(tr[p:p + 4].view("<u4")[0])
        if L < 3 or L % 3:
            raise ValueError("track akisi bozuk.")
        offs.append(p)
        npts.append(L // 3)
        p += 4 + 12 + (L - 3)
    offs, npts = np.array(offs), np.array(npts)
    pts = np.empty((int(npts.sum()), 3), np.float64)
    k = 0
    for o, n in zip(offs, npts):
        first = tr[o + 4:o + 16].view("<i4").astype(np.float64) / 32.0
        pts[k] = first
        if n > 1:
            d = tr[o + 16:o + 16 + 3 * (n - 1)].view(np.int8).reshape(-1, 3).astype(np.float64) / 32.0
            pts[k + 1:k + n] = first + np.cumsum(d, 0)
        k += n
    T = rec["trans_to_mni"].astype(np.float64).reshape(4, 4)[:3]  # 3x4 satir
    mni = pts @ T[:, :3].T + T[:, 3]
    starts = np.r_[0, np.cumsum(npts)[:-1]]
    cluster = rec["cluster"].astype(int) if "cluster" in rec else np.zeros(len(offs), int)
    names = []
    txt = Path(str(path) + ".txt")
    if txt.exists():
        names = [l.strip() for l in txt.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    return Tracts(mni, starts, starts + npts - 1, cluster, names)


def qc_report(t: Tracts, top: int = 8) -> dict:
    """Ozet QC: uzunluk dagilimi, karsi yarikureye ulasan trakt orani, komisural demetler."""
    ln = t.lengths()
    opp = np.sign(t.points_mni[t.starts, 0]) != np.sign(t.points_mni[t.ends, 0])
    rep = {
        "n_tracts": t.n,
        "length_mm": {"mean": float(ln.mean()), "median": float(np.median(ln)),
                      "p10": float(np.percentile(ln, 10)), "p90": float(np.percentile(ln, 90))},
        "ends_opposite_hemispheres_pct": float(100 * opp.mean()),
        "bundles": [],
    }
    for k in np.unique(t.cluster):
        idx = np.where(t.cluster == k)[0]
        nm = t.names[k] if k < len(t.names) else f"cluster{k}"
        rep["bundles"].append({
            "name": nm, "n": int(len(idx)), "share_pct": float(100 * len(idx) / t.n),
            "median_length_mm": float(np.median(ln[idx])),
            "ends_opposite_pct": float(100 * opp[idx].mean()),
        })
    rep["bundles"].sort(key=lambda b: -b["n"])
    comm = [b for b in rep["bundles"] if b["name"].startswith("Commissure")]
    rep["commissure_share_pct"] = float(sum(b["share_pct"] for b in comm))
    return rep

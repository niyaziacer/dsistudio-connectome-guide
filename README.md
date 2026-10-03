# DSI Studio → Konnektom (HCP-MMP) hızlı rehberi

[English README → README.en.md](README.en.md)

DSI Studio'da **Step T3** aşamasındaki `.qsdr.fz` dosyasından başlayıp **99 demetlik traktografi**, **360 bölgeli (HCP-MMP) konnektivite matrisi** ve beyin içinde **renkli toplar + bağlantılar** görünümünü (Visualize Graph) en kısa yoldan elde etmek için adım adım, görsel anlatımlı bir rehber ve küçük Python betikleri.

![Son görünüm: Region Rendering açık, Tract Rendering kapalı](docs/images/12_son_gorunum.jpg)

> **Kapsam:** Rehber + Python betikleri. DSI Studio komut satırı otomasyonu (`dsi_studio --action=...`) **kapsam dışıdır**; DSI Studio adımları arayüzden yapılır.
> **Veri:** Bu depoda hiçbir hasta/denek verisi yoktur ve olmamalıdır (bkz. [Gizlilik](#gizlilik)).

## Ne üretir?

Örnek önek: `s05` (kendi önekinizle değiştirin).

| # | Dosya | Nasıl oluşur |
|---|-------|--------------|
| 1 | `s05_autotrack_99bundles.tt.gz` | DSI Studio: *Recognize and Cluster* → *Tracts > Save All Tracts As* |
| 2 | `s05_autotrack_99bundles.tt.gz.txt` | DSI Studio, `.tt.gz` ile birlikte **otomatik** yazar (demet adları/indeksleri) |
| 3 | `s05_connectome_HCP-MMP_ntracts.mat` | DSI Studio: *Tracts > Connectivity matrix* → *Save matrix* |
| 4 | `s05_HCP-MMP_connectivity_for_graph.mat` | **Betik** (`graphmat`) — Visualize Graph'ın istediği `connectivity` adlı matrisi içerir |
| 5 | `s05_connectome_nodes_edges_2D.png` | **Betik** (`plot`) — 3 görünüm, top + kenar |
| 6 | `s05_connectome_nodes_edges_3D.png` | **Betik** (`plot`) |

Ek (isteğe bağlı): `s05_..._t2r.txt` (Tract-To-Region), `s05_node_metrics.csv` (betik `metrics`).

## Gereksinimler

- DSI Studio — bu rehber *Hou, 25 Temmuz 2026* sürümüyle yazıldı (Sun 2026.7.25 de önerilir). Resmî site: <https://dsi-studio.labsolver.org>. DSI Studio'yu **bu depo dağıtmaz**.
- HCP-MMP atlası DSI Studio ile gelir: `<dsi_studio>/atlas/human/HCP-MMP.nii.gz` ve `HCP-MMP.txt`.
- Python ≥ 3.10: `pip install -r requirements.txt` (numpy, scipy, nibabel, matplotlib)

## Tam yol (doğrulanmış)

Aşağıdaki sıra bu çalışmada uçtan uca denenmiştir (175.693 trakt → 99 demet → 360×360 matris).

1. **Dosyayı açın:** DSI Studio'da Step T3'te `…_s05.qsdr.fz`. *Step T3a*'da atlas `human`, *Step T3c*'de kalite "Low Quality (Fast)" kalabilir.
2. **Fiber Tracking** (*Step T3d*): tüm beyin traktografisi (`whole_brain`).
3. **Tracts Misc > Recognize and Cluster** → 99 isimli demet oluşur.
   ![](docs/images/02_recognize_cluster.jpg)
4. **Regions > Tract-To-Region Connectome (T2R)** → sonucu `_t2r.txt` olarak kaydedin (isteğe bağlı).
   ![](docs/images/03_regions_menu_t2r.jpg)
5. **Tracts > Save All Tracts As…** → `s05_autotrack_99bundles.tt.gz` (yanına `.tt.gz.txt` otomatik yazılır). Bu yedek, sonraki Merge adımından önce alınır.
   ![](docs/images/06_tracts_menusu.jpg)
6. **Tracts > Merge All** → tüm demetler tek satırda birleşir. *Konnektivite matrisi yalnızca seçili satırdaki traktlardan hesaplanır*; birleştirmezseniz matris birkaç yüz trakttan çıkar ve çok seyrek olur.
   ![](docs/images/05_merge_all_sonrasi.jpg)
7. **Tracts > Connectivity matrix:** *Parcellation Atlas* = **HCP-MMP** (listede yanlış atlas seçmek kolaydır — kontrol edin), *pass region*, *value: number of tracts* → **Recalculate** → **Save matrix** → `s05_connectome_HCP-MMP_ntracts.mat`.
   ![](docs/images/07_atlas_secimi.jpg)
   ![](docs/images/08_matris_hesaplandi.jpg)
8. **Betiği çalıştırın** (aşağıda) → graph `.mat` + 2B/3B PNG.
9. **Tracts > Visualize Graph…** → `s05_HCP-MMP_connectivity_for_graph.mat`. *Step T3c: Options*'ta **Region Rendering ✔, Tract Rendering ☐** yapın → kapak görüntüsü.
   ![](docs/images/09_visualize_graph_dosya.jpg)

### Neden 4. dosya (betik)?

Bu DSI Studio sürümünde *Save matrix* dosyası "Visualize Graph" için gereken `connectivity` adlı matrisi içermiyor ve şu hata çıkıyor: *"Cannot find a matrix named connectivity"*.
![](docs/images/10_hata_connectivity.jpg)
`graphmat` alt komutu `number of tracts r2r` matrisini `connectivity` adıyla yeniden yazar. Bu, DSI Studio'nun yazdığı MATLAB v4 biçimiyle uyumludur (gerçek `s05` verisinde elle üretilen dosya ile birebir aynı sonuç verdi).

## Hızlı yol (daha kısa, **henüz HCP-MMP'de doğrulanmadı**)

3–6. adımları atlayıp doğrudan `whole_brain` satırıyla 7–9'a geçmek mümkün olmalıdır; Brainnectome atlasıyla çalıştığı görülmüştü, **HCP-MMP ile denenmedi**. Bu yolda 1–2 numaralı dosyalar (99 demet) üretilmez. Deneyip sonucu bir *issue* ile bildirirseniz buraya işlenir.

## Betik kullanımı

```bash
pip install -r requirements.txt

# graph .mat + 2B + 3B PNG tek komutta
python scripts/connectome_tools.py all \
    --mat  C:/Users/ben/Desktop/s05_connectome_HCP-MMP_ntracts.mat \
    --atlas-dir "C:/dsi_studio_win/atlas/human" \
    --prefix s05

python scripts/connectome_tools.py inspect --mat s05_connectome_HCP-MMP_ntracts.mat   # içindeki matrisleri listele
python scripts/connectome_tools.py graphmat --mat X.mat --prefix s05                   # yalnız graph .mat
python scripts/connectome_tools.py plot  --mat X.mat --atlas-dir ... --prefix s05 --top-edges 400
python scripts/connectome_tools.py metrics --mat X.mat --atlas-dir ... --prefix s05    # düğüm metrikleri CSV
```

Çizim: düğüm = atlas bölgesinin ağırlık merkezi (MNI), boyut = güç (strength), turuncu = sol, mavi = sağ yarıküre; çizgi = en güçlü `--top-edges` bağlantı. Örnekler: [`examples/`](examples).

![2B örnek](examples/s05_connectome_nodes_edges_2D.png)

Testler: `pip install -r requirements-dev.txt && pytest -q`

## Sonra ne yapılır?

1. **Kalite kontrolü (önce bunu yapın).** `metrics` çıktısındaki `interhemispheric_fraction` (sol↔sağ bağlantı payı) ve `density` değerlerine bakın. Örnek veride sol-sağ pay yalnızca ≈%2,3 çıktı; corpus callosum'un tipik payına göre düşük görünüyor. Bu bir parametre/pipeline sorusu olabilir (ör. *pass* ve *end* farkı, uzunluk eşikleri, atlasın yalnız korteks olması) — kendi verinizde de kontrol edip yorumlamadan önce nedenini anlayın.
2. **Normalizasyon.** Ham "number of tracts" bölge hacmine, toplam trakt sayısına ve traktografi parametrelerine bağlıdır. Bireyler/gruplar arasında karşılaştırmadan önce normalize edin (ör. toplam trakta bölme, bölge boyutuna göre düzeltme) ya da DSI Studio'daki diğer ölçümleri (ör. *mean length*, QA/FA-ağırlıklı) kullanın.
3. **Graf metrikleri.** Derece/güç, kümeleme katsayısı, global/yerel verimlilik, modülerlik, hub'lar. Hazır kütüphaneler: [bctpy](https://github.com/aestrivex/bctpy), [networkx](https://networkx.org). Eşikleme (ör. en güçlü %10 veya yoğunluk-eşleştirilmiş) sonuçları değiştirir; birden fazla eşikte sağlamlığı gösterin.
4. **Demet bazlı analiz.** `.tt.gz` dosyasını DSI Studio'da açıp demet başına QA/FA/uzunluk istatistiklerini (Tracts > Statistics) alın; 99 demet adları `.tt.gz.txt` içindedir.
5. **Grup karşılaştırması.** Kenar bazlı testlerde çoklu karşılaştırma düzeltmesi (FDR) veya NBS (Network-Based Statistic) kullanın; yaş/cinsiyet/baş hareketi kovaryatlarını ekleyin.
6. **Yorum sınırları.** Traktografideki trakt sayısı akson sayısı değildir; yanlış-pozitif/negatif bağlantılar olabilir (özellikle kesişen lif bölgeleri ve uzun mesafeli yollar). Sonuçları "yapısal bağlantı kanıtı" olarak değil "traktografi tabanlı bağlantı tahmini" olarak raporlayın.

## Sorun giderme

[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md): tek satır seçiliyken matris, yanlış atlas, `connectivity` hatası, Region/Tract Rendering, ikinci DSI Studio penceresi/lisans, 246 ↔ 248 bölge hatası.

## Gizlilik

- `.fz`, `.tt.gz`, `.mat`, `.nii.gz` dosyaları `.gitignore` ile dışarıda tutulur. **Hasta/denek verisini asla commit etmeyin**; dosya adları (ör. tarih_yaş_AD-SOYAD içeren `.qsdr.fz` adları) ve ekran görüntülerindeki başlık çubukları kimlik içerebilir.
- Görsellerde başlık çubukları ve kişisel klasör listeleri kırpılmış/bulanıklaştırılmıştır; kendi görüntülerinizi eklerken de yapın.
- Bu depodaki örnek PNG'ler yalnızca bölge-bölge toplu sayıdan çizilmiş, kimlik taşımayan örneklerdir.

## Lisans ve atıflar

- Bu depodaki betikler ve metin: **MIT** ([LICENSE](LICENSE)).
- **DSI Studio** ayrı bir yazılımdır ve **CC BY-NC-SA 4.0** altındadır (ticari olmayan kullanım); bu depo dağıtmaz. Atıf: Yeh F.-C. (2025) doi:10.1038/s41592-025-02762-8.
- **HCP-MMP** atlası kendi lisans/kullanım koşullarına tabidir ve bu depoda dağıtılmaz. Atıf: Glasser et al. (2016) *Nature* 536:171–178.

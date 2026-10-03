# Sorun giderme / Troubleshooting

| Belirti / Symptom | Neden / Cause | Çözüm / Fix |
|---|---|---|
| Matris çok seyrek, toplam trakt birkaç yüz | Konnektivite matrisi yalnızca **seçili tract satırından** hesaplanır / only the selected row is used | `Save All Tracts As` ile yedek alın, **Tracts > Merge All**, matrisi yeniden **Recalculate** |
| Matris 360×360 değil | Yanlış atlas seçildi (liste kayar, ör. Brodmann) / wrong atlas | Listeyi tekrar açıp seçili adı okuyun, **HCP-MMP**'yi seçin, Recalculate |
| *Cannot find a matrix named connectivity* | Bu sürümde *Save matrix* dosyasında `connectivity` adlı matris yok | `python scripts/connectome_tools.py graphmat --mat X.mat --prefix s05` ile üretilen dosyayı Visualize Graph'a verin |
| Visualize Graph "bir şey olmuyor" | Graph sessizce yüklenir; görünürlük ayarlarına bağlı | *Step T3c*: **Region Rendering ✔**, **Tract Rendering ☐** (isteğe bağlı Slice Rendering ✔) |
| `connectome_tools.py plot`: "Atlas N bölgeli, matris M×M" | Matris farklı atlastan | DSI Studio'da matrisi **HCP-MMP** ile yeniden hesaplayın; `--atlas`/`--atlas-dir` doğru mu? |
| `Atlas dosyaları yok` | `--atlas-dir` yanlış | `<dsi_studio>/atlas/human` klasörünü verin (`HCP-MMP.nii.gz` + `.txt`) |
| `MATLAB v4 başlığı tanımlanamadı` | Dosya DSI Studio `.mat`'i değil veya bozuk | `inspect` ile kontrol edin; dosyayı yeniden kaydedin |
| DSI Studio ikinci kez açılıp lisans penceresi çıkıyor | Uygulama yeni bir örnek başlattı | Çalışan pencereyi kullanın; yeni örnekte lisans koşullarını okuyup bilinçli karar verin |
| Brainnectome'da 246 ↔ 248 bölge uyuşmazlığı | Atlas/sürüm farkı | Sun 2026.7.25 sürümünü deneyin; bu rehber HCP-MMP (360) için yazılmıştır |
| Sol-sağ bağlantı payı çok düşük | İzler kısa/parçalı, karşı yarıküre korteksine ulaşmıyor / streamlines too short | `connectome_tools.py qc --tt ...`; README → "Sonra ne yapılır?" madde 1 |

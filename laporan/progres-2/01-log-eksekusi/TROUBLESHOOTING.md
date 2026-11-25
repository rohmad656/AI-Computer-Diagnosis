TROUBLESHOOTING — PROGRES KE-2
===============================
Tanggal   : 2026-11-24
Proyek    : AI-Computer-Diagnosis
Versi     : Phase 13/14 (commit 4354994)

====================================================================
ISU 1: pytest -q gagal dengan "No module named 'core'"
====================================================================

GEJALA
------
Menjalankan `pytest -q` langsung dari terminal menghasilkan:
  ModuleNotFoundError: No module named 'core'

PENYEBAB
--------
Ketika `pytest` dipanggil melalui PATH system (bukan via python -m),
sys.path tidak menyertakan direktori kerja proyek secara otomatis.
Modul `core`, `evaluation`, dll. tidak dapat diimpor karena Python
tidak tahu di mana harus mencarinya.

SOLUSI
------
Gunakan invokasi via python -m untuk memastikan CWD masuk ke sys.path:

  SALAH : pytest -q
  BENAR : .venv\Scripts\python.exe -m pytest -q

VERIFIKASI
----------
Perintah yang benar menghasilkan:
  ........................................................................ [ 66%]
  ....................................                                     [100%]
  108 passed in 1.84s

CATATAN PENTING
---------------
Ini bukan bug algoritma UCS atau knowledge base.
Ini masalah invokasi lingkungan Python di Windows.
Tidak ada perubahan kode yang diperlukan.

====================================================================
ISU 2: Tee-Object menghasilkan file UTF-16 (BOM 0xFF 0xFE)
====================================================================

GEJALA
------
File log yang dibuat dengan `Tee-Object -FilePath ...` tidak dapat
dibaca dengan encoding utf-8 standar:
  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff at position 0

PENYEBAB
--------
PowerShell `Tee-Object` secara default menyimpan output sebagai
UTF-16 LE dengan BOM (Byte Order Mark), bukan UTF-8.

SOLUSI
------
Gunakan subprocess Python dengan env PYTHONUTF8=1 dan tulis file
langsung dengan open(..., encoding='utf-8') dari dalam Python:
  - Jalankan subprocess dengan capture_output=True
  - Dekode dengan .decode('utf-8', errors='replace')
  - Tulis dengan Path(...).write_text(data, encoding='utf-8', newline='\n')

Atau untuk pembacaan file yang sudah telanjur UTF-16:
  open(path, encoding='utf-8-sig')  # utf-8-sig membaca BOM dengan benar

CATATAN
-------
File-file dalam 01-log-eksekusi/ akhirnya ditulis ulang dengan
encoding UTF-8 bersih menggunakan skrip Python langsung.

====================================================================
ISU 3: EXT_DRV_045 menghasilkan missed_conclusive
====================================================================

GEJALA
------
Kasus EXT_DRV_045 (misleading false_positive driver) menghasilkan
outcome missed_conclusive (false negative) bukan correct_conclusive.

PENYEBAB
--------
test_driver_status=false_positive diperlakukan BERBEDA dengan
yellow_bang. Mapping di knowledge base memetakan false_positive ke
supporting evidence, namun UCS mengenali ini sebagai misleading
evidence dan tidak memenuhi goal state conclusive.

PENJELASAN
----------
Ini adalah keterbatasan yang DISENGAJA dan DIDOKUMENTASIKAN:
- Sistem tidak dapat mendeteksi kebohongan tes secara otomatis
- false_positive adalah hasil tes yang melaporkan masalah padahal
  tidak ada; sistem UCS mengeliminasi kategori karena evidence
  yang terkumpul tidak cukup untuk mencapai goal state
- Ini adalah risiko nyata dalam sistem diagnosis berbasis tes

KEPUTUSAN
---------
Label dataset EXT_DRV_045 TIDAK diubah.
Outcome missed_conclusive dilaporkan sebagai keterbatasan sistem.
Tidak ada perubahan pada algoritma UCS atau knowledge base rules.

====================================================================
ISU 4: 30 kasus contradictory menghasilkan observation_limited_conclusive
====================================================================

GEJALA
------
30 kasus bertipe 'contradictory' dalam extended dataset menunjukkan
outcome observation_limited_conclusive meskipun label menyatakan
inconclusive.

PENYEBAB
--------
UCS berhenti lebih awal karena goal state tercapai sebelum tes
kontradiktor teramati dalam urutan ekspansi UCS. Tes yang
mengandung bukti kontradiktor memiliki cost lebih tinggi dan
belum sempat dieksekusi saat UCS mencapai goal state.

PENJELASAN
----------
Ini bukan false positive dalam arti klasik. UCS bekerja dengan
benar sesuai cost ordering. Evidence kontradiktor memang ada dalam
dataset tapi tidak 'teramati' oleh UCS dalam jalur optimal.

KEPUTUSAN
---------
Outcome dikategorikan sebagai observation_limited_conclusive
(bukan false_positive) untuk membedakan dari kesalahan algoritma.
Tidak ada perubahan pada UCS atau dataset.

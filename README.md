# Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial

Kelompok 31 — Claudia
- Keisha Sakura Widjaja 18224002
- Claudia Melati Krid 18224032
- Zahra Zahidah Putri Ruchwijaya 18224058

Program ini mencari susunan kendaraan pada geladak kapal untuk memaksimalkan total Shipping Fee. Kendaraan yang dimuat harus berada dalam batas kapal, tidak saling bertumpuk, dan tidak melebihi kapasitas angkut.

Algoritma yang diimplementasikan:
- Hill-Climbing Steepest Ascent
- Hill-Climbing with Sideways Move
- Stochastic Hill-Climbing
- Random Restart Hill-Climbing
- Simulated Annealing
- Genetic Algorithm

Program memungkinkan untuk mengatur parameter dan menampilkan hasil, grafik pencarian, serta ilustrasi susunan awal dan akhir setiap run.

## Struktur Repository

```text
IF3070_G31_Claudia/
├── src/
│   ├── algoritma/       # Implementasi algoritma
│   ├── data.json       # Data kapal dan kendaraan
│   ├── evaluation.py   # Evaluasi, representasi state, dan pembangkitan neighbor
│   └── main.py         # GUI dan pelaksanaan eksperimen
├── docs/               # Dokumen laporan dan analisis
├── output/             # Hasil eksperimen
└── README.md
```

## Setup

Gunakan Python 3 dengan Tkinter tersedia. Program dikembangkan menggunakan Python 3.12. Matplotlib digunakan untuk membuat grafik dan gambar hasil eksperimen.

1. Clone repository dan masuk ke folder proyek:

   ```bash
   git clone https://github.com/keisha-sakura/IF3070_G31_Claudia.git
   cd IF3070_G31_Claudia
   ```

2. Instal dependency:

   ```bash
   python -m pip install matplotlib
   ```

## Menjalankan Program

Jalankan perintah berikut dari folder utama repository:

```bash
python src/main.py
```

1. Klik **Load Data** untuk memuat `src/data.json`. Lokasi file dapat diubah melalui kolom input.
2. Pilih algoritma dan isi parameternya.
3. Khusus Genetic Algorithm, isi tiga variasi generasi dan tiga variasi populasi, dipisahkan koma.
4. Klik **Run Experiment**. Algoritma selain GA dijalankan tiga kali. GA dijalankan 18 kali: tiga variasi generasi dengan populasi tetap dan tiga variasi populasi dengan generasi tetap, masing-masing diulang tiga kali.
5. Lihat hasil di tab **Hasil**, grafik di tab **Grafik**, dan ilustrasi susunan kendaraan di bagian bawah. Gunakan scrollbar untuk melihat seluruh run.

Hasil otomatis disimpan di `output/<nama_algoritma>/eksperimen_<tanggal_waktu>/`. Untuk GA, hasil dipisahkan lagi berdasarkan kelompok eksperimen dan konfigurasi populasi serta generasi. Setiap folder run berisi `hasil.json`, `console.txt`, `grafik.png`, dan `state.png` jika proses berhasil.

Shipping Fee ditampilkan dalam juta rupiah. Objective `-1` menandakan susunan melanggar constraints, bukan pendapatan negatif.

## Pembagian Tugas

| Anggota Kelompok | Tugas |
| --- | --- |
| Keisha Sakura Widjaja<br>18224002 | 1. Implementasi Hill-Climbing with Sideways Move.<br>2. Implementasi Simulated Annealing.<br>3. Penulisan deskripsi masalah pada laporan.<br>4. Inisialisasi main program.<br>5. Pembuatan main GUI program.<br>6. Pembahasan implementasi Sideways Move.<br>7. Pembahasan implementasi Simulated Annealing.<br>8. Eksperimen dan pembahasan hasil Sideways Move.<br>9. Eksperimen dan pembahasan hasil Simulated Annealing.<br>10. Analisis pertanyaan 2, 3, dan 4.<br>11. Penulisan kesimpulan dan saran.<br>12. Pengerjaan Specification Traceability. |
| Claudia Melati Krid<br>18224032 | 1. Implementasi Random Restart Hill-Climbing.<br>2. Implementasi Genetic Algorithm.<br>3. Pembuatan fungsi initial state dengan First Fit Algorithm.<br>4. Analisis pertanyaan 5 dan 6.<br>5. Pembahasan implementasi Random Restart.<br>6. Pembahasan implementasi Genetic Algorithm.<br>7. Eksperimen dan pembahasan hasil Random Restart.<br>8. Eksperimen dan pembahasan hasil Genetic Algorithm.<br>9. Pengerjaan main GUI.<br>10. Perapian dokumen. |
| Zahra Zahidah Putri Ruchwijaya<br>18224058 | 1. Implementasi Steepest Ascent Hill-Climbing.<br>2. Implementasi Stochastic Hill-Climbing.<br>3. Implementasi Random Restart Hill-Climbing.<br>4. Pembuatan objective function.<br>5. Pembuatan fungsi evaluasi.<br>6. Penulisan laporan untuk bagian implementasi yang dikerjakan.<br>7. Analisis pertanyaan 1.<br>8. Penulisan pembahasan pemilihan fungsi initial state.<br>9. Pembuatan README. |

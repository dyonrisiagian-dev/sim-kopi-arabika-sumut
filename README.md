# SIM-KOPI ARABIKA SUMUT

Aplikasi dashboard Streamlit untuk menampilkan data dari tabel `kopi_arabika_pusat_kecamatan` pada database pusat Neon PostgreSQL (`db_pusat_sumut`).

## File utama

- `app.py`: halaman dashboard, tabel data kabupaten/kecamatan, filter, grafik, dan unduh CSV.
- `requirements.txt`: dependensi Python.
- `.streamlit/config.toml`: konfigurasi tampilan Streamlit.
- `.gitignore`: mencegah file rahasia dan file sementara ikut diunggah.

## Menjalankan di komputer sendiri

1. Install Python 3.10 atau lebih baru.
2. Buka terminal di folder proyek.
3. Buat virtual environment (opsional tetapi disarankan): `python -m venv .venv`.
4. Aktifkan virtual environment.
5. Install dependensi: `pip install -r requirements.txt`.
6. Buat file `.streamlit/secrets.toml` dan isi:

```toml
NEON_CONNECTION_STRING = "postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require"
```

Ganti contoh di atas dengan connection string asli dari Neon. Jangan unggah `secrets.toml` ke GitHub.

7. Jalankan: `streamlit run app.py`.

## Deploy ke Streamlit Community Cloud

1. Upload isi folder proyek ini ke sebuah repository GitHub.
2. Buka https://share.streamlit.io dan masuk dengan GitHub.
3. Pilih **Create app**, pilih repository, branch, dan file `app.py`.
4. Di **Advanced settings → Secrets**, masukkan:

```toml
NEON_CONNECTION_STRING = "postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require"
```

5. Klik **Deploy**.

Pastikan connection string mengarah ke database `db_pusat_sumut`, bukan salah satu database wilayah.

## Struktur tabel yang dibaca

Aplikasi membaca tabel `kopi_arabika_pusat_kecamatan` dengan kolom `kode_data`, `kabupaten`, `kecamatan`, `level_data`, `komoditas`, `tahun`, `luas_tbm_ha`, `luas_tm_ha`, `luas_ttm_ha`, `luas_total_ha`, `produksi_ton`, `sumber_data`, `wilayah_sumber`, `updated_at`, dan `disinkronkan_pada`.

Aplikasi hanya membaca data. Data rekap `KABUPATEN` dan rincian `KECAMATAN` dipisahkan agar angka dari tingkat wilayah dan tahun berbeda tidak dijumlahkan sebagai satu total.

import os

import pandas as pd
import psycopg2
import streamlit as st


# ------------------------------------------------------------
# KONFIGURASI HALAMAN
# ------------------------------------------------------------
st.set_page_config(
    page_title="SIM-KOPI ARABIKA SUMUT",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

TABLE_NAME = "kopi_arabika_pusat_kecamatan"
COLUMNS = [
    "kode_data",
    "kabupaten",
    "kecamatan",
    "level_data",
    "komoditas",
    "tahun",
    "luas_tbm_ha",
    "luas_tm_ha",
    "luas_ttm_ha",
    "luas_total_ha",
    "produksi_ton",
    "sumber_data",
    "wilayah_sumber",
    "updated_at",
    "disinkronkan_pada",
]


def get_database_url() -> str:
    """Ambil connection string dari Streamlit Secrets atau environment variable."""
    try:
        secret_value = st.secrets.get("NEON_CONNECTION_STRING", "")
    except (FileNotFoundError, AttributeError):
        secret_value = ""

    connection_string = secret_value or os.getenv("NEON_CONNECTION_STRING", "")
    if not connection_string:
        raise RuntimeError(
            "Koneksi database belum diatur. Tambahkan NEON_CONNECTION_STRING "
            "di Streamlit Cloud → App settings → Secrets."
        )
    return connection_string


@st.cache_data(ttl=300, show_spinner="Mengambil data dari database pusat...")
def load_data() -> pd.DataFrame:
    """Membaca data dari database pusat Neon. Data website bersifat read-only."""
    connection_string = get_database_url()
    sql = f"""
        SELECT
            kode_data,
            kabupaten,
            kecamatan,
            level_data,
            komoditas,
            tahun,
            luas_tbm_ha,
            luas_tm_ha,
            luas_ttm_ha,
            luas_total_ha,
            produksi_ton,
            sumber_data,
            wilayah_sumber,
            updated_at,
            disinkronkan_pada
        FROM {TABLE_NAME}
        ORDER BY kabupaten, level_data, tahun, kecamatan
    """

    conn = None
    try:
        conn = psycopg2.connect(connection_string, connect_timeout=15)
        df = pd.read_sql_query(sql, conn)
    finally:
        if conn is not None:
            conn.close()

    # Menyeragamkan kolom teks agar filter tidak gagal karena spasi/huruf besar-kecil.
    for column in ["kabupaten", "kecamatan", "level_data", "komoditas"]:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()

    # Kolom angka dapat berisi NULL dari sumber data; biarkan sebagai nilai kosong.
    numeric_columns = [
        "tahun",
        "luas_tbm_ha",
        "luas_tm_ha",
        "luas_ttm_ha",
        "luas_total_ha",
        "produksi_ton",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def format_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def show_data_table(data: pd.DataFrame, key_prefix: str):
    if data.empty:
        st.info("Tidak ada data yang sesuai dengan filter.")
        return

    display_columns = [
        "kabupaten",
        "kecamatan",
        "level_data",
        "tahun",
        "luas_total_ha",
        "luas_tm_ha",
        "produksi_ton",
        "sumber_data",
    ]
    display_columns = [column for column in display_columns if column in data.columns]
    renamed = {
        "kabupaten": "Kabupaten",
        "kecamatan": "Kecamatan",
        "level_data": "Tingkat Data",
        "tahun": "Tahun",
        "luas_total_ha": "Luas Total (ha)",
        "luas_tm_ha": "Luas TM (ha)",
        "produksi_ton": "Produksi (ton)",
        "sumber_data": "Sumber Data",
    }
    st.dataframe(
        data[display_columns].rename(columns=renamed),
        use_container_width=True,
        hide_index=True,
    )
    csv_bytes = data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Unduh data yang ditampilkan (CSV)",
        data=csv_bytes,
        file_name=f"{key_prefix}_sim_kopi_arabika_sumut.csv",
        mime="text/csv",
        key=f"download_{key_prefix}",
    )


# ------------------------------------------------------------
# SIDEBAR DAN PEMUATAN DATA
# ------------------------------------------------------------
st.sidebar.title("☕ SIM-KOPI ARABIKA SUMUT")
st.sidebar.caption("Sistem Informasi Data Kopi Arabika Sumatera Utara")
menu = st.sidebar.radio(
    "Menu Utama",
    ["Dashboard", "Data Kabupaten", "Data Kecamatan", "Tentang Sistem"],
)

if st.sidebar.button("↻ Muat ulang data", use_container_width=True):
    load_data.clear()
    st.rerun()

st.sidebar.caption("Pembaruan otomatis cache: setiap 5 menit")

st.title("☕ Sistem Informasi Kopi Arabika Sumatera Utara")
st.caption("Dashboard basis data produksi dan luas tanaman kopi Arabika dari lima kabupaten.")

try:
    df = load_data()
except Exception as error:
    st.error("Website belum berhasil mengambil data dari Neon PostgreSQL.")
    st.warning(str(error))
    st.markdown(
        "**Periksa hal berikut:**\n"
        "1. Secret `NEON_CONNECTION_STRING` sudah diisi di pengaturan Streamlit.\n"
        "2. Connection string mengarah ke database `db_pusat_sumut`.\n"
        "3. Alamat, username, password, dan parameter SSL pada connection string benar.\n"
        "4. Tabel `kopi_arabika_pusat_kecamatan` sudah berisi data."
    )
    st.stop()

if df.empty:
    st.warning("Database pusat berhasil dihubungkan, tetapi tabel belum memiliki data.")
    st.stop()

# Pisahkan rekap kabupaten dan data kecamatan agar kedua tingkatan tidak tercampur.
level_normalized = df["level_data"].astype("string").str.upper()
df_kab = df[level_normalized == "KABUPATEN"].copy()
df_kec = df[level_normalized == "KECAMATAN"].copy()


# ------------------------------------------------------------
# HALAMAN DASHBOARD
# ------------------------------------------------------------
if menu == "Dashboard":
    st.subheader("Ringkasan Data")
    st.info(
        "Rekap kabupaten dan rincian kecamatan ditampilkan terpisah. "
        "Jangan menjumlahkan keduanya karena tingkat wilayah dan tahun sumbernya berbeda."
    )

    total_kabupaten = df_kab["kabupaten"].nunique() if not df_kab.empty else 0
    total_kecamatan = len(df_kec)
    total_produksi_kab = df_kab["produksi_ton"].sum(min_count=1) if not df_kab.empty else 0
    total_luas_kab = df_kab["luas_total_ha"].sum(min_count=1) if not df_kab.empty else 0
    total_tm_kab = df_kab["luas_tm_ha"].sum(min_count=1) if not df_kab.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Kabupaten dalam rekap", format_number(total_kabupaten))
    col2.metric("Catatan kecamatan", format_number(total_kecamatan))
    col3.metric("Produksi rekap kabupaten", f"{format_number(total_produksi_kab)} ton")
    col4.metric("Luas tanaman total", f"{format_number(total_luas_kab)} ha")

    col5, col6 = st.columns(2)
    col5.metric("Luas tanaman menghasilkan (TM)", f"{format_number(total_tm_kab)} ha")
    col6.metric("Total baris di database pusat", format_number(len(df)))

    st.divider()
    st.subheader("Produksi Kopi Arabika Menurut Kabupaten")
    if df_kab.empty:
        st.info("Belum ada baris dengan level_data = KABUPATEN.")
    else:
        chart_df = df_kab.dropna(subset=["produksi_ton"]).sort_values("produksi_ton", ascending=False)
        if chart_df.empty:
            st.info("Nilai produksi kabupaten belum tersedia untuk dibuatkan grafik.")
        else:
            st.bar_chart(chart_df, x="kabupaten", y="produksi_ton", height=380)

        st.subheader("Rekap Kabupaten")
        show_data_table(df_kab, "rekap_kabupaten")

    st.caption(
        "Angka ringkasan pada bagian ini dihitung dari baris berlevel KABUPATEN saja. "
        "Rincian kecamatan tidak ditambahkan ke total kabupaten."
    )


# ------------------------------------------------------------
# HALAMAN DATA KABUPATEN
# ------------------------------------------------------------
elif menu == "Data Kabupaten":
    st.subheader("Data Rekap Kabupaten")
    st.write("Menampilkan rekap luas tanaman dan produksi kopi Arabika pada tingkat kabupaten.")

    if df_kab.empty:
        st.warning("Belum terdapat data rekap kabupaten.")
    else:
        years = sorted(df_kab["tahun"].dropna().astype(int).unique().tolist())
        selected_year = st.selectbox("Pilih tahun data", ["Semua tahun"] + years)
        filtered = df_kab.copy()
        if selected_year != "Semua tahun":
            filtered = filtered[filtered["tahun"] == selected_year]

        districts = sorted(filtered["kabupaten"].dropna().unique().tolist())
        selected_districts = st.multiselect(
            "Pilih kabupaten",
            options=districts,
            default=districts,
        )
        filtered = filtered[filtered["kabupaten"].isin(selected_districts)]

        st.write(f"Jumlah baris yang ditampilkan: **{len(filtered)}**")
        show_data_table(filtered, "data_kabupaten")

        if not filtered.empty and filtered["produksi_ton"].notna().any():
            st.subheader("Grafik Produksi Kabupaten")
            chart_df = filtered.dropna(subset=["produksi_ton"]).sort_values("produksi_ton", ascending=False)
            st.bar_chart(chart_df, x="kabupaten", y="produksi_ton", height=350)


# ------------------------------------------------------------
# HALAMAN DATA KECAMATAN
# ------------------------------------------------------------
elif menu == "Data Kecamatan":
    st.subheader("Data Rincian Kecamatan")
    st.write("Gunakan filter kabupaten dan tahun untuk melihat rincian per kecamatan.")
    st.warning(
        "Tahun data kecamatan mengikuti tahun publikasi/sumber yang tersedia. "
        "Karena tahunnya tidak seluruhnya sama, perhatikan kolom Tahun dan Sumber Data."
    )

    if df_kec.empty:
        st.warning("Belum terdapat data kecamatan.")
    else:
        districts = sorted(df_kec["kabupaten"].dropna().unique().tolist())
        selected_district = st.selectbox("Pilih kabupaten", ["Semua kabupaten"] + districts)
        filtered = df_kec.copy()
        if selected_district != "Semua kabupaten":
            filtered = filtered[filtered["kabupaten"] == selected_district]

        years = sorted(filtered["tahun"].dropna().astype(int).unique().tolist())
        selected_year = st.selectbox("Pilih tahun", ["Semua tahun"] + years)
        if selected_year != "Semua tahun":
            filtered = filtered[filtered["tahun"] == selected_year]

        st.write(f"Jumlah catatan sesuai filter: **{len(filtered)}**")
        show_data_table(filtered, "data_kecamatan")

        chart_df = filtered.dropna(subset=["produksi_ton", "kecamatan"])
        if not chart_df.empty:
            st.subheader("Produksi Menurut Kecamatan")
            chart_df = chart_df.sort_values("produksi_ton", ascending=False)
            st.bar_chart(chart_df, x="kecamatan", y="produksi_ton", height=380)


# ------------------------------------------------------------
# HALAMAN TENTANG SISTEM
# ------------------------------------------------------------
else:
    st.subheader("Tentang SIM-KOPI ARABIKA SUMUT")
    st.markdown(
        """
        **SIM-KOPI ARABIKA SUMUT** merupakan prototipe sistem informasi untuk
        menampilkan data luas tanaman dan produksi kopi Arabika dari lima kabupaten
        di Provinsi Sumatera Utara.

        **Sumber data dalam basis data:**
        - Rekap kabupaten: data BPS tahun 2023 sebagaimana dicatat dalam panduan proyek.
        - Rincian kecamatan: data sesuai tahun dan publikasi/sumber yang tersedia untuk masing-masing kabupaten.

        **Alur pengolahan data:**
        1. Data wilayah disimpan dalam database masing-masing di Neon PostgreSQL.
        2. Google Colab mengambil data wilayah dan menyinkronkannya ke database pusat.
        3. Website Streamlit membaca data dari tabel `kopi_arabika_pusat_kecamatan` pada `db_pusat_sumut`.

        **Catatan penggunaan:** website ini hanya membaca dan menampilkan data. Perubahan data
        dilakukan melalui proses pengelolaan database, bukan dari halaman website.
        """
    )
    st.subheader("Informasi Database")
    st.write(f"Nama tabel: `{TABLE_NAME}`")
    st.write(f"Jumlah seluruh baris yang berhasil dibaca: **{len(df)}**")
    st.write(f"Baris rekap kabupaten: **{len(df_kab)}**")
    st.write(f"Baris rincian kecamatan: **{len(df_kec)}**")

st.sidebar.divider()
st.sidebar.caption("SIM-KOPI ARABIKA SUMUT | Proyek Basis Data Agribisnis")

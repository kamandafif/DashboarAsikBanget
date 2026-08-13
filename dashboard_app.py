"""
dashboard_app.py
-----------------
Dashboard Interaktif Terintegrasi untuk Manajemen Efisiensi Energi
dan Mobilitas Cerdas pada Lingkungan Industri Berkelanjutan.

Jalankan dengan:
    streamlit run dashboard_app.py

Membutuhkan generate_data.py pada folder yang sama. Data dasar bersifat
SINTETIS (simulasi), dibuat otomatis saat pertama kali dijalankan jika
file "data_pabrik_simulasi.csv" belum ada.

Tiga sumber data dipisah secara permanen (masing-masing file CSV sendiri,
tetap tersimpan walau dashboard ditutup & dibuka kembali):
    1) data_pabrik_simulasi.csv     -> data sintetis (tidak pernah ditimpa edit)
    2) data_pabrik_unggahan.csv     -> salinan file terakhir yang diunggah pengguna
    3) data_pabrik_edit_manual.csv  -> hasil edit manual pengguna

Dependensi tambahan (opsional, untuk unduh ringkasan PDF):
    pip install fpdf2
"""

import io
import os
import hashlib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from generate_data import generate_dataset, JAM_KERJA_MULAI, JAM_KERJA_SELESAI

# ============================================================
# KONFIGURASI HALAMAN & GAYA TAMPILAN
# ============================================================
st.set_page_config(
    page_title="DSS Energi & Mobilitas Cerdas",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# PALET WARNA UTAMA DASHBOARD (Biru & Putih)
# ------------------------------------------------------------
WARNA_BIRU_CERAH = "#1A73E8"
WARNA_BIRU_TUA = "#0F3D91"
WARNA_PUTIH = "#FFFFFF"
WARNA_BIRU_MUDA = "#BBD4FF"
WARNA_MERAH = "#D64550"
WARNA_HIJAU = "#1E8E5A"

st.markdown(f"""
<style>
    .main {{ background-color: {WARNA_PUTIH}; }}
    section[data-testid="stSidebar"] {{ background-color: {WARNA_BIRU_TUA}; }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stRadio div {{
        color: {WARNA_PUTIH} !important;
    }}
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
        background-color: {WARNA_PUTIH} !important;
        color: {WARNA_BIRU_TUA} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary *,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary span[role="img"] {{
        color: {WARNA_BIRU_TUA} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] {{
        background-color: {WARNA_PUTIH} !important;
        border-radius: 8px;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] * {{
        color: {WARNA_BIRU_TUA} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stDownloadButton button,
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stDownloadButton button * {{
        color: {WARNA_PUTIH} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background-color: {WARNA_PUTIH} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {{
        color: {WARNA_BIRU_TUA} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{
        background-color: {WARNA_BIRU_CERAH} !important;
        border: none !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {{
        color: {WARNA_PUTIH} !important;
    }}
    section[data-testid="stSidebar"] .stDownloadButton button,
    section[data-testid="stSidebar"] .stButton button {{
        background-color: {WARNA_BIRU_CERAH} !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    section[data-testid="stSidebar"] .stDownloadButton button *,
    section[data-testid="stSidebar"] .stButton button *,
    section[data-testid="stSidebar"] .stDownloadButton button p,
    section[data-testid="stSidebar"] .stButton button p {{
        color: {WARNA_PUTIH} !important;
    }}
    div[data-testid="stMetric"] {{
        background-color: {WARNA_PUTIH};
        border: 1px solid {WARNA_BIRU_MUDA};
        border-top: 4px solid {WARNA_BIRU_CERAH};
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(15,61,145,0.08);
    }}
    div[data-testid="stMetricLabel"] {{ font-weight: 600; color: {WARNA_BIRU_TUA}; }}
    div[data-testid="stMetricValue"] {{ color: {WARNA_BIRU_CERAH}; }}
    h1, h2, h3 {{ color: {WARNA_BIRU_TUA}; }}
    .app-subtitle {{ color: #5878B0; font-size: 0.95rem; }}
    .block-note {{
        background-color: {WARNA_BIRU_MUDA}; border-left: 4px solid {WARNA_BIRU_CERAH};
        padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: {WARNA_BIRU_TUA};
        margin-bottom: 8px;
    }}
    .block-analisis {{
        background-color: #F4F8FF; border-left: 4px solid {WARNA_BIRU_TUA};
        padding: 12px 16px; border-radius: 6px; font-size: 0.92rem; color: #16305C;
        margin-top: 6px;
    }}
    div[data-testid="stDataFrame"] {{ border: 1px solid {WARNA_BIRU_MUDA}; border-radius: 8px; }}
    .stButton > button, .stDownloadButton > button {{
        background-color: {WARNA_BIRU_CERAH}; color: {WARNA_PUTIH}; border: none; border-radius: 8px;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background-color: {WARNA_BIRU_TUA}; color: {WARNA_PUTIH};
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# KONSTANTA
# ============================================================
KOLOM_WAJIB = [
    "Timestamp", "Daya_Mesin_kW", "Solar_Power_kW", "Emisi_CO2_kg",
    "AGV_01_SoC", "AGV_02_SoC", "AGV_03_SoC",
    "AGV_01_Charging", "AGV_02_Charging", "AGV_03_Charging",
    "Status_Charging_AGV", "Production_Output_Units",
]
DAFTAR_AGV = ["AGV_01", "AGV_02", "AGV_03"]

# Nama file penyimpanan permanen per sumber data (SENGAJA dipisah)
FILE_SIMULASI = "data_pabrik_simulasi.csv"
FILE_UNGGAHAN = "data_pabrik_unggahan.csv"
FILE_EDIT_MANUAL = "data_pabrik_edit_manual.csv"

# Judul sumber data (dipakai di sidebar)
SUMBER_SIMULASI = "Data Simulasi (Sintetis)"
SUMBER_UNGGAH = "Unggah File Sendiri"
SUMBER_EDIT = "Edit Manual di Tabel"

# Judul konteks operasional (dipakai sebagai filter tambahan di seluruh modul)
KONTEKS_24_7 = "Keseluruhan (24/7)"
KONTEKS_JAM_KERJA = f"Jam Kerja Operasional ({JAM_KERJA_MULAI:02d}:00 - {JAM_KERJA_SELESAI:02d}:00)"
KONTEKS_OFF_PEAK = "Luar Jam Kerja / Off-Peak"

# Label kolom yang lebih mudah dibaca manusia (khusus TAMPILAN tabel & unduhan,
# nama kolom asli di dalam data tetap dipakai untuk perhitungan agar stabil)
LABEL_KOLOM = {
    "Daya_Mesin_kW": "Beban Mesin (kW)",
    "Solar_Power_kW": "Daya Surya (kW)",
    "Emisi_CO2_kg": "Emisi CO2 (kg)",
    "AGV_01_SoC": "AGV 01 - Baterai (%)",
    "AGV_02_SoC": "AGV 02 - Baterai (%)",
    "AGV_03_SoC": "AGV 03 - Baterai (%)",
    "AGV_01_Charging": "AGV 01 - Isi Daya",
    "AGV_02_Charging": "AGV 02 - Isi Daya",
    "AGV_03_Charging": "AGV 03 - Isi Daya",
    "Status_Charging_AGV": "Ada AGV Mengisi Daya",
    "Production_Output_Units": "Output Produksi (unit)",
}
LABEL_KOLOM_BALIK = {v: k for k, v in LABEL_KOLOM.items()}

# Nama modul (ditulis dengan istilah yang lebih mudah dipahami)
MODUL_RINGKASAN = "Ringkasan Kinerja (Overview)"
MODUL_ENERGI = "Energi & Jejak Emisi"
MODUL_ARMADA = "Armada AGV/EV"
MODUL_REKOMENDASI = "Rekomendasi Cerdas (Smart Recommendation)"
MODUL_SIMULASI = "Simulasi Skenario Efisiensi"


# ============================================================
# FUNGSI BANTUAN: MUAT DATA, VALIDASI, TEMPLATE, PERHITUNGAN
# ============================================================
@st.cache_data
def muat_data_simulasi():
    """Memuat dataset SINTETIS dari CSV lokal; membuat data baru bila belum ada."""
    try:
        df = pd.read_csv(FILE_SIMULASI)
    except FileNotFoundError:
        df = generate_dataset()
        df.to_csv(FILE_SIMULASI, index=False)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df


def muat_csv_persisten(path):
    """Memuat file CSV persisten (unggahan / edit manual) jika ada di disk."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df


def info_checksum_csv(path, label):
    """Menghitung checksum & ukuran file CSV untuk verifikasi versi data yang dipakai."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        isi = f.read()
    return (
        f"🧾 {label}: `{hashlib.md5(isi).hexdigest()[:10]}` · {round(len(isi)/1024, 1)} KB · "
        f"diubah {pd.Timestamp(os.path.getmtime(path), unit='s'):%Y-%m-%d %H:%M}"
    )


def validasi_kolom(df):
    """Memastikan file unggahan memiliki seluruh kolom yang dibutuhkan dashboard."""
    return [k for k in KOLOM_WAJIB if k not in df.columns]


def buat_template_excel():
    """Menyusun file Excel kosong (1 baris contoh) sebagai template input manual."""
    contoh = pd.DataFrame([{
        "Timestamp": "2026-08-01 08:00",
        "Daya_Mesin_kW": 70.0,
        "Solar_Power_kW": 15.0,
        "Emisi_CO2_kg": 9.5,
        "AGV_01_SoC": 85.0, "AGV_02_SoC": 80.0, "AGV_03_SoC": 90.0,
        "AGV_01_Charging": False, "AGV_02_Charging": False, "AGV_03_Charging": False,
        "Status_Charging_AGV": False,
        "Production_Output_Units": 12,
    }])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        contoh.to_excel(writer, index=False, sheet_name="Template")
    buffer.seek(0)
    return buffer


def buat_unduhan_excel(df_in, nama_sheet="Data"):
    """Mengonversi dataframe menjadi file Excel (bytes) siap diunduh."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_in.to_excel(writer, index=False, sheet_name=nama_sheet)
    buffer.seek(0)
    return buffer


def buat_laporan_pdf(judul, ringkasan: dict):
    """
    Membuat PDF ringkasan KPI sederhana. Butuh paket 'fpdf2'
    (pip install fpdf2). Jika belum terpasang, fungsi mengembalikan None
    dan pengguna diarahkan memakai unduhan Excel/CSV sebagai gantinya.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, judul)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 6, f"Dibuat otomatis oleh Dashboard Energi & Mobilitas Cerdas - {pd.Timestamp.now():%Y-%m-%d %H:%M}")
    pdf.ln(4)
    pdf.set_text_color(20, 20, 20)
    for label, value in ringkasan.items():
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 8, str(label))
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, str(value), ln=1)

    hasil = pdf.output()
    if isinstance(hasil, (bytes, bytearray)):
        return bytes(hasil)
    return hasil.encode("latin-1")


def resample_tampilan(df, interval_label):
    """
    Meringkas data untuk kebutuhan TAMPILAN (tabel & grafik) saja.
    Data mentah 15 menit tetap dipakai untuk KPI, Rekomendasi Cerdas,
    dan Simulasi Skenario agar akurasi deteksi beban puncak tidak hilang.
    """
    if interval_label == "15 Menit (Asli)" or df.empty:
        return df
    aturan = "1h" if interval_label == "1 Jam" else "1D"
    aturan_agregasi = {
        "Daya_Mesin_kW": "mean", "Solar_Power_kW": "mean",
        "Emisi_CO2_kg": "sum",
        "AGV_01_SoC": "mean", "AGV_02_SoC": "mean", "AGV_03_SoC": "mean",
        "AGV_01_Charging": "any", "AGV_02_Charging": "any", "AGV_03_Charging": "any",
        "Status_Charging_AGV": "any",
        "Production_Output_Units": "sum",
    }
    return df.set_index("Timestamp").resample(aturan).agg(aturan_agregasi).reset_index()


def hitung_emisi_ulang(df, faktor_emisi):
    """Menghitung ulang kolom emisi CO2 mengikuti perubahan Daya_Mesin_kW / Solar_Power_kW."""
    daya_bersih = np.maximum(0, df["Daya_Mesin_kW"] - df["Solar_Power_kW"])
    df["Emisi_CO2_kg"] = (daya_bersih * (15 / 60) * faktor_emisi).round(3)
    return df


def buat_mask_filter(df_in, mulai, selesai, konteks):
    """Mask boolean gabungan: rentang tanggal + konteks operasional (jam kerja/off-peak/24 jam)."""
    mask = (df_in["Timestamp"].dt.date >= mulai) & (df_in["Timestamp"].dt.date <= selesai)
    jam = df_in["Timestamp"].dt.hour
    jam_kerja_mask = (jam >= JAM_KERJA_MULAI) & (jam < JAM_KERJA_SELESAI)
    if konteks == KONTEKS_JAM_KERJA:
        mask &= jam_kerja_mask
    elif konteks == KONTEKS_OFF_PEAK:
        mask &= ~jam_kerja_mask
    # KONTEKS_24_7 -> tidak ada filter tambahan (seluruh siklus 24 jam dipakai)
    return mask


def siapkan_tabel_tampilan(df_in):
    """
    Menyiapkan versi tabel yang RAMAH DIBACA untuk ditampilkan/diunduh:
    - kolom Timestamp dipecah menjadi 'Tanggal' dan 'Waktu' terpisah
    - nama kolom teknis diganti label berbahasa Indonesia yang lebih jelas
    (Tidak memengaruhi data internal yang dipakai untuk perhitungan.)
    """
    d = df_in.copy()
    if "Timestamp" in d.columns:
        d["Tanggal"] = d["Timestamp"].dt.strftime("%Y-%m-%d")
        d["Waktu"] = d["Timestamp"].dt.strftime("%H:%M")
        d = d.drop(columns=["Timestamp"])
    d = d.rename(columns=LABEL_KOLOM)
    kolom_depan = [c for c in ["Tanggal", "Waktu"] if c in d.columns]
    kolom_lain = [c for c in d.columns if c not in kolom_depan]
    return d[kolom_depan + kolom_lain]


def kembalikan_dari_tampilan(d_in):
    """Kebalikan dari siapkan_tabel_tampilan(): menyusun ulang ke skema data asli (KOLOM_WAJIB)."""
    d = d_in.copy()
    d = d.rename(columns=LABEL_KOLOM_BALIK)
    d["Timestamp"] = pd.to_datetime(d["Tanggal"].astype(str) + " " + d["Waktu"].astype(str))
    d = d.drop(columns=["Tanggal", "Waktu"])
    for k in KOLOM_WAJIB:
        if k not in d.columns:
            d[k] = np.nan
    return d[KOLOM_WAJIB].sort_values("Timestamp").reset_index(drop=True)


# ============================================================
# SIDEBAR: SUMBER DATA (tiga sumber dipisah & disimpan permanen)
# ============================================================
st.sidebar.title("⚡ Navigasi Dashboard")

with st.sidebar.expander("📁 Sumber Data", expanded=True):
    sumber_data = st.radio(
        "Pilih sumber dataset:",
        [SUMBER_SIMULASI, SUMBER_UNGGAH, SUMBER_EDIT],
        label_visibility="collapsed",
        key="pilih_sumber_data",
    )
    st.caption(
        "ℹ️ Ketiga sumber ini **terpisah & permanen**: mengganti pilihan tidak akan "
        "menghapus data sumber lain, dan hasil unggahan/edit manual tetap tersimpan "
        "walau dashboard ditutup lalu dibuka kembali."
    )
    st.download_button(
        "⬇️ Unduh Template Excel",
        data=buat_template_excel(),
        file_name="template_data_pabrik.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Gunakan format ini untuk mengunggah data Anda sendiri.",
    )
    for path, label in [
        (FILE_SIMULASI, "Simulasi"), (FILE_UNGGAHAN, "Unggahan"), (FILE_EDIT_MANUAL, "Edit Manual"),
    ]:
        info = info_checksum_csv(path, label)
        if info:
            st.caption(info)

# Inisialisasi data untuk sumber Simulasi (selalu tersedia)
df_simulasi = muat_data_simulasi()

# Muat / siapkan dataframe DASAR (belum difilter tanggal/konteks) sesuai sumber terpilih.
# df_utama_dasar SELALU berisi data UTUH 24 jam penuh; filter hanya diterapkan belakangan.
if sumber_data == SUMBER_SIMULASI:
    df_utama_dasar = df_simulasi.copy()

elif sumber_data == SUMBER_UNGGAH:
    berkas = st.sidebar.file_uploader("Unggah CSV atau Excel", type=["csv", "xlsx"], key="uploader_utama")
    if berkas is not None:
        df_baru = pd.read_csv(berkas) if berkas.name.endswith(".csv") else pd.read_excel(berkas)
        kolom_hilang = validasi_kolom(df_baru)
        if kolom_hilang:
            st.sidebar.error(f"Kolom belum lengkap: {', '.join(kolom_hilang)}")
            df_utama_dasar = muat_csv_persisten(FILE_UNGGAHAN)
        else:
            df_baru["Timestamp"] = pd.to_datetime(df_baru["Timestamp"])
            df_baru.to_csv(FILE_UNGGAHAN, index=False)   # simpan permanen
            st.sidebar.success(f"Berhasil memuat & menyimpan {len(df_baru)} baris data.")
            df_utama_dasar = df_baru
    else:
        df_utama_dasar = muat_csv_persisten(FILE_UNGGAHAN)
        if df_utama_dasar is None:
            st.sidebar.warning("Belum ada file yang diunggah. Silakan unggah CSV/Excel sesuai template.")

else:  # SUMBER_EDIT
    df_persisten = muat_csv_persisten(FILE_EDIT_MANUAL)
    df_utama_dasar = df_persisten if df_persisten is not None else df_simulasi.copy()
    st.sidebar.info(
        "Ubah nilai langsung pada tabel di modul **Ringkasan Kinerja**, lalu klik "
        "**Terapkan & Simpan Perubahan**. Perubahan tersimpan permanen di file terpisah "
        "(tidak memengaruhi data simulasi asli)."
    )

if df_utama_dasar is None or df_utama_dasar.empty:
    st.warning("⚠️ Belum ada data untuk ditampilkan pada sumber ini. Silakan pilih/unggah data terlebih dahulu.")
    st.stop()

# ============================================================
# SIDEBAR: PARAMETER OPERASIONAL
# ============================================================
st.sidebar.subheader("⚙️ Parameter Operasional")
kapasitas_solar = st.sidebar.number_input("Kapasitas Solar Panel Terpasang (kWp)", value=35.0, step=1.0, min_value=1.0)
faktor_emisi = st.sidebar.number_input("Faktor Emisi Grid (kg CO2/kWh)", value=0.85, step=0.01)
tarif_listrik = st.sidebar.number_input("Tarif Listrik PLN (Rp/kWh)", value=1500, step=50)
daya_charger_agv = st.sidebar.number_input("Daya Pengisian per Unit AGV (kW)", value=5.0, step=0.5)
batas_beban_puncak = st.sidebar.number_input("Batas Beban Puncak Pabrik (kW)", value=80.0, step=5.0)

st.sidebar.subheader("🎯 Ambang Batas Baterai AGV")
min_soc = st.sidebar.slider("Batas Minimal SoC (%)", 0, 50, 20)
max_soc = st.sidebar.slider("Target SoC Penuh (%)", 50, 100, 90)

st.sidebar.subheader("🧭 Modul")
modul = st.sidebar.radio(
    "Pilih modul dashboard:",
    [MODUL_RINGKASAN, MODUL_ENERGI, MODUL_ARMADA, MODUL_REKOMENDASI, MODUL_SIMULASI],
    label_visibility="collapsed",
)

st.sidebar.subheader("🔍 Interval Tampilan")
interval_tampilan = st.sidebar.selectbox(
    "Resolusi tabel & grafik",
    ["15 Menit (Asli)", "1 Jam", "Harian"],
    index=1,
    help="Hanya meringkas tampilan tabel/grafik. KPI dan Rekomendasi Cerdas tetap "
         "memakai data 15 menit asli agar akurasi deteksi beban puncak terjaga.",
)

st.sidebar.subheader("📅 Filter Tanggal")
tgl_min, tgl_max = df_utama_dasar["Timestamp"].dt.date.min(), df_utama_dasar["Timestamp"].dt.date.max()
rentang_tanggal = st.sidebar.date_input(
    "Rentang tanggal analisis", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max
)
if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
    mulai, selesai = rentang_tanggal
else:
    mulai, selesai = tgl_min, tgl_max

st.sidebar.subheader("🕒 Konteks Operasional")
konteks_operasional = st.sidebar.radio(
    "Bagian siklus 24 jam yang ingin dianalisis:",
    [KONTEKS_24_7, KONTEKS_JAM_KERJA, KONTEKS_OFF_PEAK],
    help=(
        f"**{KONTEKS_JAM_KERJA}**: untuk menghitung efisiensi produksi & lonjakan beban kerja utama.\n\n"
        f"**{KONTEKS_OFF_PEAK}**: untuk menganalisis konsumsi energi standby & pengisian baterai malam hari.\n\n"
        f"**{KONTEKS_24_7}**: untuk menghitung total biaya tagihan bulanan & total emisi CO2 nyata."
    ),
)
st.sidebar.caption(
    "Basis data tetap mencatat seluruh siklus 15 menit selama 24 jam penuh — "
    "filter ini hanya membatasi bagian mana yang dianalisis di layar, data lain tidak dihapus."
)

# Mask & data hasil filter (dipakai di seluruh modul)
mask_filter = buat_mask_filter(df_utama_dasar, mulai, selesai, konteks_operasional)
df = df_utama_dasar[mask_filter].reset_index(drop=True)
df = hitung_emisi_ulang(df, faktor_emisi)
df_tampil = resample_tampilan(df, interval_tampilan)

if df.empty:
    st.warning("⚠️ Tidak ada data pada kombinasi filter tanggal & konteks operasional ini.")
    st.stop()

# ============================================================
# HEADER
# ============================================================
st.markdown("<h2 style='text-align:center;'>Dashboard Interaktif Manajemen Efisiensi Energi & Mobilitas Cerdas</h2>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle' style='text-align:center;'>Optimasi konsumsi daya pabrik, kontribusi energi surya, dan pengisian daya AGV secara berkelanjutan</p>", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center; color:#5878B0; font-size:0.85rem;'>Sumber data aktif: "
    f"<b>{sumber_data}</b> &nbsp;|&nbsp; Konteks: <b>{konteks_operasional}</b> &nbsp;|&nbsp; "
    f"Periode: <b>{mulai} s/d {selesai}</b></p>",
    unsafe_allow_html=True,
)
st.write("")

# Metrik dasar yang dipakai berulang di beberapa modul
total_daya_kwh = df["Daya_Mesin_kW"].sum() / 4
total_solar_kwh = df["Solar_Power_kW"].sum() / 4
total_emisi = df["Emisi_CO2_kg"].sum()
emisi_tanpa_solar = (df["Daya_Mesin_kW"] * (15 / 60) * faktor_emisi).sum()
reduksi_emisi_persen = ((emisi_tanpa_solar - total_emisi) / emisi_tanpa_solar * 100) if emisi_tanpa_solar > 0 else 0
kontribusi_solar_persen = (total_solar_kwh / total_daya_kwh * 100) if total_daya_kwh > 0 else 0

ringkasan_kpi = {
    "Sumber Data": sumber_data,
    "Konteks Operasional": konteks_operasional,
    "Periode": f"{mulai} s/d {selesai}",
    "Total Konsumsi Listrik": f"{total_daya_kwh:,.0f} kWh",
    "Kontribusi Energi Surya": f"{kontribusi_solar_persen:.1f} %",
    "Reduksi Emisi CO2 (vs tanpa surya)": f"{reduksi_emisi_persen:.1f} %",
    "Total Emisi CO2": f"{total_emisi:,.1f} kg",
    "Estimasi Biaya Listrik (tarif saat ini)": f"Rp {(total_daya_kwh - total_solar_kwh) * tarif_listrik:,.0f}",
}

# --- Unduhan ringkasan tersedia di seluruh modul (sidebar bawah) ---
with st.sidebar.expander("📤 Ekspor / Unduh Hasil", expanded=False):
    pdf_bytes = buat_laporan_pdf("Ringkasan Kinerja Energi & Mobilitas Cerdas", ringkasan_kpi)
    if pdf_bytes:
        st.download_button("📄 Unduh Ringkasan (PDF)", data=pdf_bytes,
                            file_name="ringkasan_dashboard.pdf", mime="application/pdf")
    else:
        st.caption("Unduh PDF butuh paket `fpdf2` (`pip install fpdf2`). Gunakan unduhan Excel di bawah untuk saat ini.")
    st.download_button(
        "📊 Unduh Data Terfilter (Excel)",
        data=buat_unduhan_excel(siapkan_tabel_tampilan(df), "Data Telemetri"),
        file_name="data_terfilter.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ============================================================
# MODUL 1: RINGKASAN KINERJA (OVERVIEW)
# ============================================================
if modul == MODUL_RINGKASAN:
    st.caption(
        "Ringkasan cepat kondisi pabrik: total pemakaian listrik, kontribusi energi surya, "
        "penurunan emisi karbon, dan status armada AGV — semuanya mengikuti filter tanggal "
        "dan konteks operasional yang dipilih di sidebar."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Konsumsi Listrik", f"{total_daya_kwh:,.0f} kWh")
    c2.metric("Kontribusi Energi Surya", f"{kontribusi_solar_persen:.1f}%")
    c3.metric("Reduksi Emisi CO2", f"{reduksi_emisi_persen:.1f}%")
    jumlah_agv_aktif = sum(df[f"{a}_SoC"].iloc[-1] > 0 for a in DAFTAR_AGV) if len(df) else 0
    c4.metric("Jumlah AGV Aktif", f"{jumlah_agv_aktif} / {len(DAFTAR_AGV)} unit")

    st.write("")
    st.subheader("Tabel Data Telemetri (Detail per Interval 15 Menit)")

    if sumber_data == SUMBER_EDIT:
        st.caption(
            "Kolom **Tanggal** format `YYYY-MM-DD`, kolom **Waktu** format `HH:MM`. "
            "Baris di luar rentang tanggal/konteks yang sedang difilter TIDAK ikut ditampilkan "
            "di sini, tapi tetap aman tersimpan di data dasar."
        )
        df_tampil_edit = siapkan_tabel_tampilan(df)
        df_edit_hasil = st.data_editor(df_tampil_edit, use_container_width=True, num_rows="dynamic", key="editor_utama")
        if st.button("✅ Terapkan & Simpan Perubahan"):
            try:
                df_edit_baru = kembalikan_dari_tampilan(df_edit_hasil)
            except Exception as e:
                st.error(f"Gagal membaca perubahan — periksa format Tanggal/Waktu. Detail: {e}")
            else:
                df_edit_baru = hitung_emisi_ulang(df_edit_baru, faktor_emisi)
                # Gabungkan: baris DI LUAR filter saat ini tetap dari data dasar lama,
                # baris DI DALAM filter diganti sepenuhnya oleh hasil edit (termasuk
                # baris baru yang ditambahkan / baris yang dihapus pengguna).
                df_luar_filter = df_utama_dasar[~mask_filter].copy()
                df_gabungan = pd.concat([df_luar_filter, df_edit_baru], ignore_index=True)
                df_gabungan = df_gabungan.sort_values("Timestamp").reset_index(drop=True)
                df_gabungan.to_csv(FILE_EDIT_MANUAL, index=False)  # simpan permanen ke disk
                st.success("Perubahan tersimpan permanen. Data akan tetap ada walau dashboard ditutup & dibuka kembali.")
                st.rerun()
    else:
        st.caption(f"Menampilkan data dengan resolusi: **{interval_tampilan}**" + (
            " — SoC = rata-rata & Isi Daya = *pernah terjadi* dalam periode ini (lihat catatan di modul Armada AGV/EV)."
            if interval_tampilan != "15 Menit (Asli)" else ""
        ))
        st.dataframe(siapkan_tabel_tampilan(df_tampil), use_container_width=True)
        st.caption("💡 Ingin mengedit data ini? Pilih sumber data **Edit Manual di Tabel** di sidebar.")

# ============================================================
# MODUL 2: ENERGI & JEJAK EMISI
# ============================================================
elif modul == MODUL_ENERGI:
    st.caption(
        "Modul ini membandingkan berapa banyak listrik pabrik dipasok dari **panel surya** vs "
        "**PLN**, dan menghitung berapa emisi CO2 yang dihasilkan maupun yang berhasil dihindari "
        "berkat energi terbarukan."
    )

    st.subheader("Beban Listrik Pabrik vs Produksi Energi Surya")
    st.caption(f"Resolusi grafik: **{interval_tampilan}**. Garis biru tua = total daya yang dipakai mesin pabrik; area biru muda = daya yang berhasil dipasok panel surya.")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df_tampil["Timestamp"], y=df_tampil["Daya_Mesin_kW"], name="Beban Mesin (kW)", line=dict(color=WARNA_BIRU_TUA)))
    fig_line.add_trace(go.Scatter(x=df_tampil["Timestamp"], y=df_tampil["Solar_Power_kW"], name="Daya Surya (kW)", fill="tozeroy", line=dict(color=WARNA_BIRU_CERAH), fillcolor="rgba(187,212,255,0.5)"))
    fig_line.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1), margin=dict(t=30),
                            xaxis_title="Waktu", yaxis_title="Daya (kW)")
    st.plotly_chart(fig_line, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Proporsi Sumber Energi")
        fig_donut = px.pie(
            names=["Listrik PLN", "Panel Surya"],
            values=[max(total_daya_kwh - total_solar_kwh, 0), total_solar_kwh],
            hole=0.55,
            color_discrete_sequence=[WARNA_BIRU_TUA, WARNA_BIRU_CERAH],
        )
        fig_donut.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown(
            f"<div class='block-analisis'>📊 <b>Analisis:</b> pada periode & konteks yang dipilih, "
            f"<b>{kontribusi_solar_persen:.1f}%</b> kebutuhan listrik pabrik sudah dipasok panel surya, "
            f"sisanya <b>{100 - kontribusi_solar_persen:.1f}%</b> masih bergantung pada PLN. "
            f"{'Ini tergolong kontribusi surya yang cukup baik.' if kontribusi_solar_persen >= 25 else 'Masih ada ruang besar untuk memperbesar kapasitas solar agar ketergantungan pada PLN menurun (coba modul Simulasi Skenario).'}"
            f"</div>", unsafe_allow_html=True,
        )
    with col_b:
        st.subheader("Tren Emisi CO2 Harian")
        emisi_harian = df.groupby(df["Timestamp"].dt.date)["Emisi_CO2_kg"].sum().reset_index()
        emisi_harian.columns = ["Tanggal", "Emisi_CO2_kg"]
        fig_bar = px.bar(emisi_harian, x="Tanggal", y="Emisi_CO2_kg", color_discrete_sequence=[WARNA_BIRU_CERAH])
        fig_bar.update_layout(margin=dict(t=10, b=10), xaxis_title="Tanggal", yaxis_title="Emisi CO2 (kg)")
        st.plotly_chart(fig_bar, use_container_width=True)

        if len(emisi_harian) >= 2:
            hari_tertinggi = emisi_harian.loc[emisi_harian["Emisi_CO2_kg"].idxmax()]
            hari_terendah = emisi_harian.loc[emisi_harian["Emisi_CO2_kg"].idxmin()]
            tren = emisi_harian["Emisi_CO2_kg"].iloc[-1] - emisi_harian["Emisi_CO2_kg"].iloc[0]
            arah_tren = "menurun 📉" if tren < 0 else ("meningkat 📈" if tren > 0 else "relatif stabil ➡️")
            st.markdown(
                f"<div class='block-analisis'>📊 <b>Analisis:</b> emisi harian tertinggi terjadi pada "
                f"<b>{hari_tertinggi['Tanggal']}</b> ({hari_tertinggi['Emisi_CO2_kg']:.1f} kg), sedangkan "
                f"terendah pada <b>{hari_terendah['Tanggal']}</b> ({hari_terendah['Emisi_CO2_kg']:.1f} kg). "
                f"Secara umum tren emisi pada periode ini <b>{arah_tren}</b> dari awal ke akhir periode.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='block-analisis'>📊 Pilih rentang tanggal lebih dari 1 hari agar tren emisi harian dapat dibandingkan.</div>", unsafe_allow_html=True)

# ============================================================
# MODUL 3: ARMADA AGV/EV
# ============================================================
elif modul == MODUL_ARMADA:
    st.caption(
        "Modul ini memantau kondisi baterai (State of Charge/SoC) dan aktivitas pengisian daya "
        "tiap unit AGV, agar armada tidak kehabisan baterai di tengah proses produksi."
    )

    st.subheader("Status Terkini Baterai AGV")
    data_status = []
    for a in DAFTAR_AGV:
        soc_terkini = df[f"{a}_SoC"].iloc[-1] if len(df) else np.nan
        status = "🔌 Mengisi Daya" if df[f"{a}_Charging"].iloc[-1] else "🔋 Beroperasi"
        kondisi = "⚠️ Rendah" if soc_terkini <= min_soc else ("✅ Optimal" if soc_terkini >= max_soc else "🟡 Normal")
        data_status.append({"Unit AGV": a, "SoC Terkini (%)": soc_terkini, "Status": status, "Kondisi Baterai": kondisi})
    st.dataframe(pd.DataFrame(data_status), use_container_width=True, hide_index=True)
    st.markdown(
        f"<div class='block-note'>Keterangan kondisi baterai — "
        f"⚠️ <b>Rendah</b>: SoC ≤ {min_soc}% (mendekati/di bawah ambang minimal, berisiko AGV berhenti); "
        f"🟡 <b>Normal</b>: di antara {min_soc}% dan {max_soc}%, aman untuk operasi harian; "
        f"✅ <b>Optimal</b>: SoC ≥ {max_soc}% (baterai penuh/mendekati penuh, siap operasi penuh waktu). "
        f"Ambang batas ini bisa diubah lewat sidebar (Ambang Batas Baterai AGV).</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.subheader("Tren Pengisian/Penurunan Daya Baterai")
    st.caption(f"Resolusi grafik: **{interval_tampilan}**")
    if interval_tampilan != "15 Menit (Asli)":
        st.markdown(
            "<div class='block-note'>ℹ️ Pada resolusi <b>1 Jam</b> atau <b>Harian</b>, nilai SoC yang "
            "ditampilkan adalah <b>rata-rata</b> selama periode tersebut, sedangkan status Isi Daya "
            "menunjukkan apakah pengisian terjadi <b>kapan pun</b> dalam periode itu. Akibatnya, SoC pada "
            "satu periode bisa tampak lebih tinggi dari periode sebelumnya meski status Isi Daya periode itu "
            "sudah <i>False</i> — ini wajar (pengisian baru saja selesai di awal periode). Untuk melihat "
            "korelasi SoC dan status Isi Daya secara presisi per kejadian, pilih interval <b>15 Menit (Asli)</b> "
            "di sidebar.</div>", unsafe_allow_html=True,
        )
    fig_agv = go.Figure()
    warna = {"AGV_01": WARNA_BIRU_CERAH, "AGV_02": WARNA_BIRU_TUA, "AGV_03": "#6FA0E8"}
    for a in DAFTAR_AGV:
        fig_agv.add_trace(go.Scatter(x=df_tampil["Timestamp"], y=df_tampil[f"{a}_SoC"], name=a, line=dict(color=warna[a])))
    fig_agv.add_hline(y=min_soc, line_dash="dot", line_color=WARNA_MERAH, annotation_text="Batas Minimal")
    fig_agv.add_hline(y=max_soc, line_dash="dot", line_color=WARNA_BIRU_TUA, annotation_text="Target Penuh")
    fig_agv.update_layout(hovermode="x unified", xaxis_title="Waktu", yaxis_title="State of Charge (%)", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_agv, use_container_width=True)

    baris_analisis = []
    for a in DAFTAR_AGV:
        siklus_isi = int((df[f"{a}_Charging"].astype(int).diff() == 1).sum())
        rata_soc = df[f"{a}_SoC"].mean()
        soc_min = df[f"{a}_SoC"].min()
        baris_analisis.append(f"<b>{a}</b>: rata-rata SoC {rata_soc:.1f}%, titik terendah {soc_min:.1f}%, tercatat {siklus_isi}x memulai siklus pengisian pada periode ini")
    st.markdown(
        "<div class='block-analisis'>📊 <b>Analisis:</b><br>" + "<br>".join(baris_analisis) +
        f"<br><br>Semakin sering suatu unit menyentuh batas minimal ({min_soc}%), semakin besar risiko unit "
        f"tersebut mengganggu jadwal produksi karena harus berhenti untuk mengisi daya di jam kerja.</div>",
        unsafe_allow_html=True,
    )

# ============================================================
# MODUL 4: REKOMENDASI CERDAS (SMART RECOMMENDATION)
# ============================================================
elif modul == MODUL_REKOMENDASI:
    st.caption(
        "Modul ini otomatis memeriksa setiap interval 15 menit untuk mencari kejadian di mana "
        "**AGV sedang mengisi daya** pada saat **beban listrik pabrik sedang tinggi** (melebihi "
        "batas beban puncak yang ditetapkan di sidebar). Kejadian seperti ini berisiko memicu "
        "tarikan daya ekstra dari PLN yang mahal (biaya beban puncak)."
    )
    st.subheader("Deteksi Pengisian Daya AGV Saat Beban Puncak")

    kejadian_puncak = df[(df["Daya_Mesin_kW"] > batas_beban_puncak) & (df["Status_Charging_AGV"])]
    jumlah_kejadian = len(kejadian_puncak)

    if jumlah_kejadian > 0:
        energi_terdampak_kwh = jumlah_kejadian * daya_charger_agv * (15 / 60)
        estimasi_biaya = energi_terdampak_kwh * tarif_listrik
        jam_tersering = kejadian_puncak["Timestamp"].dt.hour.mode()
        jam_tersering = int(jam_tersering.iloc[0]) if len(jam_tersering) else None

        st.warning(
            f"⚠️ **Peringatan Beban Puncak:** terdeteksi **{jumlah_kejadian} interval** "
            f"(15 menit) pengisian daya AGV bersamaan dengan beban pabrik melebihi {batas_beban_puncak:.0f} kW."
        )
        st.info(
            "💡 **Rekomendasi:** alihkan jadwal pengisian daya AGV ke rentang pukul 11.00–14.00 "
            "saat produksi panel surya berada di puncaknya, guna mengurangi tarikan daya dari PLN "
            "dan menghindari biaya beban puncak."
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimasi Energi Terdampak", f"{energi_terdampak_kwh:,.1f} kWh")
        c2.metric("Estimasi Potensi Penghematan", f"Rp {estimasi_biaya:,.0f}")
        c3.metric("Jam Paling Sering Bermasalah", f"Pukul {jam_tersering:02d}:00" if jam_tersering is not None else "-")
    else:
        st.success("✅ **Kondisi Optimal:** pengisian daya AGV berjalan efisien tanpa memicu beban puncak.")

    st.write("")
    st.subheader("Detail Interval Bermasalah")
    st.caption(
        "Daftar interval 15 menit yang memenuhi kedua syarat sekaligus: beban mesin pabrik di atas "
        "batas beban puncak, DAN minimal satu unit AGV sedang mengisi daya pada saat bersamaan."
    )
    if jumlah_kejadian > 0:
        tabel_masalah = siapkan_tabel_tampilan(
            kejadian_puncak[["Timestamp", "Daya_Mesin_kW", "Solar_Power_kW", "Status_Charging_AGV"]]
        )
        st.dataframe(tabel_masalah, use_container_width=True, hide_index=True)
        jam_terdampak = sorted(kejadian_puncak["Timestamp"].dt.hour.unique())
        st.markdown(
            f"<div class='block-analisis'>📊 <b>Analisis:</b> kejadian bermasalah tersebar pada jam "
            f"{', '.join(f'{j:02d}:00' for j in jam_terdampak)}. "
            f"Jika jam-jam tersebut berhimpitan dengan jam kerja operasional "
            f"({JAM_KERJA_MULAI:02d}:00–{JAM_KERJA_SELESAI:02d}:00), artinya pengisian AGV sedang "
            f"bersaing langsung dengan beban produksi utama — prioritaskan menggeser jadwal charging "
            f"unit tersebut ke luar jam kerja atau ke jam puncak produksi surya.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='block-note'>Tidak ada interval bermasalah pada kombinasi filter tanggal & konteks operasional yang dipilih.</div>", unsafe_allow_html=True)

# ============================================================
# MODUL 5: SIMULASI SKENARIO EFISIENSI
# ============================================================
elif modul == MODUL_SIMULASI:
    st.caption(
        "Modul pendukung keputusan (Decision Support System): uji **\"bagaimana jika\"** sebelum "
        "kebijakan diterapkan di lapangan. Geser kedua parameter di bawah untuk melihat proyeksi "
        "dampaknya terhadap emisi CO2 — tanpa mengubah data asli."
    )
    st.subheader("Simulasi Dampak Perubahan Kapasitas Solar & Pola Pengisian AGV")

    col1, col2 = st.columns(2)
    with col1:
        tambahan_kapasitas = st.slider(
            "Penambahan Kapasitas Solar Panel (kWp)", 0, 500, 0, step=5,
            help="Simulasi menambah panel surya di atas kapasitas terpasang saat ini "
                 f"({kapasitas_solar:.0f} kWp). Geser hingga 500 kWp tambahan; untuk nilai "
                 "lebih besar lagi, ubah batas atas slider pada kode (max_value)."
        )
    with col2:
        pergeseran_charging = st.slider(
            "Persentase Pengisian AGV Dialihkan ke Jam Puncak Solar (%)", 0, 100, 0, step=10,
            help="Persentase dari kejadian charging-saat-beban-puncak yang berhasil dipindah "
                 "jadwalnya ke jam puncak produksi solar (sekitar pukul 12.00)."
        )

    faktor_skala = (kapasitas_solar + tambahan_kapasitas) / kapasitas_solar if kapasitas_solar > 0 else 1
    solar_proyeksi = (df["Solar_Power_kW"] * faktor_skala).clip(upper=kapasitas_solar + tambahan_kapasitas)

    kejadian_puncak_now = (df["Daya_Mesin_kW"] > batas_beban_puncak) & (df["Status_Charging_AGV"])
    pengurangan_beban = kejadian_puncak_now * daya_charger_agv * (pergeseran_charging / 100)
    daya_mesin_proyeksi = (df["Daya_Mesin_kW"] - pengurangan_beban).clip(lower=0)

    daya_bersih_proyeksi = np.maximum(0, daya_mesin_proyeksi - solar_proyeksi)
    emisi_proyeksi = (daya_bersih_proyeksi * (15 / 60) * faktor_emisi).sum()
    delta_emisi = total_emisi - emisi_proyeksi
    persen_reduksi_tambahan = (delta_emisi / total_emisi * 100) if total_emisi > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Emisi CO2 Saat Ini", f"{total_emisi:,.1f} kg")
    c2.metric("Emisi CO2 Proyeksi", f"{emisi_proyeksi:,.1f} kg", delta=f"-{delta_emisi:,.1f} kg")
    c3.metric("Reduksi Tambahan", f"{persen_reduksi_tambahan:.1f}%")

    fig_sim = go.Figure()
    fig_sim.add_trace(go.Bar(
        name="Emisi Saat Ini", x=["Total Emisi CO2 (kg)"], y=[total_emisi],
        marker_color=WARNA_BIRU_TUA, text=[f"{total_emisi:,.1f}"], textposition="outside",
    ))
    fig_sim.add_trace(go.Bar(
        name="Emisi Proyeksi", x=["Total Emisi CO2 (kg)"], y=[emisi_proyeksi],
        marker_color=WARNA_HIJAU if emisi_proyeksi < total_emisi else WARNA_BIRU_CERAH,
        text=[f"{emisi_proyeksi:,.1f}"], textposition="outside",
    ))
    fig_sim.update_layout(
        barmode="group", margin=dict(t=30, b=10),
        yaxis_title="Total Emisi CO2 (kg)", legend=dict(orientation="h", y=1.15),
        yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(fig_sim, use_container_width=True)

    if tambahan_kapasitas == 0 and pergeseran_charging == 0:
        analisis_sim = "Geser salah satu atau kedua slider di atas untuk melihat proyeksi penurunan emisi dibandingkan kondisi saat ini."
    else:
        bagian = []
        if tambahan_kapasitas > 0:
            bagian.append(f"penambahan {tambahan_kapasitas:.0f} kWp kapasitas solar (naik menjadi {kapasitas_solar + tambahan_kapasitas:.0f} kWp)")
        if pergeseran_charging > 0:
            bagian.append(f"pengalihan {pergeseran_charging:.0f}% pengisian AGV ke jam puncak solar")
        analisis_sim = (
            f"Dengan {' dan '.join(bagian)}, emisi CO2 diproyeksikan turun dari {total_emisi:,.1f} kg "
            f"menjadi {emisi_proyeksi:,.1f} kg — reduksi tambahan sekitar <b>{persen_reduksi_tambahan:.1f}%</b> "
            f"dibanding kondisi saat ini. "
            + ("Ini adalah reduksi yang cukup signifikan dan layak dipertimbangkan sebagai kebijakan." if persen_reduksi_tambahan >= 10
               else "Dampaknya masih relatif kecil; coba naikkan salah satu parameter untuk melihat titik yang lebih optimal.")
        )

    st.markdown(f"<div class='block-analisis'>📊 <b>Analisis:</b> {analisis_sim}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='block-note'>Catatan asumsi: produksi solar diasumsikan naik secara linear "
        "terhadap penambahan kapasitas, dan daya charging yang dialihkan diasumsikan sepenuhnya "
        "disuplai dari solar tanpa menambah beban PLN. Hasil ini adalah estimasi untuk pengambilan "
        "keputusan awal, bukan angka final rekayasa.</div>",
        unsafe_allow_html=True,
    )

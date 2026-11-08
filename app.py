"""Aplikasi Streamlit — Asisten Diagnosis Masalah Komputer berbasis UCS.

Tampilan antarmuka Modern Tech Diagnostics:
- Desain profesional, bersih, dan bertema teknologi diagnostik komputer.
- Classical Artificial Intelligence dengan algoritma Uniform Cost Search (UCS).
- Seluruh pemeriksaan disimulasikan melalui basis pengetahuan JSON terstruktur.
- Tidak melakukan perubahan otomatis ke sistem operasi Windows.
"""

from __future__ import annotations

import html
from collections.abc import MutableMapping
from typing import Any

import streamlit as st

from core.diagnosis import (
    DiagnosisState,
    apply_test_result,
    evaluate_diagnosis,
    get_evidence_sufficiency,
    get_next_recommended_test,
    get_pending_tests,
    initialize_diagnosis,
)
from core.exceptions import DiagnosisError, KnowledgeBaseError
from core.knowledge_base import load_diagnostic_tests, load_symptoms
from core.symptom_matcher import (
    create_user_defined_symptom,
    suggest_symptoms_from_text,
    validate_bsod_code,
)

APP_NAME = "Asisten Diagnosis Masalah Komputer"
APP_DESCRIPTION = (
    "Sistem pakar diagnostik berbasis Classical Artificial Intelligence dengan algoritma "
    "Uniform Cost Search (UCS) untuk mengidentifikasi akar permasalahan sistem Windows secara efisien."
)

OUTCOME_LABELS = {
    "normal": "Normal (Suhu Stabil)",
    "elevated": "Meningkat (Hangat / Waspada)",
    "critical": "Kritis (Panas Ekstrem)",
    "healthy": "Sehat (Kondisi Prima)",
    "warning": "Peringatan (Atribut Kritis Muncul)",
    "bad": "Buruk (Kerusakan Sektor / Gagal)",
    "all_ok": "Semua Normal (Driver Stabil)",
    "yellow_bang": "Tanda Seru Kuning (Error / Corrupt)",
    "error_code": "Kode Error Driver (Device Fails)",
    "no_errors": "Tidak Ada Error (Log Bersih)",
    "disk_errors_present": "Error Disk Ditemukan (Bad Block/I/O)",
    "no_driver_errors": "Tidak Ada Error Driver (Minidump Bersih)",
    "driver_errors_found": "Error Driver Terdeteksi (Crash Dump)",
    "errors_found": "Error Ditemukan (Modul RAM Korup)",
    "skip": "Lewati pemeriksaan ini (Skip)",
}

EVIDENCE_LABELS = {
    "driver_issue_confirmed": "Indikasi Masalah Driver Terkonfirmasi",
    "high_temperature_confirmed": "Temperatur Tinggi Abnormal Terkonfirmasi",
    "disk_issue_confirmed": "Indikasi Kerusakan Storage / Disk Terkonfirmasi",
    "memory_issue_confirmed": "Indikasi Kegagalan Modul RAM Terkonfirmasi",
}

SUFFICIENCY_LABELS = {
    "sufficient": ("CUKUP", "green", "Bukti minimum untuk satu kategori telah terpenuhi tanpa kontradiksi aktif."),
    "partial": ("BELUM CUKUP", "amber", "Bukti belum definitif. Pemeriksaan lanjutan masih dapat dijalankan."),
    "insufficient": ("TIDAK CUKUP", "red", "Seluruh pemeriksaan relevan telah selesai, namun tidak ada bukti pendukung konklusif."),
    "conflicting": ("BERPENTANGAN", "red", "Terdapat bukti yang saling bertentangan antar kategori masalah."),
}

CATEGORY_ICONS = {
    "driver_software": "DRV",
    "overheating": "THM",
    "storage_disk": "DSK",
    "ram_memory": "RAM",
}

CATEGORY_SUBTITLES = {
    "driver_software": "Konflik driver .sys, Device Manager, & OS crash",
    "overheating": "Disipasi panas CPU/GPU & sirkulasi udara casing",
    "storage_disk": "Integritas S.M.A.R.T., bad sector, & I/O drive",
    "ram_memory": "Stabilitas modul memori fisik & memory leak",
}

# Petunjuk pemeriksaan per test_id (dari data/diagnostic_tests.json)
DIAGNOSTIC_INSTRUCTIONS: dict[str, dict[str, Any]] = {
    "test_cpu_gpu_temp": {
        "steps": [
            "Unduh dan buka aplikasi monitoring suhu (HWMonitor, Core Temp, atau HWiNFO).",
            "Biarkan komputer idle beberapa menit, catat suhu CPU & GPU.",
            "Jalankan beban berat (game/rendering) 5-10 menit, amati suhu puncak.",
            "Bandingkan dengan ambang: CPU idle <50°C, elevated 50-80°C, kritis >80°C. GPU idle <45°C, elevated 45-83°C, kritis >83°C.",
        ],
        "windows_path": "Tidak perlu menu Windows — unduh aplikasi monitoring suhu dari situs resmi.",
        "warning": None,
        "skip_allowed": True,
    },
    "test_smart_disk": {
        "steps": [
            "Unduh CrystalDiskInfo (versi portable) atau gunakan `wmic diskdrive get status` di CMD.",
            "Buka CrystalDiskInfo, periksa kolom 'Health Status' dan atribut: Reallocated Sectors Count (05), Current Pending Sector (C5), Offline Uncorrectable (C6).",
            "Jika status 'Caution' atau 'Bad', catat atribut yang bermasalah.",
            "Backup data penting segera jika ada indikator warning.",
        ],
        "windows_path": "Start → CMD (Admin) → `wmic diskdrive get status`",
        "warning": "Jika S.M.A.R.T. menunjukkan Bad/Caution, hentikan aktivitas disk berat dan backup segera.",
        "skip_allowed": True,
    },
    "test_driver_status": {
        "steps": [
            "Buka Device Manager (Win+X → Device Manager).",
            "Periksa apakah ada perangkat dengan tanda seru kuning (⚠) atau status 'Unknown device'.",
            "Klik kanan perangkat bermasalah → Properties → tab Driver → catat versi driver dan error code.",
            "Coba Update Driver → Search automatically, atau unduh driver terbaru dari situs produsen (NVIDIA/AMD/Intel/Realtek/dll).",
        ],
        "windows_path": "Win+X → Device Manager",
        "warning": "Hindari driver dari situs pihak ketiga yang tidak resmi; gunakan situs produsen hardware.",
        "skip_allowed": True,
    },
    "test_disk_system_error_logs": {
        "steps": [
            "Buka Event Viewer (Win+X → Event Viewer).",
            "Navigasi: Windows Logs → System.",
            "Filter Current Log → Event sources: 'disk', 'ntfs', 'storahci', 'iaStorV' → OK.",
            "Cari Event ID: 7, 9, 11, 51, 153, 521, atau Level 'Error'/'Warning' terkait disk.",
            "Catat jumlah dan pola error (sering saat idle, saat beban, atau acak).",
        ],
        "windows_path": "Win+X → Event Viewer → Windows Logs → System",
        "warning": "Error disk berulang (Event ID 7/11/51) mengindikasikan kerusakan fisik media — backup segera.",
        "skip_allowed": True,
    },
    "test_error_code_history": {
        "steps": [
            "Buka Reliability Monitor (Win → ketik 'reliability' → View reliability history).",
            "Cari item 'Windows Failure' atau 'BSOD' pada grafik, klik untuk detail.",
            "Catat Bug Check Code (mis. 0x0000001A, 0x000000D1) dan nama file driver (.sys) jika ada.",
            "Atau gunakan BlueScreenView / WhoCrashed untuk membaca minidump (%SystemRoot%\\Minidump\\).",
            "Cari pola: driver yang sama berulang, atau kategori error konsisten.",
        ],
        "windows_path": "Start → Reliability Monitor",
        "warning": "Minidump memerlukan izin Administrator; pastikan 'Small memory dump' aktif di System Properties → Startup and Recovery.",
        "skip_allowed": True,
    },
    "test_memory_diagnostic": {
        "steps": [
            "Simpan semua pekerjaan dan tutup aplikasi.",
            "Tekan Win+R, ketik `mdsched`, tekan Enter.",
            "Pilih 'Restart now and check for problems (recommended)'.",
            "Sistem restart dan menjalankan Windows Memory Diagnostic (bisa memakan waktu 15-40 menit).",
            "Setelah boot, hasil muncul di notifikasi atau Event Viewer → System → Source: MemoryDiagnostics-Results.",
        ],
        "windows_path": "Win+R → mdsched → Restart sekarang",
        "warning": "Komputer Akan RESTART. Pastikan semua file tersimpan. Tes standar (Standard) memadai; Extended lebih teliti tapi jauh lebih lama.",
        "skip_allowed": True,
    },
}

CUSTOM_CSS = """
<style>
    /* Google Fonts Import dengan Fallback Aman */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

    :root {
        --deep-navy: #172554;
        --midnight-navy: #111827;
        --primary-blue: #2563EB;
        --electric-cyan: #06B6D4;
        --sky-blue: #0EA5E9;
        --teal-accent: #14B8A6;
        --bg-main: #F1F5F9;
        --surface-white: #FFFFFF;
        --text-main: #172033;
        --text-secondary: #64748B;
        --border-color: #E2E8F0;
        --success-green: #16A34A;
        --warning-amber: #D97706;
        --danger-red: #DC2626;
        --radius-lg: 14px;
        --radius-md: 10px;
        --radius-sm: 6px;
        --shadow-soft: 0 1px 3px rgba(17, 24, 39, 0.06), 0 4px 16px -4px rgba(17, 24, 39, 0.08);
        --shadow-elevated: 0 8px 24px -6px rgba(37, 99, 235, 0.18), 0 2px 6px -1px rgba(17, 24, 39, 0.06);
    }

    .stApp {
        background-color: var(--bg-main);
        color: var(--text-main);
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }

    /* ============ HEADER & TOOLBAR: Minimal, keep expand button ============ */
    /* Header transparan, tinggi minimal; toolbar hanya tombol expand sidebar */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: auto !important;
        min-height: 0 !important;
        z-index: 1000 !important;
    }

    div[data-testid="stToolbar"] {
        background: transparent !important;
    }

    /* Sembunyikan elemen toolbar kecuali tombol expand sidebar */
    div[data-testid="stToolbar"] > div > div:not(:has([data-testid="stExpandSidebarButton"])) {
        display: none !important;
    }

    /* Tombol expand sidebar tampil rapi */
    header [data-testid="stExpandSidebarButton"],
    div[data-testid="stToolbar"] [data-testid="stExpandSidebarButton"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        margin: 0.5rem !important;
        color: var(--primary-blue) !important;
        pointer-events: auto !important;
    }

    div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* ============ CONTENT CONTAINER ============ */
    /* stMain (main[data-testid="stMain"]) memakai display:flex + align-items:center.
       Agar konten benar-benar simetris, container diberi width penuh + margin auto
       dan box-sizing border-box supaya padding tidak menambah lebar. */
    .block-container,
    .stMainBlockContainer,
    div[data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 1180px;
        margin-left: auto !important;
        margin-right: auto !important;
        box-sizing: border-box !important;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        padding-left: clamp(16px, 3vw, 32px);
        padding-right: clamp(16px, 3vw, 32px);
    }

    /* Ensure main content area has no extra top margin */
    .stAppViewBlockContainer {
        padding-top: 0 !important;
    }

    /* Hide the empty decoration div that Streamlit sometimes renders */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        padding-top: 0 !important;
    }

    /* ============ SIDEBAR ============ */
    /* Lebar sidebar dikelola berdasarkan atribut data-collapsed milik Streamlit
       agar saat ditutup sidebar benar-benar 0px dan konten utama full width. */
    section[data-testid="stSidebar"] {
        background-color: var(--deep-navy) !important;
        border-right: 1px solid #1E3A8A !important;
    }

    section[data-testid="stSidebar"] > div {
        width: 100% !important;
    }

    section[data-testid="stSidebar"][data-collapsed="true"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        border-right: none !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"][data-collapsed="false"] {
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] li,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h1,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h3,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h4 {
        color: #CBD5E1 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] strong {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h4 {
        color: #F1F5F9 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0.2rem 0 !important;
    }

    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {
        color: #94A3B8 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #1E3A8A !important;
        margin: 0.9rem 0 !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid #334155 !important;
        color: #E2E8F0 !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.12) !important;
        border-color: #475569 !important;
        color: #FFFFFF !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-bottom: 0.85rem;
    }

    .sidebar-brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 9px;
        background: linear-gradient(135deg, var(--primary-blue), var(--sky-blue));
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        flex-shrink: 0;
        box-shadow: 0 4px 12px -2px rgba(14, 165, 233, 0.5);
    }

    .sidebar-brand-name {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: #FFFFFF;
        line-height: 1.2;
    }

    .sidebar-brand-sub {
        font-size: 0.68rem;
        color: #7DD3FC;
        font-weight: 600;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .sidebar-section-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: #93C5FD;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin: 0.2rem 0 0.4rem 0;
        font-family: 'Space Grotesk', sans-serif;
    }

    .sidebar-principle {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #1E3A8A;
        border-radius: 8px;
        padding: 0.6rem 0.75rem;
        margin-bottom: 0.5rem;
    }

    .sidebar-principle-title {
        color: #E2E8F0;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 0.15rem;
    }

    .sidebar-principle-text {
        color: #94A3B8;
        font-size: 0.73rem;
        line-height: 1.4;
    }

    .sidebar-category-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0;
    }

    .sidebar-category-code {
        font-size: 0.62rem;
        font-weight: 700;
        color: #7DD3FC;
        background: rgba(14, 165, 233, 0.15);
        border: 1px solid rgba(14, 165, 233, 0.35);
        border-radius: 4px;
        padding: 0.1rem 0.35rem;
        font-family: 'Space Grotesk', sans-serif;
        flex-shrink: 0;
    }

    .sidebar-category-name {
        font-size: 0.8rem;
        color: #CBD5E1;
        line-height: 1.3;
    }

    .sidebar-footer {
        color: #64748B;
        font-size: 0.7rem;
        text-align: center;
        line-height: 1.4;
    }

    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif !important;
        color: var(--midnight-navy);
        letter-spacing: -0.02em;
        font-weight: 700;
    }

    /* Hero / Header Container */
    .hero-container {
        background: linear-gradient(135deg, #172554 0%, #1E3A8A 100%);
        border: 1px solid #1E40AF;
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.75rem;
        margin-bottom: 0.9rem;
        color: #F8FAFC;
        position: relative;
        overflow: visible;
        box-shadow: 0 10px 30px -8px rgba(23, 37, 84, 0.45);
    }

    .hero-container::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-top-left-radius: var(--radius-lg);
        border-top-right-radius: var(--radius-lg);
        background: linear-gradient(90deg, var(--sky-blue), var(--electric-cyan), var(--teal-accent));
    }

    .hero-kicker-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.45rem;
    }

    .status-pulse-dot {
        width: 7px;
        height: 7px;
        background-color: #22D3EE;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #22D3EE;
    }

    .hero-kicker {
        color: #7DD3FC;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        font-family: 'Space Grotesk', monospace;
    }

    .hero-title {
        color: #FFFFFF;
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.25;
        margin: 0.15rem 0 0.4rem 0;
        font-family: 'Space Grotesk', sans-serif;
    }

    .hero-subtitle {
        color: #BFDBFE;
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0;
        max-width: 760px;
    }

    .hero-badge-row {
        margin-top: 0.85rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        align-items: center;
    }

    .hero-badge-row .badge {
        margin: 0;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(125, 211, 252, 0.4);
        color: #DBEAFE;
        font-size: 0.66rem;
        padding: 0.2rem 0.55rem;
    }

    /* Badges & Tags */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 9999px;
        border: 1px solid;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.22rem 0.65rem;
        margin: 0.3rem 0.3rem 0 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-family: 'Space Grotesk', sans-serif;
    }

    .badge-blue { color: #2563EB; background: #EFF6FF; border-color: #BFDBFE; }
    .badge-cyan { color: #0891B2; background: #ECFEFF; border-color: #A5F3FC; }
    .badge-green { color: #16A34A; background: #F0FDF4; border-color: #BBF7D0; }
    .badge-amber { color: #D97706; background: #FFFBEB; border-color: #FDE68A; }
    .badge-red { color: #DC2626; background: #FEF2F2; border-color: #FECACA; }
    .badge-slate { color: #475569; background: #F8FAFC; border-color: #E2E8F0; }

    /* Tech Cards */
    .tech-card {
        background: var(--surface-white);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.35rem;
        margin-bottom: 1.1rem;
        box-shadow: var(--shadow-soft);
    }

    /* Category Cards */
    .category-card {
        background: var(--surface-white);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem 1.05rem;
        min-height: 118px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        box-shadow: var(--shadow-soft);
        border-top: 3px solid var(--sky-blue);
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
    }

    .category-card:hover {
        box-shadow: 0 6px 20px -6px rgba(37, 99, 235, 0.22);
        border-color: #BFDBFE;
    }

    .category-card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.55rem;
    }

    .category-icon {
        font-size: 0.64rem;
        font-weight: 700;
        color: var(--primary-blue);
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 5px;
        padding: 0.18rem 0.42rem;
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0.03em;
        flex-shrink: 0;
    }

    .category-name {
        font-size: 0.88rem;
        font-weight: 700;
        color: var(--midnight-navy);
        font-family: 'Space Grotesk', sans-serif;
        line-height: 1.25;
    }

    .category-desc {
        color: var(--text-secondary);
        font-size: 0.76rem;
        line-height: 1.45;
        margin: 0;
    }

    /* Centerpiece: UCS Recommended Test Card */
    .ucs-featured-card {
        background: #FFFFFF;
        border: 1.5px solid #BFDBFE;
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1.3rem;
        box-shadow: var(--shadow-elevated);
        position: relative;
    }

    .ucs-featured-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3.5px;
        background: linear-gradient(90deg, var(--primary-blue), var(--electric-cyan));
        border-top-left-radius: var(--radius-lg);
        border-top-right-radius: var(--radius-lg);
    }

    .ucs-tagline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .ucs-rationale-box {
        background: #F8FAFC;
        border: 1px dashed #CBD5E1;
        border-radius: var(--radius-sm);
        padding: 0.85rem 1rem;
        margin: 0.9rem 0;
        font-size: 0.84rem;
        color: #334155;
        line-height: 1.55;
    }

    /* Metric Cards Redesign */
    div[data-testid="stMetric"] {
        background: var(--surface-white);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.95rem 1.1rem;
        box-shadow: var(--shadow-soft);
        min-height: 84px;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: #475569 !important;
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-family: 'Space Grotesk', sans-serif !important;
        opacity: 1 !important;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        color: #172033 !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', 'Space Grotesk', monospace !important;
        opacity: 1 !important;
    }

    /* Evidence Panels */
    .evidence-card {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.15rem;
        height: 100%;
        box-shadow: var(--shadow-soft);
    }

    .evidence-card-header {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-family: 'Space Grotesk', sans-serif;
    }

    .evidence-item {
        font-size: 0.88rem;
        color: #1E293B;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.35rem;
        border-radius: var(--radius-sm);
        line-height: 1.45;
        display: flex;
        align-items: flex-start;
        gap: 0.45rem;
    }

    .evidence-item-support {
        background: #F0FDF4;
        border-left: 3px solid var(--success-green);
        color: #14532D;
    }

    .evidence-item-contra {
        background: #FEF2F2;
        border-left: 3px solid var(--danger-red);
        color: #7F1D1D;
    }

    .evidence-item-pending {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #334155;
    }

    .evidence-empty {
        color: #94A3B8;
        font-size: 0.82rem;
        font-style: italic;
        padding: 0.3rem 0;
    }

    /* Result Banners */
    .result-conclusive {
        background: linear-gradient(180deg, #F0FDF4 0%, #FFFFFF 100%);
        border: 1.5px solid #86EFAC;
        border-radius: var(--radius-lg);
        padding: 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 25px -4px rgba(22, 163, 74, 0.1);
    }

    .result-inconclusive {
        background: linear-gradient(180deg, #FFFBEB 0%, #FFFFFF 100%);
        border: 1.5px solid #FDE68A;
        border-radius: var(--radius-lg);
        padding: 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 25px -4px rgba(217, 119, 6, 0.1);
    }

    .result-in-progress {
        background: linear-gradient(180deg, #EFF6FF 0%, #FFFFFF 100%);
        border: 1.5px solid #BFDBFE;
        border-radius: var(--radius-lg);
        padding: 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 25px -4px rgba(37, 99, 235, 0.1);
    }

    /* Recommendations Checklist */
    .rec-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: var(--radius-sm);
        padding: 0.9rem 1.1rem;
        margin-top: 0.8rem;
    }

    .rec-item {
        font-size: 0.9rem;
        color: #1E293B;
        padding: 0.35rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
    }

    .rec-item-bullet {
        color: var(--primary-blue);
        font-weight: 700;
    }

    /* Disclaimer / Simulation Notice */
    .sim-alert {
        background: #EFF6FF;
        border: 1px solid #DBEAFE;
        border-left: 3px solid var(--sky-blue);
        border-radius: var(--radius-sm);
        padding: 0.6rem 0.9rem;
        font-size: 0.82rem;
        color: #1E3A8A;
        line-height: 1.5;
        margin-bottom: 1.4rem;
    }

    .sim-alert strong {
        color: #1E40AF;
        font-weight: 700;
    }

    /* How It Works Steps */
    .step-card {
        background: var(--surface-white);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.15rem 1.2rem;
        height: 100%;
        min-height: 132px;
        box-shadow: var(--shadow-soft);
    }

    .step-number {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: var(--primary-blue);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 0.6rem;
    }

    .step-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--midnight-navy);
        margin: 0 0 0.3rem 0;
    }

    .step-desc {
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }

    /* Streamlit Form Styling */
    div[data-testid="stForm"] {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        background: #FFFFFF !important;
        padding: 1.25rem !important;
    }

    /* Button Enhancements */
    button[kind="primary"] {
        background-color: var(--primary-blue) !important;
        border: 1.5px solid var(--primary-blue) !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.25rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2) !important;
    }

    button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    }

    button[kind="primary"]:focus-visible {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.35) !important;
    }

    button[kind="primary"]:disabled {
        background-color: #94A3B8 !important;
        border-color: #94A3B8 !important;
        color: #F1F5F9 !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        opacity: 0.7 !important;
    }

    /* Expander Styling */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
        box-shadow: var(--shadow-soft) !important;
    }

    div[data-testid="stExpander"] details summary {
        color: #172033 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.75rem 1rem !important;
    }

    div[data-testid="stExpander"] details summary:hover {
        color: var(--primary-blue) !important;
    }

    /* Alert / Callout Modernization */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        border-width: 1px !important;
        border-style: solid !important;
        padding: 0.85rem 1.1rem !important;
    }

    /* Chips */
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.4rem 0 0.8rem 0;
    }

    .chip {
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        color: #334155;
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.25rem 0.65rem;
    }

    /* ============================================================
       RESPONSIVE LAYOUT — Modern Tech Diagnostics
       ============================================================ */
    @media (min-width: 1440px) {
        .block-container,
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"] {
            max-width: 1320px !important;
            padding-top: 2rem !important;
        }
        section[data-testid="stSidebar"][data-collapsed="false"] {
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
        }
    }

    @media (max-width: 1023px) {
        /* Container: gunakan hampir seluruh lebar area kerja, padding simetris */
        .block-container,
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding-left: clamp(16px, 3vw, 24px) !important;
            padding-right: clamp(16px, 3vw, 24px) !important;
        }
    }

    /* Tablet: sidebar lebih ringkas bila dibuka */
    @media (min-width: 768px) and (max-width: 1023px) {
        section[data-testid="stSidebar"][data-collapsed="false"] {
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
        }
    }

    /* Mobile: drawer overlay, tidak memakan lebar konten */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"][data-collapsed="false"] {
            width: min(86vw, 320px) !important;
            min-width: min(86vw, 320px) !important;
            max-width: min(86vw, 320px) !important;
        }
    }

    /* Wrap columns and stack on small screens */
    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.75rem !important; }
    
    /* Mobile: stack everything */
    @media (max-width: 767px) {
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 100% !important;
            width: 100% !important;
        }
        /* Metrics row: 2-up on mobile, then 1-up at small screen */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div[data-testid="stColumn"] {
            flex: 1 1 calc(50% - 0.5rem) !important;
            width: calc(50% - 0.5rem) !important;
        }
    }
    @media (max-width: 479px) {
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div[data-testid="stColumn"] {
            flex: 1 1 100% !important;
            width: 100% !important;
        }
        .hero-title { font-size: 1.25rem !important; }
    }

    /* Tablet/Laptop: 2-up columns */
    @media (min-width: 768px) and (max-width: 1023px) {
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 calc(50% - 0.5rem) !important;
            width: calc(50% - 0.5rem) !important;
        }
    }

    /* Responsive Typography */
    .hero-title { font-size: clamp(1.2rem, 3vw, 1.8rem) !important; }
    div[data-testid="stMetricValue"] { font-size: clamp(1.1rem, 2.5vw, 1.7rem) !important; }
    .block-container h1 { font-size: clamp(1.4rem, 2.6vw, 1.9rem) !important; }
    .block-container h2 { font-size: clamp(1.2rem, 2vw, 1.5rem) !important; }

    /* Radio grid */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)) !important;
        gap: 0.6rem !important;
    }

    /* Radio Button & Form Elements Fix - High Contrast Card Selection */
    div[data-testid="stRadio"] > div {
        gap: 0.6rem !important;
    }

    div[data-testid="stRadio"] label {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: var(--radius-md) !important;
        padding: 0.85rem 1.1rem !important;
        margin-bottom: 0.4rem !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-testid="stRadio"] label:hover {
        border-color: var(--primary-blue) !important;
        background-color: #F8FAFC !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        border-color: var(--primary-blue) !important;
        background-color: #EFF6FF !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
    }

    div[data-testid="stRadio"] label:has(input:focus-visible) {
        outline: none !important;
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25) !important;
    }

    div[data-testid="stRadio"] label:has(input:disabled) {
        opacity: 0.6 !important;
        cursor: not-allowed !important;
        background-color: #F1F5F9 !important;
    }

    div[data-testid="stRadio"] span[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label div {
        color: #172033 !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        margin: 0 !important;
        opacity: 1 !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) span[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #1D4ED8 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stRadio"] input[type="radio"] {
        accent-color: var(--primary-blue) !important;
        width: 1.15rem !important;
        height: 1.15rem !important;
        margin-right: 0.75rem !important;
        cursor: pointer !important;
    }

    /* Checkbox Fix */
    div[data-testid="stCheckbox"] label {
        color: #172033 !important;
        font-weight: 500 !important;
        cursor: pointer !important;
    }

    div[data-testid="stCheckbox"] span[data-testid="stMarkdownContainer"] p {
        color: #172033 !important;
        font-size: 0.9rem !important;
        opacity: 1 !important;
    }

    div[data-testid="stCheckbox"] input[type="checkbox"] {
        accent-color: var(--primary-blue) !important;
        width: 1.1rem !important;
        height: 1.1rem !important;
    }

    /* ============================================================
       SELECT / MULTISELECT — Modern Tech Diagnostics
       Streamlit 1.67 (BaseWeb). Tema light ditetapkan di
       .streamlit/config.toml; aturan ini hanya menyelaraskan
       container, chip, dan dropdown dengan design system.
       ============================================================ */
    div[data-testid="stMultiSelect"] div[data-baseweb="select"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }

    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: var(--radius-md) !important;
        box-shadow: none !important;
        min-height: 46px !important;
    }

    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {
        border-color: #94A3B8 !important;
    }

    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    div[data-testid="stMultiSelect"] div[data-baseweb="input"],
    div[data-testid="stMultiSelect"] div[role="combobox"],
    div[data-testid="stMultiSelect"] input,
    div[data-testid="stSelectbox"] div[role="combobox"],
    div[data-testid="stSelectbox"] input {
        background-color: transparent !important;
        color: #172033 !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        font-size: 0.88rem !important;
    }

    div[data-testid="stMultiSelect"] input::placeholder,
    div[data-testid="stSelectbox"] input::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* Placeholder text node in select */
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div {
        color: #172033 !important;
    }

    /* Selected multiselect chips — biru muda, bukan merah */
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #DBEAFE !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 6px !important;
        color: #1D4ED8 !important;
        height: auto !important;
        padding: 2px 4px 2px 8px !important;
    }

    div[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] div {
        color: #1D4ED8 !important;
        font-weight: 500 !important;
        background-color: transparent !important;
    }

    /* Tombol hapus chip */
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] button,
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        color: #1D4ED8 !important;
        fill: #1D4ED8 !important;
        opacity: 0.85 !important;
    }

    div[data-testid="stMultiSelect"] [data-baseweb="tag"] button:hover svg {
        opacity: 1 !important;
    }

    div[data-baseweb="select"] svg {
        color: #64748B !important;
    }

    /* Dropdown menu */
    div[data-baseweb="popover"] ul[role="listbox"],
    div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 8px 24px -6px rgba(17, 24, 39, 0.18) !important;
    }

    div[data-baseweb="popover"] li {
        background-color: #FFFFFF !important;
        color: #172033 !important;
        font-size: 0.88rem !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: #EFF6FF !important;
        color: #1E3A8A !important;
    }

    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        font-weight: 600 !important;
        border-left: 3px solid var(--primary-blue) !important;
    }

    /* Selectbox label above field */
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stMultiSelect"] label p {
        color: #172033 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    /* Text Input / Number Input Fix */
    input[type="text"], input[type="number"], input[type="password"], textarea {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: var(--radius-md) !important;
        color: #1E293B !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.9rem !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    }

    input[type="text"]:hover, input[type="number"]:hover, textarea:hover {
        border-color: #94A3B8 !important;
    }

    input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        outline: none !important;
    }

    /* Button Secondary */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #172033 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.25rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(17, 24, 39, 0.05) !important;
    }

    button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: var(--primary-blue) !important;
        color: var(--primary-blue) !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12) !important;
    }

    button[kind="secondary"]:focus-visible {
        outline: none !important;
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25) !important;
    }

    button[kind="secondary"]:disabled {
        background-color: #F8FAFC !important;
        border-color: #E2E8F0 !important;
        color: #94A3B8 !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        opacity: 0.7 !important;
    }

    /* Test Result Form Container */
    .test-form-container {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin-top: 1rem;
    }

    .test-form-header {
        font-size: 0.8rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Progress Indicator */
    .progress-track {
        display: flex;
        align-items: flex-start;
        gap: 0;
        margin: 1rem 0;
    }
    .progress-step {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }
    .progress-step:not(:last-child)::after {
        content: "";
        position: absolute;
        top: 14px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: var(--border-color);
        z-index: 0;
    }
    .progress-step.done:not(:last-child)::after {
        background: var(--primary-blue);
    }
    .progress-dot {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: 2px solid var(--border-color);
        background: var(--surface-white);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        color: var(--text-secondary);
        z-index: 1;
        transition: all 0.2s ease;
    }
    .progress-step.done .progress-dot {
        background: var(--primary-blue);
        border-color: var(--primary-blue);
        color: #FFFFFF;
    }
    .progress-step.active .progress-dot {
        background: var(--surface-white);
        border-color: var(--primary-blue);
        color: var(--primary-blue);
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
    }
    .progress-label {
        margin-top: 0.4rem;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-align: center;
        font-family: 'Space Grotesk', sans-serif;
    }
    .progress-step.done .progress-label,
    .progress-step.active .progress-label {
        color: var(--primary-blue);
    }
    .progress-sub {
        font-size: 0.62rem;
        color: var(--text-secondary);
        text-align: center;
        margin-top: 0.1rem;
        font-weight: 500;
    }

    /* Custom Symptom Card */
    .custom-symptom-card {
        background: #F8FAFC;
        border: 1px solid #BFDBFE;
        border-left: 4px solid var(--primary-blue);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin: 0.75rem 0;
    }
    .custom-symptom-kicker {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--primary-blue);
    }
    .custom-symptom-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: var(--deep-navy);
        margin: 0.15rem 0 0.35rem;
        line-height: 1.35;
    }
    .custom-symptom-desc {
        font-size: 0.83rem;
        color: #334155;
        margin-bottom: 0.25rem;
        line-height: 1.5;
    }
    .custom-symptom-note {
        margin-top: 0.55rem;
        font-size: 0.78rem;
        line-height: 1.5;
        color: #92400E;
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 6px;
        padding: 0.45rem 0.6rem;
    }

    /* Contextual Feedback */
    .contextual-feedback {
        border-radius: var(--radius-md);
        padding: 0.9rem 1rem;
        margin: 0.5rem 0 1rem;
        border-left: 4px solid;
        font-size: 0.88rem;
        line-height: 1.55;
    }
    .contextual-feedback.blue { border-color: var(--primary-blue); background: #EFF6FF; }
    .contextual-feedback.green { border-color: var(--success-green); background: #F0FDF4; }
    .contextual-feedback.amber { border-color: var(--warning-amber); background: #FFFBEB; }
    .contextual-feedback.slate { border-color: var(--border-color); background: #F8FAFC; }
    .contextual-feedback .feedback-title {
        font-weight: 700;
        margin-bottom: 0.25rem;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Free Text Panel */
    .free-text-panel {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .free-text-result {
        margin-top: 0.75rem;
        padding: 0.75rem;
        background: #F8FAFC;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
    }
    .free-text-badge-row {
        margin: 0.5rem 0;
    }

    /* Diagnostic Instructions */
    .diag-instructions {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-top: 0.75rem;
    }
    .diag-instructions-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--primary-blue);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }
    .diag-instructions-steps {
        margin: 0;
        padding-left: 1.25rem;
        font-size: 0.84rem;
        line-height: 1.7;
    }
    .diag-instructions-steps li {
        margin-bottom: 0.35rem;
    }
    .diag-instructions-path {
        font-size: 0.78rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }
    .diag-instructions-warning {
        font-size: 0.78rem;
        color: var(--warning-amber);
        margin-top: 0.5rem;
        font-weight: 600;
    }

    /* Skip Radio Option */
    .skip-option-label {
        color: var(--text-secondary);
        font-style: italic;
    }

    /* ============ ANIMATED FEEDBACK: New Diagnosis Session ============ */
    /* Interaksi tombol: hover halus + pressed, transisi 150-250ms, tanpa bounce. */
    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {
        transition: transform 160ms ease, box-shadow 200ms ease,
                    background-color 200ms ease, border-color 200ms ease,
                    color 200ms ease;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px -6px rgba(37, 99, 235, 0.35);
    }

    div[data-testid="stButton"] > button:active,
    div[data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0) scale(0.985);
        box-shadow: 0 2px 6px -2px rgba(37, 99, 235, 0.28);
    }

    div[data-testid="stButton"] > button:focus-visible,
    div[data-testid="stFormSubmitButton"] > button:focus-visible {
        outline: 2px solid var(--primary-blue);
        outline-offset: 2px;
    }

    @keyframes nd-fade-slide-up {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes nd-scale-in {
        from { opacity: 0; transform: scale(0.55); }
        to   { opacity: 1; transform: scale(1); }
    }

    @keyframes nd-spin {
        to { transform: rotate(360deg); }
    }

    @keyframes nd-processing-out {
        from { opacity: 1; }
        to   { opacity: 0; visibility: hidden; }
    }

    /* Container feedback: slide-up ringan lalu stabil. */
    .new-diag-feedback {
        position: relative;
        margin: 0.35rem 0 1.05rem 0;
        animation: nd-fade-slide-up 380ms cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    /* Kartu sukses: aksen biru/teal, muncul fade + scale-in. */
    .new-diag-success {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.85rem 1.05rem;
        border-radius: var(--radius-lg);
        border: 1px solid rgba(20, 184, 166, 0.35);
        border-left: 4px solid var(--teal-accent);
        background: linear-gradient(180deg, rgba(14, 165, 233, 0.06), rgba(20, 184, 166, 0.05));
        box-shadow: var(--shadow-soft);
        animation: nd-scale-in 420ms cubic-bezier(0.22, 1, 0.36, 1) 600ms both;
        transform-origin: 18% 50%;
    }

    .new-diag-check {
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        margin-top: 1px;
        border-radius: 50%;
        color: #FFFFFF;
        background: linear-gradient(135deg, var(--primary-blue), var(--teal-accent));
        box-shadow: 0 4px 12px -4px rgba(20, 184, 166, 0.55);
        animation: nd-scale-in 340ms cubic-bezier(0.34, 1.56, 0.64, 1) 720ms both;
    }

    .new-diag-check svg {
        display: block;
        width: 16px;
        height: 16px;
    }

    .new-diag-success-body { min-width: 0; }

    .new-diag-success-title {
        font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--deep-navy);
        margin: 0 0 0.18rem 0;
    }

    .new-diag-success-text {
        font-size: 0.86rem;
        line-height: 1.5;
        color: var(--text-secondary);
        margin: 0;
    }

    /* Overlay fase processing: tampil singkat lalu memudar, tidak memblokir. */
    .new-diag-processing {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.85rem 1.05rem;
        border-radius: var(--radius-lg);
        border: 1px solid rgba(37, 99, 235, 0.22);
        border-left: 4px solid var(--primary-blue);
        background: rgba(241, 245, 249, 0.98);
        color: var(--deep-navy);
        font-size: 0.86rem;
        font-weight: 600;
        animation: nd-processing-out 240ms ease 620ms forwards;
    }

    .new-diag-spinner {
        flex: 0 0 auto;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid rgba(37, 99, 235, 0.25);
        border-top-color: var(--primary-blue);
        animation: nd-spin 700ms linear infinite;
    }

    /* Transisi masuk bagian identifikasi: fade-in + slide-up ringan. */
    .section-enter {
        animation: nd-fade-slide-up 400ms cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    .section-enter h3 {
        margin-top: 0.2rem;
    }

    /* Hormati preferensi pengguna yang membatasi animasi. */
    @media (prefers-reduced-motion: reduce) {
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            transition: none !important;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stButton"] > button:active,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:active {
            transform: none !important;
        }
        .new-diag-feedback,
        .new-diag-success,
        .new-diag-check,
        .new-diag-spinner,
        .section-enter {
            animation: none !important;
        }
        .new-diag-processing { display: none !important; }
        .new-diag-success {
            opacity: 1 !important;
            transform: none !important;
        }
        .new-diag-check {
            opacity: 1 !important;
            transform: none !important;
        }
    }
</style>
"""


def inject_styles() -> None:
    """Tambahkan CSS Modern Tech Diagnostics."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def badge(text: str, tone: str = "slate") -> str:
    """Membuat elemen HTML badge modern dengan label teks eksplisit."""
    return f'<span class="badge badge-{tone}">{html.escape(text)}</span>'


def render_badges(items: list[tuple[str, str]]) -> None:
    """Menampilkan kumpulan badge dalam satu baris fleksibel."""
    content = "".join(badge(text, tone) for text, tone in items)
    st.markdown(f'<div style="margin: 0.25rem 0;">{content}</div>', unsafe_allow_html=True)


def render_chips(items: list[str]) -> None:
    """Menampilkan daftar nilai sebagai chips visual yang rapi."""
    if not items:
        st.caption("Belum ada data.")
        return
    content = "".join(f'<span class="chip">{html.escape(str(item))}</span>' for item in items)
    st.markdown(f'<div class="chip-row">{content}</div>', unsafe_allow_html=True)


def evidence_label(key: str) -> str:
    """Ubah kunci bukti internal menjadi label bahasa Indonesia deskriptif."""
    return EVIDENCE_LABELS.get(key, key)


def outcome_label(outcome: str) -> str:
    """Ubah kode outcome Knowledge Base menjadi label yang mudah dipahami."""
    return OUTCOME_LABELS.get(outcome, outcome)


def category_lookup(symptoms_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Buat pemetaan category_id ke data kategori."""
    return {category["id"]: category for category in symptoms_data["categories"]}


def symptom_lookup(symptoms_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Buat pemetaan symptom_id ke data gejala."""
    return {symptom["id"]: symptom for symptom in symptoms_data["symptoms"]}


def tests_lookup(tests_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Buat pemetaan test_id ke data pemeriksaan."""
    return {test["id"]: test for test in tests_data["tests"]}


# Nilai awal seluruh state yang termasuk dalam sesi diagnosis. Didefinisikan
# terpusat agar reset tombol utama dan reset sidebar memakai aturan yang sama.
DIAGNOSIS_STATE_DEFAULTS: dict[str, Any] = {
    "diag_state": None,
    "diag_symptoms": None,
    "diag_log": [],
    "skipped_tests": [],
    "text_analysis": None,
    "bsod_validation": None,
    "pending_custom_symptom": None,
    "analysis_signature": None,
    "confirmed_analysis_signature": None,
    "custom_symptoms": {},
    "confirm_reset": False,
}

# Key tambahan untuk feedback UI setelah reset diagnosis.
# Key ini tidak dimasukkan ke DIAGNOSIS_STATE_DEFAULTS agar selamat dari clear_diagnosis_state().
NEW_DIAGNOSIS_FEEDBACK_KEY: str = "new_diagnosis_feedback"

# Key widget yang wajib dihapus agar formulir kembali ke kondisi kosong.
DIAGNOSIS_WIDGET_KEYS: tuple[str, ...] = (
    "symptom_selector",
    "free_text_input",
    "bsod_input",
)

# Prefiks key widget dinamis untuk pemilihan kategori gejala khusus.
CUSTOM_CATEGORY_KEY_PREFIX = "custom_symptom_categories_"


def clear_diagnosis_state(store: MutableMapping[str, Any]) -> None:
    """Reset seluruh state sesi diagnosis pada mapping tertentu.

    Hanya key yang berkaitan dengan sesi diagnosis yang diubah atau dihapus.
    Konfigurasi aplikasi dan key di luar daftar tetap dipertahankan.
    """
    for key, default in DIAGNOSIS_STATE_DEFAULTS.items():
        if isinstance(default, list):
            store[key] = list(default)
        elif isinstance(default, dict):
            store[key] = dict(default)
        else:
            store[key] = default

    for key in list(store.keys()):
        if key in DIAGNOSIS_WIDGET_KEYS or str(key).startswith(CUSTOM_CATEGORY_KEY_PREFIX):
            del store[key]


def reset_diagnosis_session() -> None:
    """Reset terpusat sesi diagnosis (dipakai tombol utama & kontrol sidebar)."""
    clear_diagnosis_state(st.session_state)


def start_new_diagnosis() -> None:
    """Reset sesi diagnosis lalu tandai feedback sukses untuk ditampilkan.

    Flag feedback disimpan pada key UI terpisah (``NEW_DIAGNOSIS_FEEDBACK_KEY``)
    sehingga tidak termasuk state diagnosis dan tidak memengaruhi algoritma UCS.
    """
    clear_diagnosis_state(st.session_state)
    st.session_state[NEW_DIAGNOSIS_FEEDBACK_KEY] = {"status": "ready"}


def consume_new_diagnosis_feedback() -> bool:
    """Ambil dan konsumsi flag feedback agar hanya tampil satu kali.

    Returns:
        ``True`` jika feedback baru saja dipicu pada run sebelumnya.
    """
    feedback = st.session_state.get(NEW_DIAGNOSIS_FEEDBACK_KEY)
    if not feedback:
        return False
    st.session_state[NEW_DIAGNOSIS_FEEDBACK_KEY] = None
    return True


def render_new_diagnosis_feedback() -> None:
    """Tampilkan feedback animasi sesi diagnosis baru (processing -> sukses).

    HTML dibangun sebagai satu string tanpa baris kosong dan tanpa indentasi
    awal agar Streamlit tidak merendernya sebagai teks mentah.
    """
    html_success = (
        '<div class="new-diag-feedback" role="status" aria-live="polite">'
        '<div class="new-diag-success">'
        '<span class="new-diag-check" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>'
        '</span>'
        '<div class="new-diag-success-body">'
        '<div class="new-diag-success-title">Sesi Diagnosis Baru Siap</div>'
        '<div class="new-diag-success-text">Semua data diagnosis sebelumnya telah '
        'dibersihkan. Silakan identifikasi masalah komputer yang ingin diperiksa.</div>'
        '</div>'
        '</div>'
        '<div class="new-diag-processing" aria-hidden="true">'
        '<span class="new-diag-spinner"></span>'
        '<span>Menyiapkan sesi diagnosis baru...</span>'
        '</div>'
        '</div>'
    )
    st.markdown(html_success, unsafe_allow_html=True)


def request_reset() -> None:
    """Minta konfirmasi 2-tahap sebelum mereset sesi aktif dari sidebar."""
    st.session_state.confirm_reset = True


def render_sidebar(
    categories: dict[str, dict[str, Any]],
    has_active_session: bool,
) -> None:
    """Tampilkan panel navigasi samping dengan identitas sistem dan kontrol sesi."""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">TD</div>
            <div>
                <div class="sidebar-brand-name">Tech Diagnostics</div>
                <div class="sidebar-brand-sub">Classical AI Engine</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "Prototipe diagnosis kerusakan komputer Windows berbasis "
        "**Uniform Cost Search (UCS)** dengan bobot biaya relatif."
    )
    render_badges([("Classical AI", "blue"), ("UCS + heapq", "cyan"), ("Simulasi", "slate")])

    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="sidebar-section-title">Prinsip Kerja UCS</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
        <div class="sidebar-principle">
            <div class="sidebar-principle-title">Jalur Biaya Minimum</div>
            <div class="sidebar-principle-text">Memilih urutan pemeriksaan dengan total cost kumulatif terendah.</div>
        </div>
        <div class="sidebar-principle">
            <div class="sidebar-principle-title">Cost Relatif (1-5)</div>
            <div class="sidebar-principle-text">Merefleksikan tingkat disrupsi tiap uji diagnostik.</div>
        </div>
        <div class="sidebar-principle">
            <div class="sidebar-principle-title">Bukan Machine Learning</div>
            <div class="sidebar-principle-text">Inferensi deterministik via priority queue min-heap.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="sidebar-section-title">Kategori Masalah</div>',
        unsafe_allow_html=True,
    )
    cat_rows = "".join(
        f"""
        <div class="sidebar-category-row">
            <span class="sidebar-category-code">{CATEGORY_ICONS.get(cat_id, '-')}</span>
            <span class="sidebar-category-name">{html.escape(cat['name'])}</span>
        </div>
        """
        for cat_id, cat in categories.items()
    )
    st.sidebar.markdown(cat_rows, unsafe_allow_html=True)

    if has_active_session:
        st.sidebar.divider()
        st.sidebar.markdown(
            '<div class="sidebar-section-title">Kontrol Sesi</div>',
            unsafe_allow_html=True,
        )
        if not st.session_state.get("confirm_reset"):
            st.sidebar.button(
                "Mulai Diagnosis Baru",
                type="secondary",
                use_container_width=True,
                on_click=request_reset,
            )
        else:
            st.sidebar.warning(
                "Konfirmasi: Sesi aktif dan riwayat pemeriksaan akan dihapus permanen."
            )
            col_yes, col_no = st.sidebar.columns(2)
            col_yes.button(
                "Ya, Reset",
                type="primary",
                use_container_width=True,
                on_click=reset_diagnosis_session,
            )
            if col_no.button("Batal", use_container_width=True):
                st.session_state.confirm_reset = False
                st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="sidebar-footer">Tugas Akhir UAS Artificial Intelligence<br>2026</div>',
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Tampilkan Hero Header bertema Modern Tech Diagnostics."""
    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-kicker-row">
                <span class="status-pulse-dot"></span>
                <span class="hero-kicker">Diagnostic System Ready &middot; Classical AI</span>
            </div>
            <div class="hero-title">{html.escape(APP_NAME)}</div>
            <p class="hero-subtitle">{html.escape(APP_DESCRIPTION)}</p>
            <div class="hero-badge-row">
                <span class="badge">Uniform Cost Search</span>
                <span class="badge">Classical AI</span>
                <span class="badge">Windows Troubleshooting</span>
                <span class="badge">Simulasi Basis Pengetahuan</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sim-alert"><strong>Catatan Simulasi:</strong> Sistem beroperasi pada basis pengetahuan simulasi terstruktur. Tidak ada perintah eksekusi otomatis atau modifikasi langsung terhadap sistem operasi Windows Anda.</div>',
        unsafe_allow_html=True,
    )


def render_start_section(
    symptoms: dict[str, dict[str, Any]],
    categories: dict[str, dict[str, Any]],
    tests: dict[str, dict[str, Any]],
    has_active_session: bool,
    animate_enter: bool = False,
) -> None:
    """Bagian A: Pemilihan gejala awal dan kartu kategori masalah."""
    heading = "A. Identifikasi &amp; Pemilihan Gejala Awal"
    if animate_enter:
        st.markdown(f'<div class="section-enter"><h3>{heading}</h3></div>', unsafe_allow_html=True)
    else:
        st.markdown("### A. Identifikasi & Pemilihan Gejala Awal")
    st.markdown(
        "Pilih indikasi atau gejala kerusakan yang terjadi pada komputer Windows. "
        "Sistem akan memetakan gejala ke kategori masalah terkait dan merumuskan lintasan pemeriksaan optimal."
    )

    # 4 Kartu Kategori Masalah
    cat_cols = st.columns(4)
    cat_keys = ["driver_software", "overheating", "storage_disk", "ram_memory"]
    for idx, cat_id in enumerate(cat_keys):
        cat = categories[cat_id]
        icon = CATEGORY_ICONS.get(cat_id, "")
        subtitle = CATEGORY_SUBTITLES.get(cat_id, cat["description"])
        with cat_cols[idx]:
            st.markdown(
                f"""
                <div class="category-card">
                    <div class="category-card-header">
                        <span class="category-icon">{icon}</span>
                        <div class="category-name">{html.escape(cat['name'])}</div>
                    </div>
                    <p class="category-desc">{html.escape(subtitle)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # Panel deskripsi bebas (hanya sebelum sesi dimulai)
    if not has_active_session:
        render_free_text_panel(symptoms, categories, tests)

    # Gabungkan gejala bawaan + gejala tambahan terkonfirmasi untuk dropdown
    custom_symptoms: dict[str, dict[str, Any]] = st.session_state.get("custom_symptoms") or {}
    all_selectable: dict[str, dict[str, Any]] = dict(symptoms)
    all_selectable.update(custom_symptoms)

    # Form Pemilihan Gejala
    with st.container(border=True):
        st.markdown("**Pilih Gejala yang Teramati**")
        symptom_labels = {}
        for symptom_id, symptom in all_selectable.items():
            rel = symptom.get("related_categories") or ["driver_software"]
            primary_cat = rel[0] if rel else "driver_software"
            cat_display = categories.get(primary_cat, {}).get("name", primary_cat)
            prefix = "[TAMBAHAN]" if symptom.get("source") == "user_report" else CATEGORY_ICONS.get(primary_cat, "-")
            symptom_labels[symptom_id] = f"{prefix} - {symptom['name']} ({cat_display})"

        selected_ids = st.multiselect(
            "Daftar Gejala Teramati (Dapat memilih lebih dari satu):",
            options=list(all_selectable.keys()),
            format_func=lambda s_id: symptom_labels[s_id],
            key="symptom_selector",
            placeholder="Pilih satu atau beberapa gejala...",
            help="Pilih semua gejala yang relevan dengan kondisi komputer saat ini.",
            label_visibility="collapsed",
        )

        if selected_ids:
            custom_count = sum(1 for s in selected_ids if s in custom_symptoms)
            note = f" ({custom_count} gejala tambahan dari laporan Anda)" if custom_count else ""
            st.caption(f"Tervalidasi: {len(selected_ids)} gejala dipilih dari {len(all_selectable)} gejala tersedia{note}.")
        else:
            st.caption(f"Belum ada gejala dipilih. Tersedia {len(all_selectable)} gejala dari empat kategori masalah.")

        if not has_active_session:
            col_btn, _ = st.columns([1, 2])
            with col_btn:
                btn_start = st.button(
                    "Mulai Sesi Diagnosis",
                    type="primary",
                    disabled=not selected_ids,
                    use_container_width=True,
                )
            if btn_start:
                st.session_state.diag_state = initialize_diagnosis(
                    selected_ids, custom_symptoms=custom_symptoms or None
                )
                st.session_state.diag_symptoms = tuple(sorted(selected_ids))
                st.session_state.diag_log = []
                st.session_state.confirm_reset = False
                st.rerun()

            if not selected_ids:
                st.caption("Pilih minimal satu gejala di atas untuk mengaktifkan tombol diagnosis.")
        else:
            st.info(
                "Sesi diagnosis sedang berlangsung. Untuk memulai sesi baru, gunakan tombol "
                "**Mulai Diagnosis Baru** pada bagian hasil diagnosis (atau kontrol sesi di sidebar)."
            )


def render_active_categories(state: DiagnosisState, categories: dict[str, dict[str, Any]]) -> None:
    """Tampilkan kategori yang masih berpeluang dengan indikator visual."""
    if not state.possible_categories:
        st.warning("Seluruh kategori telah tereliminasi oleh bukti bertentangan.")
        return

    st.markdown('<div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">Kategori Dalam Investigasi:</div>', unsafe_allow_html=True)
    cols = st.columns(len(state.possible_categories))
    for idx, cat_id in enumerate(sorted(state.possible_categories)):
        cat = categories[cat_id]
        icon = CATEGORY_ICONS.get(cat_id, "")
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 0.55rem 0.75rem; font-size: 0.84rem;">
                    <strong>{icon} {html.escape(cat['name'])}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.write("")


def render_evidence(
    state: DiagnosisState,
    tests: dict[str, dict[str, Any]],
    categories: dict[str, dict[str, Any]],
) -> None:
    """Bagian C: Kartu visual bukti pendukung, bertentangan, dan uji tertunda."""
    st.markdown("### C. Analisis Status Bukti Diagnostik")
    sufficiency = get_evidence_sufficiency(state)
    label, tone, explanation = SUFFICIENCY_LABELS[sufficiency]

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
            <span style="font-size: 0.88rem; font-weight: 600; color: #475569;">Kecukupan Bukti:</span>
            {badge(label, tone)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(explanation)

    col_support, col_contradict, col_pending = st.columns(3)

    # 1. Bukti Pendukung — satu blok HTML self-contained
    support_items = "".join(
        f'<div class="evidence-item evidence-item-support"><span>[V]</span><span>{html.escape(evidence_label(key))}</span></div>'
        for key in sorted(state.supporting_evidence)
    ) or '<div class="evidence-empty">Belum ada bukti pendukung yang terkonfirmasi.</div>'
    with col_support:
        st.markdown(
            f"""
            <div class="evidence-card">
                <div class="evidence-card-header" style="color: #15803D;">
                    <span>[V]</span> Bukti Pendukung Terkonfirmasi
                </div>
                {support_items}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Bukti Bertentangan — satu blok HTML self-contained
    contra_items = "".join(
        f'<div class="evidence-item evidence-item-contra"><span>[-]</span><span>{html.escape(evidence_label(key))}</span></div>'
        for key in sorted(state.contradicting_evidence)
    ) or '<div class="evidence-empty">Tidak ada bukti pertentangan.</div>'
    with col_contradict:
        st.markdown(
            f"""
            <div class="evidence-card">
                <div class="evidence-card-header" style="color: #B91C1C;">
                    <span>[-]</span> Bukti Bertentangan (Dieliminasi)
                </div>
                {contra_items}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Pemeriksaan Tertunda — satu blok HTML self-contained
    pending = get_pending_tests(state)
    if pending:
        pending_items = "".join(
            f"""
            <div class="evidence-item evidence-item-pending">
                <div>
                    <div><strong>{html.escape(test['name'])}</strong></div>
                    <div style="font-size: 0.74rem; color: #64748B;">{html.escape(categories[test['category']]['name'])} · Cost: {test['cost']}</div>
                </div>
            </div>
            """
            for test in pending
        )
    else:
        pending_items = '<div class="evidence-empty">Semua pemeriksaan relevan telah dijalankan.</div>'
    with col_pending:
        st.markdown(
            f"""
            <div class="evidence-card">
                <div class="evidence-card-header" style="color: #0369A1;">
                    <span></span> Pemeriksaan Belum Dilakukan
                </div>
                {pending_items}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_performed_tests_table(
    state: DiagnosisState,
    tests: dict[str, dict[str, Any]],
) -> None:
    """Tampilkan tabel pemeriksaan yang sudah dilakukan secara rapi."""
    if not state.test_results:
        st.caption("Belum ada pemeriksaan yang diselesaikan.")
        return

    rows = []
    for test_id, outcome in sorted(state.test_results):
        test = tests[test_id]
        rows.append(
            {
                "Pemeriksaan": test["name"],
                "Kategori Uji": test["category"].replace("_", " ").title(),
                "Hasil Observasi": outcome_label(outcome),
                "Bobot Cost": test["cost"],
            }
        )
    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_result(
    state: DiagnosisState,
    evaluation: dict[str, Any],
    tests: dict[str, dict[str, Any]],
    categories: dict[str, dict[str, Any]],
) -> None:
    """Bagian D: Tampilan hasil diagnosis konklusif, inkonklusif, atau in-progress."""
    st.markdown("### D. Hasil Kesimpulan Diagnosis")
    status = evaluation["status"]

    if status == "conclusive":
        category_name = evaluation["category_name"]
        rec_html = "".join(
            f'<div class="rec-item"><span class="rec-item-bullet">-></span><span>{html.escape(rec)}</span></div>'
            for rec in evaluation["recommendations"]
        ) or '<div class="evidence-empty">Tidak ada rekomendasi tambahan.</div>'
        st.markdown(
            f"""
            <div class="result-conclusive">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 0.6rem;">
                    {badge("Diagnosis Konklusif Terkonfirmasi", "green")}
                    <span style="font-size: 0.8rem; font-weight: 700; color: #15803D; font-family: 'Space Grotesk', sans-serif;">VERIFIKASI SUKSES</span>
                </div>
                <h2 style="color: #14532D; margin: 0 0 0.5rem 0; font-size: 1.85rem;">{html.escape(category_name)}</h2>
                <p style="color: #166534; font-size: 0.95rem; margin-bottom: 1.1rem; line-height: 1.55;">
                    Sistem mengonfirmasi kategori masalah ini karena bukti pendukung minimum telah terpenuhi secara definitif dan tidak ditemukan bukti kontradiksi pada pemeriksaan yang dilakukan.
                </p>
                <div style="font-size: 0.85rem; font-weight: 700; color: #14532D; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
                    Rekomendasi Tindakan Perbaikan:
                </div>
                <div class="rec-box">{rec_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Total Biaya Kumulatif UCS", f"{evaluation['cumulative_cost']:g}")
        with col_m2:
            st.metric("Pemeriksaan Diselesaikan", len(state.test_results))

        with st.expander("Rincian Pemeriksaan & Bukti yang Mendukung"):
            st.markdown("**Bukti Pendukung:**")
            for key in sorted(evaluation["supporting_evidence"]):
                st.markdown(f"- {evidence_label(key)}")
            st.markdown("**Riwayat Pemeriksaan:**")
            render_performed_tests_table(state, tests)

        st.button(
            "Mulai Diagnosis Baru",
            type="primary",
            key="btn_reset_conclusive",
            on_click=start_new_diagnosis,
        )
        return

    if status == "inconclusive":
        rec_html = "".join(
            f'<div class="rec-item"><span class="rec-item-bullet" style="color: #D97706;">-></span><span>{html.escape(rec)}</span></div>'
            for rec in evaluation["recommendations"]
        ) or '<div class="evidence-empty">Tidak ada saran lanjutan.</div>'
        st.markdown(
            f"""
            <div class="result-inconclusive">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 0.6rem;">
                    {badge("Diagnosis Belum Konklusif", "amber")}
                    <span style="font-size: 0.8rem; font-weight: 700; color: #B45309; font-family: 'Space Grotesk', sans-serif;">BUKTI TIDAK MEMADAI</span>
                </div>
                <h2 style="color: #78350F; margin: 0 0 0.5rem 0; font-size: 1.7rem;">Tidak Ada Kategori Memenuhi Syarat</h2>
                <p style="color: #92400E; font-size: 0.95rem; margin-bottom: 1rem; line-height: 1.55;">
                    Seluruh pemeriksaan relevan pada basis pengetahuan telah dilakukan, namun tidak terdapat bukti yang cukup untuk menetapkan satu diagnosis pasti. Sesuai prinsip keandalan AI klasik, sistem <strong>tidak memaksakan kesimpulan palsu</strong>.
                </p>
                <div style="font-size: 0.85rem; font-weight: 700; color: #78350F; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
                    Saran Tindakan Lanjutan:
                </div>
                <div class="rec-box">{rec_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Total Biaya Kumulatif", f"{evaluation['cumulative_cost']:g}")
        with col_m2:
            st.metric("Pemeriksaan Diselesaikan", len(state.test_results))

        with st.expander("Rincian Log Evaluasi Inkonklusif"):
            render_performed_tests_table(state, tests)

        st.button(
            "Mulai Diagnosis Baru",
            type="primary",
            key="btn_reset_inconclusive",
            on_click=start_new_diagnosis,
        )
        return

    # Status: in_progress
    st.markdown(
        f"""
        <div class="result-in-progress">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 0.5rem;">
                {badge("Investigasi Masih Berlangsung", "blue")}
                <span style="font-size: 0.8rem; font-weight: 700; color: #1D4ED8; font-family: 'Space Grotesk', sans-serif;">LANGKAH LANJUTAN DIPERLUKAN</span>
            </div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.4rem;">
                Bukti Belum Lengkap untuk Menetapkan Diagnosis
            </div>
            <p style="color: #1E40AF; font-size: 0.9rem; line-height: 1.55; margin: 0;">
                Sistem membutuhkan luaran dari pemeriksaan yang direkomendasikan pada Bagian B di atas untuk mengonfirmasi atau mengeliminasi kategori yang masih terbuka.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history(performed_log: list[dict[str, Any]]) -> None:
    """Tampilkan riwayat langkah pemeriksaan dan lintasan UCS."""
    with st.expander("Riwayat Pemeriksaan & Lintasan Penelusuran UCS"):
        st.markdown(
            "Tabel ini merekam setiap transisi state diagnosis. UCS mengevaluasi "
            "ulang pohon pencarian setelah setiap luaran dimasukkan untuk memastikan jalur berbiaya minimal."
        )
        if not performed_log:
            st.caption("Belum ada pemeriksaan yang dicatat dalam sesi ini.")
            return

        rows = []
        for index, entry in enumerate(performed_log, start=1):
            rows.append(
                {
                    "Langkah": f"#{index}",
                    "Nama Pemeriksaan": entry["test_name"],
                    "Hasil Observasi": outcome_label(entry["outcome"]),
                    "Step Cost": entry["cost"],
                    "Cumulative Cost g(n)": f"{entry['cumulative_cost']:g}",
                }
            )
        st.dataframe(rows, hide_index=True, use_container_width=True)


def render_algorithm_explanation() -> None:
    """Kartu edukasi ilmiah mengenai prinsip kerja UCS dan batasannya."""
    with st.expander("Penjelasan Ilmiah: Mengapa Menggunakan Uniform Cost Search?"):
        st.markdown(
            """
            **Uniform Cost Search (UCS)** adalah algoritma pencarian graf berbasis biaya tanpa informasi tambahan (*uninformed search*) 
            yang menjamin ditemukannya lintasan dengan total biaya kumulatif $g(n)$ terendah (*optimal path*).
            
            - **Fungsi Biaya $g(n)$**: Setiap uji diagnostik memiliki bobot disrupsi (1–5). UCS memprioritaskan uji paling ringan terlebih dahulu sebelum merekomendasikan uji yang invasif.
            - **Asumsi Favourable Outcome**: Dalam merencanakan langkah ke depan, UCS mengasumsikan hasil yang mengonfirmasi goal. Uji pertama pada lintasan termurah tersebut disajikan sebagai rekomendasi.
            - **Online Replanning**: Saat pengguna memasukkan hasil observasi aktual, state sistem diperbarui dan UCS melakukan pencarian ulang secara dinamis jika hasil ternyata berlawanan.
            - **Bukan Probabilitas / Machine Learning**: Algoritma murni berbasis pohon pencarian status diskrit dengan *priority queue* min-heap (`heapq`).
            """
        )


def render_progress_indicator(
    state: DiagnosisState | None,
    has_active_session: bool,
    evaluation_status: str,
) -> None:
    """Menampilkan progress indicator 4 tahap diagnosis."""
    diag_symptoms = st.session_state.get("diag_symptoms")
    diag_state = st.session_state.get("diag_state")

    stage1_done = diag_symptoms is not None
    stage2_done = diag_state is not None
    stage3_done = diag_state is not None and len(diag_state.test_results) > 0
    stage4_done = evaluation_status in ("conclusive", "inconclusive")

    if not stage1_done:
        active_stage = 1
    elif not stage2_done:
        active_stage = 2
    elif not stage3_done:
        active_stage = 3
    elif not stage4_done:
        active_stage = 4
    else:
        active_stage = 4

    stages = [
        (1, "Identifikasi Gejala", stage1_done, active_stage == 1),
        (2, "Analisis UCS", stage2_done, active_stage == 2),
        (3, "Pemeriksaan", stage3_done, active_stage == 3),
        (4, "Kesimpulan", stage4_done, active_stage == 4),
    ]

    steps_html = []
    for step_num, step_name, is_done, is_active in stages:
        status_cls = "done" if is_done else ("active" if is_active else "")
        icon = "&#10003;" if is_done else str(step_num)
        steps_html.append(
            f'<div class="progress-step {status_cls}">'
            f'<div class="progress-dot">{icon}</div>'
            f'<div class="progress-label">{step_name}</div>'
            f"</div>"
        )

    # Dirender sebagai satu baris HTML tanpa baris kosong: baris kosong
    # memutus blok HTML pada parser Markdown Streamlit sehingga tag tampil
    # sebagai teks mentah di dalam code block.
    track_html = '<div class="progress-track">' + "".join(steps_html) + "</div>"
    st.markdown(track_html, unsafe_allow_html=True)


def render_contextual_feedback(
    state: DiagnosisState | None,
    evaluation: dict[str, Any] | None,
) -> None:
    """Menampilkan pesan kontekstual sesuai kondisi sesi diagnosis."""
    if state is None:
        # Belum ada sesi -> Pesan A
        tone = "slate"
        title = "Sistem Siap"
        message = (
            "Belum ada sesi diagnosis aktif. Silakan pilih gejala awal atau ceritakan masalah "
            "komputer Anda pada formulir di bawah untuk memulai analisis."
        )
    elif len(state.test_results) == 0:
        # Sesi baru dimulai -> Pesan B
        tone = "blue"
        title = "Sesi Diagnosis Dimulai"
        message = (
            "Gejala awal berhasil dimuat. Algoritma Uniform Cost Search (UCS) sedang merumuskan "
            "lintasan pemeriksaan optimal dengan bobot biaya disrupsi terendah."
        )
    elif evaluation and evaluation.get("status") in ("conclusive", "inconclusive"):
        # Diagnosis selesai -> Pesan G
        if evaluation.get("status") == "conclusive":
            tone = "green"
            title = "Diagnosis Selesai — Masalah Teridentifikasi"
            cat_name = html.escape(evaluation.get("category_name", "Kategori Terkonfirmasi"))
            message = (
                f"Sistem berhasil menetapkan diagnosis konklusif: <strong>{cat_name}</strong>. "
                "Silakan ikuti rekomendasi perbaikan teknis pada Bagian D di bawah."
            )
        else:
            tone = "amber"
            title = "Diagnosis Selesai — Belum Konklusif"
            message = (
                "Seluruh pemeriksaan relevan telah diselesaikan, namun bukti belum definitif untuk "
                "memastikan satu kategori masalah. Sesuai prinsip keandalan AI, sistem tidak memaksakan kesimpulan palsu."
            )
    elif evaluation and evaluation.get("evidence_sufficiency") == "partial":
        # Bukti belum cukup -> Pesan F
        tone = "amber"
        title = "Bukti Belum Cukup"
        message = (
            "Hasil observasi sebelumnya belum definitif untuk mengonfirmasi kategori. "
            "Lanjutkan pemeriksaan berikutnya yang direkomendasikan UCS agar bukti semakin lengkap."
        )
    elif len(state.test_results) > 0:
        # Hasil diterima -> Pesan E
        tone = "blue"
        title = "Hasil Pemeriksaan Diterima"
        message = (
            "Bukti telah diperbarui berdasarkan observasi terbaru. UCS mengevaluasi ulang pohon "
            "pencarian untuk menentukan langkah diagnostik optimal berikutnya."
        )
    else:
        # UCS merekomendasikan tes -> Pesan C/D
        tone = "blue"
        title = "Pemeriksaan Direkomendasikan"
        message = (
            "Lakukan pemeriksaan yang disarankan pada Bagian B sesuai petunjuk teknis yang tertera, "
            "kemudian pilih hasil observasi aktual."
        )

    st.markdown(
        f"""
        <div class="contextual-feedback {tone}">
            <div class="feedback-title">{title}</div>
            <div>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_free_text_panel(
    symptoms: dict[str, dict[str, Any]],
    categories: dict[str, dict[str, Any]],
    tests: dict[str, dict[str, Any]],
) -> None:
    """Panel deskripsi bebas dan perumusan gejala tambahan berbasis sesi."""
    with st.expander("Ceritakan Masalah Komputer Anda (Deskripsi Bebas & BSOD)", expanded=False):
        st.markdown(
            "Tuliskan keluhan atau gejala komputer Anda dalam bahasa sehari-hari "
            "(misal: *'laptop sering layar biru DPC_WATCHDOG_VIOLATION dan freeze saat buka file'*) "
            "dan/atau masukkan kode error layar biru (BSOD)."
        )
        col_desc, col_bsod = st.columns([2, 1])
        with col_desc:
            user_text = st.text_area(
                "Deskripsi Bebas Masalah:",
                placeholder="Contoh: Laptop sering bluescreen DPC_WATCHDOG_VIOLATION saat copy file besar...",
                key="free_text_input",
                height=90,
            )
        with col_bsod:
            bsod_input = st.text_input(
                "Kode Error / BSOD (Opsional):",
                placeholder="Contoh: DPC_WATCHDOG_VIOLATION",
                key="bsod_input",
            )
            st.caption("Pilihan umum: DPC_WATCHDOG_VIOLATION, MEMORY_MANAGEMENT, VIDEO_TDR_FAILURE, dll.")

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            btn_analyze = st.button("Analisis Masalah", type="secondary", key="btn_analyze_text", use_container_width=True)
        with col_act2:
            btn_not_found = st.button("Saya Tidak Menemukan Masalah Saya", key="btn_not_found_symptom", use_container_width=True)

        current_text = (user_text or "").strip()
        current_code = (bsod_input or "").strip()
        current_signature = f"{current_text}::{current_code.upper()}"

        if btn_analyze or btn_not_found:
            if not current_text and not current_code:
                st.warning(
                    "Isi deskripsi masalah atau kode BSOD terlebih dahulu sebelum menjalankan analisis."
                )
            else:
                val_res = validate_bsod_code(current_code) if current_code else None

                # Kategori awal hanya diambil dari kode BSOD yang benar-benar valid.
                cat_list: list[str] = []
                if val_res and val_res["status"] == "valid":
                    cat_list = list(val_res["canonical"]["candidate_categories"])

                symptom_text = current_text or "Masalah belum teridentifikasi pada daftar gejala bawaan"
                analysis = suggest_symptoms_from_text(current_text, current_code, symptoms)
                user_sym_res = create_user_defined_symptom(
                    symptom_text, current_code, categories=cat_list
                )

                st.session_state.text_analysis = analysis
                st.session_state.pending_custom_symptom = user_sym_res
                st.session_state.bsod_validation = val_res
                st.session_state.analysis_signature = current_signature
                st.session_state.confirmed_analysis_signature = None

        # Tampilkan Hasil Analisis & Konfirmasi Gejala
        analysis_result = st.session_state.get("text_analysis")
        pending_custom = st.session_state.get("pending_custom_symptom")
        bsod_validation = st.session_state.get("bsod_validation")
        stored_signature = st.session_state.get("analysis_signature")
        confirmed_signature = st.session_state.get("confirmed_analysis_signature")

        if not current_text and not current_code:
            st.caption(
                "Belum ada analisis. Isi deskripsi masalah atau kode BSOD, lalu tekan "
                "\"Analisis Masalah\" untuk melihat hasil identifikasi."
            )
            return

        if stored_signature is None or stored_signature != current_signature:
            st.caption(
                "Input berubah sejak analisis terakhir. Tekan \"Analisis Masalah\" untuk "
                "memperbarui hasil identifikasi."
            )
            return

        if confirmed_signature is not None and confirmed_signature == stored_signature:
            st.success("Gejala khusus berhasil ditambahkan ke sesi diagnosis.")
            st.caption(
                "Gejala tersebut sudah terpilih pada daftar gejala di bawah dan akan dipakai "
                "saat sesi diagnosis dimulai."
            )
            return

        st.divider()
        st.markdown("#### Ringkasan Identifikasi Masalah Pengguna")

        # Status validasi kode BSOD
        if bsod_validation:
            status = bsod_validation.get("status")
            if status == "conflict":
                st.warning(
                    f"**Nama dan kode BSOD tidak cocok.** Kode `{bsod_validation['hex']}` "
                    f"teridentifikasi sebagai **{bsod_validation['expected_name']}**, sedangkan nama "
                    f"yang Anda tulis adalah **{bsod_validation['name']}**. "
                    "Periksa kembali layar BSOD sebelum melanjutkan."
                )
                st.caption(
                    "Hasil pemetaan belum dipakai untuk diagnosis karena input masih bertentangan. "
                    "Perbaiki nama atau kode BSOD, lalu jalankan analisis ulang."
                )
                return
            if status == "unknown_code":
                st.info(
                    f"Kode `{bsod_validation.get('code', '')}` belum terdaftar pada basis pengetahuan. "
                    "Sistem tetap dapat melanjutkan jika Anda memilih kategori masalah secara manual."
                )
            elif status == "unknown":
                st.info(
                    "Kode BSOD belum terdaftar pada basis pengetahuan. Sistem tetap dapat melanjutkan "
                    "jika Anda memilih kategori masalah secara manual."
                )
            elif status == "invalid_format":
                st.info(
                    "Format kode BSOD tidak dikenali. Gunakan bentuk seperti `NTFS_FILE_SYSTEM (0x00000024)` "
                    "atau cukup nama kodenya."
                )
            elif status == "valid":
                st.caption(
                    "Kode BSOD terverifikasi dan hanya menjadi petunjuk awal, bukan bukti kerusakan."
                )

        suggested_ids = analysis_result.get("suggested_symptom_ids", []) if analysis_result else []
        bsod_res = analysis_result.get("bsod_result") if analysis_result else None

        # 1. Gejala bawaan yang cocok langsung
        if suggested_ids:
            render_badges([("Dikenali pada Basis Pengetahuan", "green")])
            st.markdown("**Gejala Bawaan yang Cocok:**")
            for sid in suggested_ids:
                if sid in symptoms:
                    primary = symptoms[sid]["related_categories"][0]
                    st.markdown(
                        f"- **{symptoms[sid]['name']}** "
                        f"({categories[primary]['name']})"
                    )

            if st.button("Pilih Gejala Bawaan Ini", type="secondary", key="btn_use_builtin"):
                valid_ids = [sid for sid in suggested_ids if sid in symptoms]
                st.session_state.symptom_selector = valid_ids
                st.rerun()

        if bsod_res and bsod_res.get("found"):
            st.caption(f"Petunjuk awal: {bsod_res.get('explanation', '')}")

        # 2. Gejala Tambahan Terstruktur (User-Defined Symptom)
        if pending_custom and pending_custom["success"]:
            sym = pending_custom["symptom"]
            render_badges([("Gejala Khusus", "blue"), ("Perlu Konfirmasi", "amber")])

            st.markdown(
                (
                    '<div class="custom-symptom-card">'
                    '<div class="custom-symptom-kicker">GEJALA TAMBAHAN TERSTRUKTUR</div>'
                    f'<div class="custom-symptom-title">{html.escape(sym["name"])}</div>'
                    f'<div class="custom-symptom-desc"><strong>Deskripsi asli:</strong> '
                    f'{html.escape(sym["description"])}</div>'
                    + (
                        f'<div class="custom-symptom-desc"><strong>Kode BSOD:</strong> '
                        f'{html.escape(sym["error_code"])}</div>'
                        if sym.get("error_code")
                        else ""
                    )
                    + '<div class="custom-symptom-note"><strong>Catatan ketidakpastian:</strong> '
                    f'{" ".join(html.escape(n) for n in sym["uncertainty_notes"])}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            st.markdown("**Pilih Kategori Masalah yang Berkaitan:**")
            st.caption(
                "Kategori berikut disarankan dari pencocokan kode BSOD dan kata kunci deskripsi. "
                "Anda dapat menambah atau menghapus kategori sebelum mengonfirmasi."
            )

            cat_options = {cat_id: cat["name"] for cat_id, cat in categories.items()}
            default_cats = [c for c in sym.get("related_categories", []) if c in cat_options]

            selected_categories = st.multiselect(
                "Kategori yang dikaitkan dengan gejala ini:",
                options=list(cat_options.keys()),
                format_func=lambda c: cat_options[c],
                default=default_cats,
                key=f"custom_symptom_categories_{sym['id']}",
                help=(
                    "Pilih satu atau lebih kategori. Pemeriksaan diagnostik akan "
                    "didasarkan pada kategori yang dipilih."
                ),
            )

            cat_to_tests = {
                "driver_software": ["test_driver_status", "test_error_code_history"],
                "overheating": ["test_cpu_gpu_temp"],
                "storage_disk": ["test_smart_disk", "test_disk_system_error_logs"],
                "ram_memory": ["test_memory_diagnostic"],
            }

            relevant_tests: list[str] = []
            for cat in selected_categories:
                for tid in cat_to_tests.get(cat, []):
                    if tid not in relevant_tests:
                        relevant_tests.append(tid)

            if selected_categories and relevant_tests:
                st.markdown("**Pemeriksaan yang Tersedia untuk Kategori Terpilih:**")
                for tid in relevant_tests:
                    if tid in tests:
                        test = tests[tid]
                        st.markdown(
                            f"- **{test['name']}** "
                            f"({categories[test['category']]['name']}) - Cost relatif: {test['cost']}"
                        )
            elif not selected_categories:
                st.warning("Pilih minimal satu kategori untuk melanjutkan.")

            c_k1, c_k2, c_k3 = st.columns([2, 1, 1])
            with c_k1:
                if st.button(
                    "Konfirmasi dan Tambahkan ke Diagnosis",
                    type="primary",
                    key="btn_confirm_custom_sym",
                    use_container_width=True,
                    disabled=len(selected_categories) == 0,
                ):
                    sym["related_categories"] = list(selected_categories)
                    sym["candidate_tests"] = relevant_tests
                    sym["confirmed"] = True

                    if "custom_symptoms" not in st.session_state:
                        st.session_state.custom_symptoms = {}
                    # Gejala yang sama tidak diduplikasi: ID deterministik menimpa entri lama.
                    st.session_state.custom_symptoms[sym["id"]] = sym

                    current_sel = list(st.session_state.get("symptom_selector", []))
                    if sym["id"] not in current_sel:
                        current_sel.append(sym["id"])
                    st.session_state.symptom_selector = current_sel

                    st.session_state.pending_custom_symptom = None
                    st.session_state.confirmed_analysis_signature = current_signature
                    st.toast("Gejala khusus berhasil ditambahkan ke sesi diagnosis.")
                    st.rerun()
            with c_k2:
                if st.button("Pilih Gejala Lain", key="btn_other_sym", use_container_width=True):
                    st.session_state.pending_custom_symptom = None
                    st.session_state.text_analysis = None
                    st.session_state.bsod_validation = None
                    st.session_state.analysis_signature = None
                    st.rerun()
            with c_k3:
                if st.button("Batalkan", key="btn_cancel_custom_sym", use_container_width=True):
                    st.session_state.pending_custom_symptom = None
                    st.session_state.text_analysis = None
                    st.session_state.bsod_validation = None
                    st.session_state.analysis_signature = None
                    st.rerun()

        elif pending_custom and not pending_custom["success"]:
            render_badges([("Belum Ada Kandidat", "slate")])
            st.info(pending_custom.get("message"))
            st.caption(
                "Analisis belum menemukan kandidat. Anda dapat memilih gejala terdekat pada daftar "
                "di bawah, atau mengulang penjelasan dengan kata kunci perangkat keras "
                "(driver, suhu, disk, atau RAM)."
            )
        elif analysis_result and not suggested_ids:
            render_badges([("Belum Ada Kandidat", "slate")])
            st.info(analysis_result.get("summary"))


def get_next_recommended_test_filtered(
    state: DiagnosisState,
    skipped_tests: list[str] | set[str] | None = None,
) -> dict[str, Any] | None:
    """Wrapper get_next_recommended_test yang mengabaikan tes yang di-skip."""
    if not skipped_tests:
        return get_next_recommended_test(state)

    skipped_set = set(skipped_tests)
    shadow_state = DiagnosisState(
        initial_symptoms=state.initial_symptoms,
        performed_tests=state.performed_tests | frozenset(skipped_set),
        test_results=state.test_results,
        supporting_evidence=state.supporting_evidence,
        contradicting_evidence=state.contradicting_evidence,
        possible_categories=state.possible_categories,
        cumulative_cost=state.cumulative_cost,
    )
    return get_next_recommended_test(shadow_state)


def render_diagnostic_instructions(
    instruction: dict[str, Any], test: dict[str, Any]
) -> None:
    """Tampilkan petunjuk langkah-langkah diagnostik untuk suatu test."""
    steps_html = "".join(
        f"<li>{html.escape(step)}</li>" for step in instruction.get("steps", [])
    )
    st.markdown(
        f"""
        <div class="diag-instructions">
            <div class="diag-instructions-title">Petunjuk Teknis: {html.escape(test['name'])}</div>
            <ol class="diag-instructions-steps">{steps_html}</ol>
            <div class="diag-instructions-path"><strong>Navigasi Windows:</strong> <code>{html.escape(instruction.get('windows_path', '-'))}</code></div>
            {f'<div class="diag-instructions-warning">Peringatan: {html.escape(instruction["warning"])}</div>' if instruction.get("warning") else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_process_section(
    state: DiagnosisState,
    tests: dict[str, dict[str, Any]],
    categories: dict[str, dict[str, Any]],
    symptom_names: dict[str, str],
) -> None:
    """Bagian B: Dashboard KPI dan Kartu Rekomendasi Pemeriksaan UCS."""
    st.markdown("### B. Proses Diagnosis & Rekomendasi UCS")

    performed_count = len(state.performed_tests)

    # Metric Dashboard 4 Kolom
    m_cols = st.columns(4)
    m_cols[0].metric("Pemeriksaan Selesai", f"{performed_count} / {len(tests)}")
    m_cols[1].metric("Total Cost Kumulatif", f"{state.cumulative_cost:g}")
    m_cols[2].metric("Kategori Terbuka", f"{len(state.possible_categories)} dari 4")
    sufficiency = get_evidence_sufficiency(state)
    m_cols[3].metric("Status Kecukupan", SUFFICIENCY_LABELS[sufficiency][0])

    st.write("")

    # Gejala Terpilih
    st.markdown('<div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.2rem;">Gejala Awal yang Dipilih:</div>', unsafe_allow_html=True)
    render_chips([symptom_names[s_id] for s_id in sorted(state.initial_symptoms)])

    # Kategori Aktif
    render_active_categories(state, categories)

    evaluation = evaluate_diagnosis(state)
    if evaluation["status"] != "in_progress":
        return

    skipped_tests = st.session_state.get("skipped_tests", [])
    next_test = get_next_recommended_test_filtered(state, skipped_tests)
    if next_test is None:
        st.info("Tidak ada pemeriksaan lanjutan yang dapat direkomendasikan. Periksa hasil evaluasi di bawah.")
        return

    # Centerpiece: UCS Recommended Test Card (blok HTML self-contained)
    st.markdown(
        f"""
        <div class="ucs-featured-card">
            <div class="ucs-tagline">
                <span class="badge badge-blue">REKOMENDASI PEMERIKSAAN BERIKUTNYA</span>
                <span class="badge badge-slate">KATEGORI: {html.escape(categories[next_test['category']]['name'].upper())}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
                <div>
                    <h2 style="color: #0F172A; margin: 0 0 0.4rem 0; font-size: 1.55rem;">{html.escape(next_test['name'])}</h2>
                    <p style="color: #475569; font-size: 0.95rem; margin: 0; line-height: 1.5;">{html.escape(next_test['description'])}</p>
                </div>
                <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-radius: 8px; padding: 0.5rem 1rem; text-align: center; min-width: 110px;">
                    <div style="font-size: 0.72rem; font-weight: 700; color: #1D4ED8; text-transform: uppercase; letter-spacing: 0.05em;">BOBOT BIAYA</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #1E40AF; font-family: 'JetBrains Mono', monospace;">{next_test['cost']}</div>
                </div>
            </div>
            <div class="ucs-rationale-box">
                <strong>Mengapa pemeriksaan ini dipilih?</strong> UCS mengevaluasi antrean prioritas berbasis min-heap dan mengidentifikasi pemeriksaan ini sebagai langkah awal dengan <em>total cumulative cost terendah</em> untuk mengonfirmasi kategori yang masih mungkin. Bobot biaya {next_test['cost']} mencerminkan tingkat disrupsi terendah di antara uji yang relevan saat ini.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Petunjuk teknis pemeriksaan
    instruction = DIAGNOSTIC_INSTRUCTIONS.get(next_test["id"])
    if instruction:
        render_diagnostic_instructions(instruction, next_test)

    # Form Input Hasil Observasi
    with st.container(border=True):
        st.markdown(f"**Pilih Hasil Observasi:** {next_test['name']}")
        with st.form(key=f"test_result_form_{next_test['id']}_{performed_count}"):
            choice_options = list(next_test["possible_outcomes"]) + ["skip"]

            def format_choice(val: str) -> str:
                if val == "skip":
                    return "Lewati pemeriksaan ini (Skip test — uji lain akan diprioritaskan)"
                return outcome_label(val)

            outcome = st.radio(
                "Pilihan hasil:",
                options=choice_options,
                format_func=format_choice,
                horizontal=False,
                label_visibility="collapsed",
                help="Pilih luaran sesuai hasil pengamatan pada komputer, atau pilih lewati.",
            )
            st.write("")
            btn_submit = st.form_submit_button("Kirim & Evaluasi Hasil Pemeriksaan", type="primary")

    if btn_submit:
        if outcome == "skip":
            if "skipped_tests" not in st.session_state:
                st.session_state.skipped_tests = []
            if next_test["id"] not in st.session_state.skipped_tests:
                st.session_state.skipped_tests.append(next_test["id"])
            st.session_state.diag_log.append(
                {
                    "test_name": f"{next_test['name']} [Dilewati]",
                    "outcome": "skip",
                    "cost": 0,
                    "cumulative_cost": state.cumulative_cost,
                }
            )
            st.rerun()
        else:
            try:
                updated_state = apply_test_result(state, next_test["id"], outcome)
            except DiagnosisError as exc:
                st.error(str(exc))
            else:
                st.session_state.diag_state = updated_state
                st.session_state.diag_log.append(
                    {
                        "test_name": next_test["name"],
                        "outcome": outcome,
                        "cost": next_test["cost"],
                        "cumulative_cost": updated_state.cumulative_cost,
                    }
                )
                st.rerun()


def render_intro() -> None:
    """Tampilkan panduan interaktif saat belum ada sesi yang aktif."""
    st.markdown("### Cara Kerja Sistem Diagnostik")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-number">1</div>
                <div class="step-title">Pilih Gejala</div>
                <p class="step-desc">
                    Tentukan indikasi kerusakan fisik atau perangkat lunak Windows yang dialami komputer.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-number">2</div>
                <div class="step-title">Rekomendasi UCS</div>
                <p class="step-desc">
                    Algoritma menghitung jalur pemeriksaan berbiaya minimum dan merekomendasikan uji optimal bertahap.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-number">3</div>
                <div class="step-title">Hasil &amp; Rekomendasi</div>
                <p class="step-desc">
                    Sistem menyimpulkan diagnosis konklusif atau inkonklusif secara objektif tanpa estimasi palsu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_algorithm_explanation()


def main() -> None:
    """Titik masuk aplikasi Streamlit."""
    st.set_page_config(
        page_title=f"{APP_NAME} | Classical AI",
        page_icon="TD",
        layout="wide",
        initial_sidebar_state="auto",
    )
    inject_styles()

    for key, default in DIAGNOSIS_STATE_DEFAULTS.items():
        st.session_state.setdefault(
            key, list(default) if isinstance(default, list) else dict(default) if isinstance(default, dict) else default
        )
    # Flag feedback UI terpisah dari state diagnosis; tidak ikut direset.
    st.session_state.setdefault(NEW_DIAGNOSIS_FEEDBACK_KEY, None)

    try:
        symptoms_data = load_symptoms()
        tests_data = load_diagnostic_tests()
    except KnowledgeBaseError as exc:
        st.error(f"Knowledge base tidak dapat dimuat: {exc}")
        st.stop()

    categories = category_lookup(symptoms_data)
    symptoms = symptom_lookup(symptoms_data)
    tests = tests_lookup(tests_data)
    custom_symptoms: dict[str, dict[str, Any]] = st.session_state.get("custom_symptoms") or {}
    symptom_names = {symptom_id: symptom["name"] for symptom_id, symptom in symptoms.items()}
    symptom_names.update({sid: sym["name"] for sid, sym in custom_symptoms.items()})

    state: DiagnosisState | None = st.session_state.diag_state
    has_active_session = state is not None

    evaluation = evaluate_diagnosis(state) if state is not None else None
    eval_status = evaluation["status"] if evaluation else "not_started"

    render_sidebar(categories, has_active_session)
    render_header()
    render_progress_indicator(state, has_active_session, eval_status)
    render_contextual_feedback(state, evaluation)

    # Feedback animasi "sesi diagnosis baru siap": konsumsi sekali pakai.
    show_new_session_feedback = consume_new_diagnosis_feedback()
    if show_new_session_feedback:
        render_new_diagnosis_feedback()

    render_start_section(
        symptoms,
        categories,
        tests,
        has_active_session,
        animate_enter=show_new_session_feedback,
    )

    if state is None:
        render_intro()
        return

    if tuple(sorted(state.initial_symptoms)) != st.session_state.diag_symptoms:
        st.warning(
            "Pilihan gejala baru terdeteksi. Sesi diagnosis saat ini masih berjalan pada gejala sebelumnya. "
            "Gunakan tombol Mulai Diagnosis Baru pada bagian hasil diagnosis untuk beralih sesi."
        )

    render_process_section(state, tests, categories, symptom_names)
    st.write("")
    render_evidence(state, tests, categories)
    st.write("")
    render_result(state, evaluation, tests, categories)
    st.write("")
    render_history(st.session_state.diag_log)
    render_algorithm_explanation()


if __name__ == "__main__":
    main()

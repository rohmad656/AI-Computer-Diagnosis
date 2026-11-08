"""Pencocokan gejala dari deskripsi bebas dan kode BSOD.

Modul ini sepenuhnya deterministik dan berbasis aturan (bukan Machine Learning).
Hasil pencocokan hanya berupa *saran* symptom_id yang harus dikonfirmasi pengguna.
Modul ini tidak pernah menambahkan bukti diagnosis secara otomatis.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pemetaan kode BSOD
# ---------------------------------------------------------------------------
# Catatan: seluruh symptom_id di bawah harus valid terhadap data/symptoms.json.
BSOD_MAP: dict[str, dict[str, Any]] = {
    "FAT_FILE_SYSTEM": {
        "candidate_symptoms": ["sym_disk_slow_freeze", "sym_chkdsk_auto"],
        "candidate_categories": ["storage_disk"],
        "explanation": "Masalah sistem file FAT (File Allocation Table).",
    },
    "NTFS_FILE_SYSTEM": {
        "candidate_symptoms": ["sym_disk_slow_freeze", "sym_chkdsk_auto"],
        "candidate_categories": ["storage_disk"],
        "explanation": "Masalah sistem file NTFS (New Technology File System).",
    },
    "DPC_WATCHDOG_VIOLATION": {
        "candidate_symptoms": ["sym_bsod_driver", "sym_disk_slow_freeze"],
        "candidate_categories": ["driver_software", "storage_disk"],
        "explanation": (
            "DPC Watchdog mendeteksi waktu tunggu DPC yang berlebihan. Paling sering terkait "
            "driver sistem/storage yang tidak kompatibel (mis. SSD/SATA driver/firmware) atau masalah I/O storage."
        ),
    },
    "SYSTEM_SERVICE_EXCEPTION": {
        "candidate_symptoms": ["sym_bsod_driver"],
        "candidate_categories": ["driver_software"],
        "explanation": (
            "Kesalahan pada layanan sistem Windows. Paling sering disebabkan "
            "driver yang tidak kompatibel."
        ),
    },
    "MEMORY_MANAGEMENT": {
        "candidate_symptoms": ["sym_bsod_memory_management", "sym_app_crash_random"],
        "candidate_categories": ["ram_memory"],
        "explanation": (
            "Masalah manajemen memori Windows. Umumnya terkait modul RAM yang "
            "bermasalah atau instabilitas memori."
        ),
    },
    "VIDEO_TDR_FAILURE": {
        "candidate_symptoms": ["sym_bsod_driver", "sym_shutdown_thermal"],
        "candidate_categories": ["driver_software", "overheating"],
        "explanation": (
            "Driver kartu grafis (GPU) gagal merespons dalam batas waktu timeout. "
            "Penyebab utama adalah driver GPU korup atau GPU mengalami overheating."
        ),
    },
    "PAGE_FAULT_IN_NONPAGED_AREA": {
        "candidate_symptoms": ["sym_bsod_memory_management", "sym_app_crash_random"],
        "candidate_categories": ["ram_memory", "storage_disk"],
        "explanation": (
            "Kesalahan akses memori pada area non-paged. Dapat disebabkan modul RAM bermasalah "
            "atau kegagalan paging file pada media storage."
        ),
    },
    "IRQL_NOT_LESS_OR_EQUAL": {
        "candidate_symptoms": ["sym_bsod_driver", "sym_bsod_memory_management"],
        "candidate_categories": ["driver_software", "ram_memory"],
        "explanation": (
            "Driver mengakses alamat memori pada level IRQL yang salah. Sangat sering terkait "
            "driver yang tidak kompatibel atau modul RAM yang mengalami error bit."
        ),
    },
    "KERNEL_SECURITY_CHECK_FAILURE": {
        "candidate_symptoms": ["sym_bsod_driver", "sym_app_crash_random"],
        "candidate_categories": ["driver_software", "ram_memory"],
        "explanation": (
            "Struktur data kernel mengalami korupsi integritas. Sering dipicu oleh driver yang bermasalah, "
            "file sistem corrupt, atau memori yang tidak stabil."
        ),
    },
    "WHEA_UNCORRECTABLE_ERROR": {
        "candidate_symptoms": ["sym_shutdown_thermal", "sym_fan_loud_hot", "sym_app_crash_random"],
        "candidate_categories": ["overheating", "ram_memory"],
        "explanation": (
            "Hardware error yang tidak dapat diperbaiki (Windows Hardware Error Architecture). "
            "Sering terkait CPU overheating, voltase tidak stabil, atau kerusakan fisik RAM/motherboard."
        ),
    },
    "CRITICAL_PROCESS_DIED": {
        "candidate_symptoms": ["sym_bsod_driver", "sym_disk_slow_freeze"],
        "candidate_categories": ["driver_software", "storage_disk"],
        "explanation": (
            "Proses kritis Windows berhenti tidak terduga. Biasanya terkait "
            "driver sistem atau hilangnya komunikasi drive/file sistem secara mendadak."
        ),
    },
}

# Mapping kode hex ke nama BSOD untuk validasi
_BSOD_HEX_MAP: dict[str, str] = {
    "0x00000023": "FAT_FILE_SYSTEM",
    "0x00000024": "NTFS_FILE_SYSTEM",
}

def validate_bsod_code(input_str: str) -> dict[str, Any]:
    """Validasi input BSOD nama atau kode hexadecimal."""
    text = (input_str or "").strip()
    if not text:
        return {"status": "empty"}

    # Pattern: NAMA (0xHEX) atau hanya NAMA atau hanya 0xHEX
    match = re.match(r"^([a-zA-Z_]+)(?:\s*\(?([xX0-9a-fA-F]+)\)?)?$", text)
    if not match:
        # Mungkin hanya hex
        if re.match(r"^[xX0-9a-fA-F]+$", text):
            hex_code = text.upper() if text.startswith("0X") else f"0x{text.upper()}"
            if hex_code in _BSOD_HEX_MAP:
                name = _BSOD_HEX_MAP[hex_code]
                return {"status": "valid", "canonical": BSOD_MAP[name]}
            return {"status": "unknown_code", "code": hex_code}
        return {"status": "invalid_format"}

    name_part = match.group(1).upper()
    hex_part = match.group(2).upper() if match.group(2) else None
    if hex_part and not hex_part.startswith("0X"):
        hex_part = f"0X{hex_part}"

    # Cari di map
    found_by_name = BSOD_MAP.get(name_part)
    
    found_by_hex = None
    if hex_part and hex_part in _BSOD_HEX_MAP:
        found_by_hex = BSOD_MAP[_BSOD_HEX_MAP[hex_part]]

    if hex_part and found_by_hex:
        if name_part and found_by_hex != BSOD_MAP.get(name_part):
            return {"status": "conflict", "name": name_part, "hex": hex_part, "expected_name": _BSOD_HEX_MAP[hex_part]}
        return {"status": "valid", "canonical": found_by_hex}

    if found_by_name:
        return {"status": "valid", "canonical": found_by_name}
    
    return {"status": "unknown", "name": name_part, "hex": hex_part}


# Ringkasan instruksi per kode BSOD untuk ditampilkan di UI.
BSOD_INSTRUCTIONS: dict[str, dict[str, Any]] = {
    code: {
        "explanation": data["explanation"],
        "candidate_categories": list(data["candidate_categories"]),
    }
    for code, data in BSOD_MAP.items()
}


# ---------------------------------------------------------------------------
# Alias deskripsi bebas (Bahasa Indonesia + Inggris)
# ---------------------------------------------------------------------------
# Seluruh nilai harus berupa symptom_id yang ada pada data/symptoms.json.
ALIAS_MAP: dict[str, list[str]] = {
    # Layar biru / BSOD umum
    "bsod": ["sym_bsod_driver", "sym_bsod_memory_management"],
    "blue screen": ["sym_bsod_driver", "sym_bsod_memory_management"],
    "bluescreen": ["sym_bsod_driver", "sym_bsod_memory_management"],
    "blue screen of death": ["sym_bsod_driver", "sym_bsod_memory_management"],
    "layar biru": ["sym_bsod_driver", "sym_bsod_memory_management"],
    # Driver
    "driver": ["sym_bsod_driver", "sym_device_manager_yellow"],
    "driver error": ["sym_bsod_driver"],
    "error driver": ["sym_bsod_driver"],
    "driver bermasalah": ["sym_bsod_driver"],
    "driver rusak": ["sym_bsod_driver"],
    "driver crash": ["sym_bsod_driver"],
    "system service exception": ["sym_bsod_driver"],
    "video tdr failure": ["sym_bsod_driver"],
    "dpc watchdog violation": ["sym_bsod_driver"],
    "device manager": ["sym_device_manager_yellow"],
    "tanda seru kuning": ["sym_device_manager_yellow"],
    "yellow bang": ["sym_device_manager_yellow"],
    "unknown device": ["sym_device_manager_yellow"],
    "perangkat tidak dikenal": ["sym_device_manager_yellow"],
    # Overheating
    "overheat": ["sym_fan_loud_hot", "sym_shutdown_thermal"],
    "overheating": ["sym_fan_loud_hot", "sym_shutdown_thermal"],
    "panas": ["sym_fan_loud_hot"],
    "suhu panas": ["sym_fan_loud_hot", "sym_shutdown_thermal"],
    "suhu tinggi": ["sym_fan_loud_hot", "sym_shutdown_thermal"],
    "kipas bising": ["sym_fan_loud_hot"],
    "kipas kencang": ["sym_fan_loud_hot"],
    "kipas berisik": ["sym_fan_loud_hot"],
    "fan loud": ["sym_fan_loud_hot"],
    "thermal": ["sym_fan_loud_hot", "sym_shutdown_thermal"],
    "thermal shutdown": ["sym_shutdown_thermal"],
    "mati mendadak": ["sym_shutdown_thermal"],
    "shutdown sendiri": ["sym_shutdown_thermal"],
    "restart sendiri": ["sym_shutdown_thermal"],
    # Storage / disk
    "disk lambat": ["sym_disk_slow_freeze"],
    "hardisk lambat": ["sym_disk_slow_freeze"],
    "hard disk lambat": ["sym_disk_slow_freeze"],
    "hdd lambat": ["sym_disk_slow_freeze"],
    "ssd lambat": ["sym_disk_slow_freeze"],
    "slow disk": ["sym_disk_slow_freeze"],
    "freeze": ["sym_disk_slow_freeze"],
    "hang": ["sym_disk_slow_freeze"],
    "lemot": ["sym_disk_slow_freeze"],
    "100 disk": ["sym_disk_slow_freeze"],
    "chkdsk": ["sym_chkdsk_auto"],
    "scanning and repairing drive": ["sym_chkdsk_auto"],
    "bad sector": ["sym_chkdsk_auto", "sym_disk_slow_freeze"],
    # RAM / memori
    "ram": ["sym_app_crash_random", "sym_bsod_memory_management"],
    "memory": ["sym_app_crash_random", "sym_bsod_memory_management"],
    "memori": ["sym_app_crash_random", "sym_bsod_memory_management"],
    "memory management": ["sym_bsod_memory_management", "sym_app_crash_random"],
    "page fault": ["sym_bsod_memory_management", "sym_app_crash_random"],
    "aplikasi crash": ["sym_app_crash_random"],
    "aplikasi close": ["sym_app_crash_random"],
    "aplikasi tertutup": ["sym_app_crash_random"],
    "app crash": ["sym_app_crash_random"],
    "random crash": ["sym_app_crash_random"],
    "crash": ["sym_app_crash_random"],
    "access violation": ["sym_app_crash_random"],
}

# Kata umum yang tidak dianggap sebagai istilah tak dikenal.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "with", "without", "my", "me", "i",
        "is", "are", "was", "were", "be", "been", "being", "it", "its", "this",
        "that", "these", "those", "to", "of", "in", "on", "at", "for", "from",
        "when", "while", "after", "before", "saat", "ketika", "dan", "atau",
        "tapi", "tetapi", "yang", "saya", "aku", "komputer", "laptop", "pc",
        "windows", "sering", "kadang", "kadang-kadang", "selalu", "tiba", "tiba-tiba",
        "terus", "sudah", "telah", "sedang", "akan", "ada", "tidak", "bukan",
        "belum", "juga", "karena", "seperti", "pada", "di", "ke", "dari", "untuk",
        "dengan", "tanpa", "ini", "itu", "nya", "mulai", "makin", "sangat",
        "sekali", "setelah", "sebelum", "kalau", "jika", "bila", "malah", "saja",
        "mesin", "masalah", "problem", "mengalami", "terjadi", "muncul",
    }
)

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)

_NORMALIZED_BSOD: dict[str, str] = {
    re.sub(_WHITESPACE_RE, " ", _PUNCT_RE.sub(" ", code.lower())).strip(): code
    for code in BSOD_MAP
}


def normalize_text(text: str) -> str:
    """Lowercase, strip, collapse whitespace, dan hapus tanda baca."""
    if not isinstance(text, str):
        return ""
    lowered = text.lower().strip()
    cleaned = _PUNCT_RE.sub(" ", lowered)
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def _contains_phrase(normalized_text: str, phrase: str) -> bool:
    """Cek kemunculan frasa sebagai kata utuh (word boundary)."""
    if not phrase:
        return False
    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
    return re.search(pattern, normalized_text) is not None


def match_bsod_code(code: str) -> dict[str, Any]:
    """Cocokkan kode BSOD dengan kandidat gejala pada basis pengetahuan.

    Hasil bersifat saran dan membutuhkan konfirmasi pengguna.
    """
    raw = (code or "").strip()
    empty_result = {
        "code": raw,
        "found": False,
        "candidate_symptoms": [],
        "candidate_categories": [],
        "explanation": "Kode BSOD tidak diisi.",
        "needs_confirmation": False,
    }
    if not raw:
        return empty_result

    normalized = normalize_text(raw)
    canonical = _NORMALIZED_BSOD.get(normalized)
    if canonical is None:
        return {
            "code": raw.upper(),
            "found": False,
            "candidate_symptoms": [],
            "candidate_categories": [],
            "explanation": (
                f"Kode BSOD '{raw}' belum dikenali pada basis pengetahuan. "
                "Silakan pilih gejala secara manual."
            ),
            "needs_confirmation": False,
        }

    data = BSOD_MAP[canonical]
    return {
        "code": canonical,
        "found": True,
        "candidate_symptoms": list(data["candidate_symptoms"]),
        "candidate_categories": list(data["candidate_categories"]),
        "explanation": data["explanation"],
        "needs_confirmation": True,
    }


def match_free_text(text: str, available_symptom_ids: list[str]) -> dict[str, Any]:
    """Cocokkan deskripsi bebas terhadap alias gejala yang tersedia.

    Hanya symptom_id yang terdapat pada ``available_symptom_ids`` yang
    dikembalikan. Hasil tidak pernah menjadi bukti diagnosis otomatis.
    """
    normalized = normalize_text(text)
    if not normalized:
        return {
            "matched_symptoms": [],
            "matched_aliases": [],
            "unmatched_terms": [],
            "confidence": "none",
            "needs_confirmation": False,
        }

    available = set(available_symptom_ids)
    matched_symptoms: list[str] = []
    matched_aliases: list[str] = []
    matched_alias_tokens: set[str] = set()

    # Frasa terpanjang diperiksa lebih dulu agar "memory management" menang
    # atas "memory".
    for alias in sorted(ALIAS_MAP, key=len, reverse=True):
        alias_normalized = normalize_text(alias)
        if not _contains_phrase(normalized, alias_normalized):
            continue
        matched_aliases.append(alias_normalized)
        matched_alias_tokens.update(alias_normalized.split())
        for symptom_id in ALIAS_MAP[alias]:
            if symptom_id in available and symptom_id not in matched_symptoms:
                matched_symptoms.append(symptom_id)

    tokens = normalized.split()
    unmatched_terms: list[str] = []
    for token in tokens:
        if token in _STOPWORDS or token in matched_alias_tokens:
            continue
        if token not in unmatched_terms:
            unmatched_terms.append(token)

    if len(matched_symptoms) == 1:
        confidence = "high"
    elif len(matched_symptoms) > 1:
        confidence = "medium"
    elif matched_aliases:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "matched_symptoms": matched_symptoms,
        "matched_aliases": matched_aliases,
        "unmatched_terms": unmatched_terms,
        "confidence": confidence,
        "needs_confirmation": bool(matched_symptoms),
    }


def suggest_symptoms_from_text(
    text: str,
    bsod_code: str,
    all_symptoms: dict[str, Any],
) -> dict[str, Any]:
    """Gabungkan hasil pencocokan deskripsi bebas dan kode BSOD.

    ``all_symptoms`` adalah mapping symptom_id -> data gejala (mengikuti
    struktur data/symptoms.json). Keluaran hanya berisi saran symptom_id.
    """
    available_ids = list(all_symptoms.keys())

    bsod_result = match_bsod_code(bsod_code) if (bsod_code or "").strip() else None
    text_result = match_free_text(text, available_ids) if normalize_text(text) else None

    suggested: list[str] = []

    def _add(candidates: list[str]) -> None:
        for symptom_id in candidates:
            if symptom_id in all_symptoms and symptom_id not in suggested:
                suggested.append(symptom_id)

    if bsod_result is not None:
        _add(bsod_result["candidate_symptoms"])
    if text_result is not None:
        _add(text_result["matched_symptoms"])

    if not suggested:
        summary = (
            "Belum ada gejala bawaan yang cocok langsung. "
            "Sistem dapat merumuskan Gejala Tambahan Terstruktur berdasarkan deskripsi atau kode Anda."
        )
    else:
        names = [all_symptoms[sid]["name"] for sid in suggested]
        summary = (
            f"Ditemukan {len(suggested)} kandidat gejala: " + "; ".join(names) + ". "
            "Konfirmasi sebelum digunakan sebagai gejala awal."
        )

    return {
        "suggested_symptom_ids": suggested,
        "bsod_result": bsod_result,
        "text_result": text_result,
        "summary": summary,
    }


def create_user_defined_symptom(
    user_text: str,
    bsod_code: str = "",
    categories: list[str] | None = None,
    session_prefix: str = "custom",
) -> dict[str, Any]:
    """Membuat objek Gejala Tambahan terstruktur berdasarkan laporan pengguna."""
    clean_text = (user_text or "").strip()
    clean_code = (bsod_code or "").strip()

    if not clean_text and not clean_code:
        return {"success": False, "message": "Input kosong.", "symptom": None}

    import hashlib
    content_hash = hashlib.md5(f"{clean_code}::{clean_text}".encode("utf-8")).hexdigest()[:8]
    symptom_id = f"sym_user_{session_prefix}_{content_hash}"

    # Validasi kode BSOD
    bsod_validation = validate_bsod_code(clean_code) if clean_code else None
    
    # Kategori: Prioritaskan input manual, fallback ke BSOD mapping
    final_categories = categories or []
    if not final_categories and bsod_validation and bsod_validation["status"] == "valid":
        final_categories = bsod_validation["canonical"]["candidate_categories"]

    # Keyword inferensi jika tidak ada kategori
    if not final_categories:
        norm_text = normalize_text(clean_text)
        keyword_cat_map = [
            (("driver", "vga", "display", "gpu", "kartu grafis", "device manager"), "driver_software"),
            (("panas", "overheat", "suhu", "kipas", "thermal", "fan", "mati mendadak"), "overheating"),
            (("disk", "harddisk", "hdd", "ssd", "lemot", "freeze", "bad sector", "chkdsk"), "storage_disk"),
            (("ram", "memory", "memori", "access violation", "aplikasi crash", "crash acak"), "ram_memory"),
        ]
        for kw, cat in keyword_cat_map:
            if any(k in norm_text for k in kw) and cat not in final_categories:
                final_categories.append(cat)

    if not final_categories:
        return {
            "success": False,
            "message": (
                "Deskripsi berhasil disimpan sebagai informasi tambahan, tetapi belum tersedia "
                "aturan pemeriksaan yang cukup untuk mendiagnosis masalah ini."
            ),
            "symptom": None,
        }

    # Map ke pemeriksaan
    cat_to_tests = {
        "driver_software": ["test_driver_status", "test_error_code_history"],
        "overheating": ["test_cpu_gpu_temp"],
        "storage_disk": ["test_smart_disk", "test_disk_system_error_logs"],
        "ram_memory": ["test_memory_diagnostic"],
    }
    tests = [tid for cat in final_categories for tid in cat_to_tests.get(cat, [])]

    symptom_obj = {
        "id": symptom_id,
        "name": f"Laporan: {clean_code or 'Gejala Tambahan'}",
        "description": clean_text,
        "source": "user_report",
        "error_code": clean_code,
        "related_categories": final_categories,
        "candidate_tests": list(set(tests)),
        "uncertainty_notes": ["Berdasarkan laporan pengguna."],
        "confirmed": False,
    }
    return {"success": True, "symptom": symptom_obj}

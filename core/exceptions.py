"""Kecuali (exceptions) kustom untuk knowledge base dan diagnosis."""

from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Kecuali dasar untuk error knowledge base."""
    pass


class KnowledgeBaseFileNotFoundError(KnowledgeBaseError):
    """File knowledge base tidak ditemukan."""
    pass


class KnowledgeBaseInvalidJSONError(KnowledgeBaseError):
    """File knowledge base bukan JSON valid."""
    pass


class KnowledgeBaseValidationError(KnowledgeBaseError):
    """Struktur knowledge base tidak valid."""
    pass


class DiagnosisError(Exception):
    """Kecuali dasar untuk error mesin diagnosis."""
    pass


class InvalidStateError(DiagnosisError):
    """State diagnosis tidak valid."""
    pass


class NoPathFoundError(DiagnosisError):
    """Tidak ditemukan jalur ke diagnosis."""
    pass
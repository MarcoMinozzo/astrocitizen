"""Erros de dominio partilhados."""

from __future__ import annotations


class AstroCitizenError(Exception):
    """Erro base da plataforma."""


class DomainError(AstroCitizenError):
    """Violacao de regra de negocio (RN-*)."""

    def __init__(self, message: str, *, rule_id: str | None = None) -> None:
        super().__init__(message)
        self.rule_id = rule_id


class NotFoundError(DomainError):
    """Entidade nao encontrada."""


class ConflictError(DomainError):
    """Conflito de versao / estado / unicidade."""

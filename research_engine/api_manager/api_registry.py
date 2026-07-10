"""
API Registry

Implements APIRegistry, the Category -> Primary Provider -> Backup
Provider mapping, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.2. Holds
no live status (APIHealth) and makes no network call -- it only
records which provider currently holds which role, per Category.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .api_provider import (
    APIProvider,
    Category,
    ProviderName,
    ProviderRole,
    copy_default_registrations,
)


class DuplicateRoleError(Exception):
    """Raised when registering a provider for a Category role that
    already has a registered provider -- exactly one Primary and one
    Backup per Category, per Section 3."""


class ProviderRoleNotFoundError(Exception):
    """Raised when looking up a Category role with no registered
    provider."""


class APIRegistry:
    """Category -> Primary/Backup Provider mapping. Seeded with the
    finalized Section 2/3 mapping by default; a Future Dashboard's
    Manual Provider Switch (Section 9) mutates this mapping via
    swap_roles() -- never APIManager's own selection logic, which only
    ever reads this Registry at request time (Section 6)."""

    def __init__(self, providers: Optional[List[APIProvider]] = None) -> None:
        self._by_role: Dict[Tuple[Category, ProviderRole], APIProvider] = {}
        for provider in providers if providers is not None else copy_default_registrations():
            self.register(provider)

    def register(self, provider: APIProvider) -> None:
        """Register a Category-role row. Raises DuplicateRoleError if
        that Category already has a provider registered for that Role
        -- exactly one Primary and one Backup per Category, never
        more."""
        key = (provider.category, provider.role)
        if key in self._by_role:
            raise DuplicateRoleError(
                f"{provider.category.value} already has a registered "
                f"{provider.role.value} provider."
            )
        self._by_role[key] = provider

    def get(self, category: Category, role: ProviderRole) -> APIProvider:
        try:
            return self._by_role[(category, role)]
        except KeyError as exc:
            raise ProviderRoleNotFoundError(
                f"No {role.value} provider registered for {category.value}."
            ) from exc

    def get_primary(self, category: Category) -> APIProvider:
        return self.get(category, ProviderRole.PRIMARY)

    def get_backup(self, category: Category) -> APIProvider:
        return self.get(category, ProviderRole.BACKUP)

    def swap_roles(self, category: Category) -> None:
        """Manual Provider Switch, per Section 9: swap which provider
        is Primary and which is Backup for `category`. Takes effect on
        the next request with no code change, since APIManager always
        reads this Registry at request time (Section 6)."""
        primary = self.get_primary(category)
        backup = self.get_backup(category)
        primary.role, backup.role = ProviderRole.BACKUP, ProviderRole.PRIMARY
        self._by_role[(category, ProviderRole.PRIMARY)] = backup
        self._by_role[(category, ProviderRole.BACKUP)] = primary

    def set_active(self, category: Category, role: ProviderRole, active: bool) -> None:
        """Enable or disable a Category-role row, per the `active` flag
        described in Section 10.1 -- a Dashboard toggle adjacent to
        Manual Provider Switch."""
        self.get(category, role).active = active

    def categories(self) -> List[Category]:
        """Every Category this Registry currently has entries for."""
        return list(Category)

    def all_providers(self) -> List[APIProvider]:
        """Every registered Category-role row, in no particular order."""
        return list(self._by_role.values())

    def find_by_name(self, provider_name: ProviderName) -> List[APIProvider]:
        """Every Category-role row for one raw provider name -- for
        example, Finnhub returns its two rows (Category 1 Backup,
        Category 3 Backup), per Section 2."""
        return [
            provider
            for provider in self._by_role.values()
            if provider.provider_name == provider_name
        ]

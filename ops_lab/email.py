"""Consent-aware planning only; there is deliberately no mail transport."""
from dataclasses import dataclass, field
import hashlib
import json


def approval_digest(row: dict) -> str:
    """Content binding for a simulated review; this is not authentication."""
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass
class EmailPlanner:
    suppressed: set = field(default_factory=set)
    uncertain: set = field(default_factory=set)
    planned: set = field(default_factory=set)
    daily: dict = field(default_factory=dict)
    last_at: int | None = None

    def plan(self, row: dict, approved_digest: str, at: int) -> str:
        # Synthetic clock: integer seconds from demo day zero, UTC.
        address = row.get('email', '').strip().lower()
        if not address.endswith('@example.invalid') or address.count('@') != 1:
            return 'held:fixture_only'
        if address in self.suppressed:
            return 'held:suppressed'
        if address in self.uncertain:
            return 'held:manual_review'
        consent = row.get('consent', {})
        if (consent.get('status') != 'granted' or not consent.get('evidence')
                or consent.get('scope') != row.get('purpose')
                or not consent.get('scope')
                or not consent.get('valid_from', 1) <= at <= consent.get('valid_until', -1)):
            return 'held:consent'
        if approval_digest(row) != approved_digest:
            return 'held:approval'
        if address in self.planned:
            return 'held:duplicate'
        if self.last_at is not None and at - self.last_at < 120:
            return 'held:spacing'
        day = at // 86400
        if self.daily.get(day, 0) >= 200:
            return 'held:daily_cap'
        self.planned.add(address)
        self.daily[day] = self.daily.get(day, 0) + 1
        self.last_at = at
        return 'dry_run:planned'

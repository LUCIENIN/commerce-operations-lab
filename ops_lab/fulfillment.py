"""In-memory state machine, with synthetic milestones and no external effects."""
from dataclasses import dataclass, field

STEPS = {
    'approve': ('needs_review', 'approved'),
    'label': ('approved', 'label_simulated'),
    'message': ('label_simulated', 'message_simulated'),
    'confirm': ('message_simulated', 'confirmation_simulated'),
}


@dataclass
class Fulfillment:
    order_id: str
    complete: bool = True
    uncertain: bool = False
    state: str = 'needs_review'
    audit: list = field(default_factory=list)

    def __post_init__(self):
        if not self.order_id.startswith('demo-order-'):
            raise ValueError('Synthetic order reference required')

    def advance(self, event: str) -> str:
        if self.uncertain:
            return 'held:manual_review'
        if not self.complete:
            return 'held:incomplete_order'
        if event in [entry['event'] for entry in self.audit]:
            return 'simulated:already_applied'
        if event not in STEPS or STEPS[event][0] != self.state:
            return 'held:invalid_transition'
        previous, self.state = STEPS[event]
        self.audit.append({'sequence': len(self.audit) + 1, 'event': event,
                           'from': previous, 'to': self.state, 'order': self.order_id})
        return 'simulated:applied'

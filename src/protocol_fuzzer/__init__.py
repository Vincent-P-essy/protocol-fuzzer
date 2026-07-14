"""Coverage-guided, grammar-based protocol fuzzer with crash triage."""

from .engine import run_campaign
from .models import CampaignConfig, CampaignResult, CrashBucket, Protocol

__all__ = [
    "CampaignConfig",
    "CampaignResult",
    "CrashBucket",
    "Protocol",
    "run_campaign",
]
__version__ = "0.2.0"

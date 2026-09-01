from dataclasses import dataclass

from app.models.call import CallState


@dataclass
class ProviderEvent:

    provider_name: str
    provider_call_id: str
    call_state: CallState
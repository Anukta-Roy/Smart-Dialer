import random
import time
import uuid

from app.providers.base_provider import BaseProvider
from app.providers.provider_event import ProviderEvent
from app.models.call import CallState


class ProviderB(BaseProvider):

    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:
        """
        Provider B simulation.

        Characteristics:
        - Slower than Provider A
        - Occasional timeouts
        """

        # Simulate slower provider latency
        time.sleep(
            random.uniform(0.1, 0.3)
        )

        # Higher failure probability: 25%
        if random.random() < 0.25:

            raise TimeoutError(
                "Provider B timed out "
                "while initiating call"
            )

        # Generate simulated provider call ID
        provider_call_id = (
            f"provider_b_{uuid.uuid4()}"
        )

        print(
            f"[Provider B] Initiated "
            f"{provider_call_id} "
            f"for {borrower_phone}"
        )

        return provider_call_id


    def cancel_call(
        self,
        provider_call_id: str
    ) -> bool:
        """
        Simulate cancelling a call.
        """

        print(
            f"[Provider B] Cancelled "
            f"{provider_call_id}"
        )

        return True


    def get_provider_name(self) -> str:
        """
        Return provider name.
        """

        return "ProviderB"


    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:
        """
        Return simulated Provider B events.

        Provider B deliberately generates:
        - Duplicate events
        - Out-of-order events
        """

        return [

            # Normal event
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.RINGING
            ),

            # Normal event
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.ANSWERED
            ),

            # Duplicate event
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.ANSWERED
            ),

            # Out-of-order stale event
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.RINGING
            ),

            # Normal progression
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.CONNECTED
            ),

            # Terminal event
            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.COMPLETED
            )
        ]
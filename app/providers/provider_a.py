import random
import time
import uuid

from app.providers.base_provider import BaseProvider
from app.providers.provider_event import ProviderEvent
from app.models.call import CallState


class ProviderA(BaseProvider):

    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:
        """
        Provider A simulation.

        Characteristics:
        - Fast
        - Reliable
        - Low failure rate
        """

        # Simulate fast provider latency
        time.sleep(
            random.uniform(0.01, 0.05)
        )

        # Low failure probability: 5%
        if random.random() < 0.05:

            raise TimeoutError(
                "Provider A failed to initiate call"
            )

        # Generate simulated provider call ID
        provider_call_id = (
            f"provider_a_{uuid.uuid4()}"
        )

        print(
            f"[Provider A] Initiated "
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
            f"[Provider A] Cancelled "
            f"{provider_call_id}"
        )

        return True


    def get_provider_name(self) -> str:
        """
        Return provider name.
        """

        return "ProviderA"


    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:
        """
        Return a clean and ordered call
        lifecycle for Provider A.
        """

        return [

            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.RINGING
            ),

            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.ANSWERED
            ),

            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.CONNECTED
            ),

            ProviderEvent(
                provider_name=self.get_provider_name(),
                provider_call_id=provider_call_id,
                call_state=CallState.COMPLETED
            )
        ]
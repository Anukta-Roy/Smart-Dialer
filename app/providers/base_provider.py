from abc import ABC, abstractmethod


class BaseProvider(ABC):

    @abstractmethod
    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:
        pass


    @abstractmethod
    def cancel_call(
        self,
        provider_call_id: str
    ) -> bool:
        pass


    @abstractmethod
    def get_provider_name(self) -> str:
        pass


    @abstractmethod
    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:
        """
        Return simulated call lifecycle events.
        """

        pass
from app.providers.provider_a import ProviderA
from app.models.call import CallState


def test_provider_a_returns_name():

    provider = ProviderA()

    assert (
        provider.get_provider_name()
        == "ProviderA"
    )


def test_provider_a_initiates_call():

    provider = ProviderA()

    successful_call = False

    # Provider A has a small simulated failure rate,
    # so try multiple times.
    for _ in range(20):

        try:

            provider_call_id = (
                provider.initiate_call(
                    call_id="test-call-123",
                    borrower_phone="9999999999"
                )
            )

            assert provider_call_id.startswith(
                "provider_a_"
            )

            successful_call = True

            break

        except TimeoutError:
            pass

    assert successful_call is True


def test_provider_a_cancels_call():

    provider = ProviderA()

    result = provider.cancel_call(
        provider_call_id="provider_a_test"
    )

    assert result is True


def test_provider_a_generates_ordered_events():

    provider = ProviderA()

    events = provider.get_call_events(
        provider_call_id="provider_a_test"
    )

    states = [
        event.call_state
        for event in events
    ]

    assert states == [

        CallState.RINGING,

        CallState.ANSWERED,

        CallState.CONNECTED,

        CallState.COMPLETED
    ]
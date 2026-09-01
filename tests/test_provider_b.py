from app.providers.provider_b import ProviderB
from app.models.call import CallState


def test_provider_b_returns_name():

    provider = ProviderB()

    assert (
        provider.get_provider_name()
        == "ProviderB"
    )


def test_provider_b_can_initiate_call():

    provider = ProviderB()

    successful_call = False

    # Provider B intentionally has a higher timeout rate.
    for _ in range(20):

        try:

            provider_call_id = (
                provider.initiate_call(
                    call_id="test-call-456",
                    borrower_phone="8888888888"
                )
            )

            assert provider_call_id.startswith(
                "provider_b_"
            )

            successful_call = True

            break

        except TimeoutError:
            pass

    assert successful_call is True


def test_provider_b_cancels_call():

    provider = ProviderB()

    result = provider.cancel_call(
        provider_call_id="provider_b_test"
    )

    assert result is True


def test_provider_b_generates_duplicate_and_out_of_order_events():

    provider = ProviderB()

    events = provider.get_call_events(
        provider_call_id="provider_b_test"
    )

    states = [
        event.call_state
        for event in events
    ]

    assert states == [

        CallState.RINGING,

        CallState.ANSWERED,

        # Duplicate
        CallState.ANSWERED,

        # Out-of-order stale event
        CallState.RINGING,

        CallState.CONNECTED,

        CallState.COMPLETED
    ]
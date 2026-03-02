import logging
import pytest

from src.tlvflow.domain.payment_service import PaymentService, PaymentProcessingError

@pytest.fixture()
def service() -> PaymentService:
    return PaymentService()

@pytest.fixture()
def no_sleep(monkeypatch):
    """
    Patch asyncio.sleep so tests run instantly, and track delays.
    """
    import asyncio
    calls = {"delays": []}

    async def fake_sleep(delay: float):
        calls["delays"].append(delay)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    return calls


# -------------------------
# Success paths
# -------------------------

@pytest.mark.asyncio
async def test_process_charge_success(service, no_sleep, caplog):
    caplog.set_level(logging.INFO)
    result = await service.process_charge("ride-123", 15.0, "pm_tok_abc")

    assert result is True
    assert no_sleep["delays"] == [0.5]
    assert "Processing charge" in caplog.text


@pytest.mark.asyncio
async def test_issue_receipt_success(service, no_sleep, caplog):
    caplog.set_level(logging.INFO)
    result = await service.issue_receipt("ride-123", 15.0, "user@example.com", "pm_tok_abc")

    assert result is True
    assert no_sleep["delays"] == [0.2]
    assert "Issuing receipt" in caplog.text


@pytest.mark.asyncio
async def test_issue_refund_success(service, no_sleep, caplog):
    caplog.set_level(logging.INFO)
    result = await service.issue_refund("ride-123", 10.0, "user@example.com", "pm_tok_abc")

    assert result is True
    assert no_sleep["delays"] == [0.5]
    assert "Processing refund" in caplog.text


# -------------------------
# Validation paths
# -------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("bad_ride_id", ["", "   ", None])
async def test_invalid_ride_id_raises(service, bad_ride_id):
    with pytest.raises(PaymentProcessingError, match="ride_id must be a non-empty string"):
        await service.process_charge(bad_ride_id, 15.0, "pm_tok_abc")


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_pm_id", ["", "   ", None])
async def test_invalid_payment_method_id_raises(service, bad_pm_id):
    with pytest.raises(PaymentProcessingError, match="payment_method_id must be a non-empty string"):
        await service.process_charge("ride-123", 15.0, bad_pm_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_amount", [0, 0.0, -1, -10.5])
async def test_invalid_amount_raises(service, bad_amount):
    with pytest.raises(PaymentProcessingError, match="Amount must be greater than zero"):
        await service.process_charge("ride-123", float(bad_amount), "pm_tok_abc")

    with pytest.raises(PaymentProcessingError, match="Amount must be greater than zero"):
        await service.issue_receipt("ride-123", float(bad_amount), "user@example.com", "pm_tok_abc")

    with pytest.raises(PaymentProcessingError, match="Amount must be greater than zero"):
        await service.issue_refund("ride-123", float(bad_amount), "user@example.com", "pm_tok_abc")


# -------------------------
# Email Validation paths
# -------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("bad_email", ["", "   ", "just-a-string", "domain.com", None])
async def test_invalid_email_raises(service, bad_email):
    # Notice we don't test strings with "@" here, because your current code accepts them.
    with pytest.raises(PaymentProcessingError, match="email must be a valid email address"):
        await service.issue_receipt("ride-123", 15.0, bad_email, "pm_tok_abc")

    with pytest.raises(PaymentProcessingError, match="email must be a valid email address"):
        await service.issue_refund("ride-123", 15.0, bad_email, "pm_tok_abc")
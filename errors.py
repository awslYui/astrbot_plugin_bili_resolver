class BiliRiskControlError(RuntimeError):
    """Raised when Bilibili rejects a request with HTTP 412."""

    def __init__(self, url: str = ""):
        super().__init__("Bilibili risk control rejected the request (HTTP 412)")
        self.url = url


def raise_for_risk_control_payload(payload, url: str = "") -> None:
    """Handle Bilibili APIs that report -412 inside a JSON response."""
    if isinstance(payload, dict) and payload.get("code") in (-412, 412):
        raise BiliRiskControlError(url)

from pydantic import BaseModel

from typing import List, Optional, Dict


class GoogleAnalytics(BaseModel):
    client_id: Optional[str] = None


class Amplitude(BaseModel):
    user_id: Optional[str] = None
    device_id: Optional[str] = None


class Klaviyo(BaseModel):
    profile_id: Optional[str] = None


class Identity(BaseModel):
    google_analytics: Optional[GoogleAnalytics] = None
    amplitude: Optional[Amplitude] = None
    klaviyo: Optional[Klaviyo] = None


class Metadata(BaseModel):
    sdk_version: Optional[str] = None
    analytics_services: Optional[List[str]] = []
    callback_webhook: Optional[str] = None


# class EventData(BaseModel):
#     product_id: str
#     product_category: str
#     product_price: float
#     more: str


class AnalyticsIn(BaseModel):
    event_id: str
    app_id: str
    event_name: str
    event_data: dict
    identity: Identity
    metadata: Metadata = {}

    class Config:
        schema_extra = {
            "example": {
                "event_id": "4f5d6e7a-8b9c-10d1-11e2-12f3456g7h8i",
                "app_id": "esa",
                "event_name": "cart_add",
                "event_data": {
                    "product_id": "ESAREG",
                    "product_category": "S Bensuttation",
                    "product_price": 129.99,
                    "more": ""
                },
                "identity": {
                    "google_analytics": {
                        "client_id": ""
                    },
                    "amplitude": {
                        "client_id": "",
                        "device_id": ""
                    },
                    "klaviyo": {}
                },
                "metadata": {
                    "sdk_version": "1.2.3",
                    "analytics_services": ["google_analytics", "amplitude", "klaviyo"],
                    "callback_webhook": "https://intellipet.org/api/webhook-endpoint"
                }
            }
        }

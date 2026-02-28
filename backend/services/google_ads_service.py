"""
Google Ads API Integration (Stub)

This module is a placeholder for future Google Ads API integration
to get real search volume data via KeywordPlanIdeaService.

=== HOW TO SET UP GOOGLE ADS API ===

1. Create a Google Ads Manager Account:
   - Go to https://ads.google.com/home/tools/manager-accounts/
   - Sign up for a Manager Account (MCC)

2. Apply for API Developer Token:
   - In Google Ads UI: Tools & Settings > Setup > API Center
   - Apply for a Developer Token
   - Note: Basic access is sufficient for keyword research
   - Approval may take a few days

3. Create OAuth2 Credentials:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing
   - Enable "Google Ads API"
   - Go to Credentials > Create Credentials > OAuth 2.0 Client ID
   - Application type: Desktop App
   - Download the client_secret.json

4. Generate Refresh Token:
   - pip install google-ads
   - Run: google-ads-generate-refresh-token
   - Follow the OAuth flow in browser
   - Save the refresh token

5. Configure environment variables:
   GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
   GOOGLE_ADS_CLIENT_ID=your_client_id
   GOOGLE_ADS_CLIENT_SECRET=your_client_secret
   GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
   GOOGLE_ADS_CUSTOMER_ID=your_customer_id (without dashes)

6. Usage with KeywordPlanIdeaService:
   The service provides:
   - Monthly search volume (avg)
   - Competition level (LOW/MEDIUM/HIGH)
   - Top-of-page bid estimates
   - Seasonal trends (12-month breakdown)
"""

import logging

logger = logging.getLogger(__name__)


async def fetch_search_volumes(keywords: list[str]) -> dict[str, dict]:
    """
    Stub: Fetch real search volumes from Google Ads API.

    Returns dict like:
    {
        "ai video generator": {
            "avg_monthly_searches": 12000,
            "competition": 0.85,
            "competition_level": "HIGH",
            "top_of_page_bid_low": 1.20,
            "top_of_page_bid_high": 5.50,
            "monthly_search_volumes": [...]
        }
    }
    """
    logger.info(
        "Google Ads API not configured. "
        "See google_ads_service.py for setup instructions."
    )
    return {}

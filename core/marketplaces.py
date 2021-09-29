import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


MARKETPLACES_TEMPLATES = {
    "de": {
        "domain": "de",
        "market_place_id": "AN7V1F1VY261K",
        "country": "Germany"
    },
    "us": {
        "domain": "com",
        "market_place_id": "AF2M0KC94RCEA",
        "country": "United States"
    },
    "uk": {
        "domain": "co.uk",
        "market_place_id": "A2I9A3Q2GNFNGQ",
        "country": "United Kingdom"
    },
    "fr": {
        "domain": "fr",
        "market_place_id": "A2728XDNODOQ8T",
        "country": "France"
    },
    "ca": {
        "domain": "ca",
        "market_place_id": "A2CQZ5RBY40XE",
        "country": "Canada"
    },
    "it": {
        "domain": "it",
        "market_place_id": "A2N7FU2W2BU2ZC",
        "country": "Italy"
    },
    "au": {
        "domain": "com.au",
        "market_place_id": "AN7EY7DTAW63G",
        "country": "Australia"
    },
    "in": {
        "domain": "in",
        "market_place_id": "AJO3FBRUE6J4S",
        "country": "India"
    },
    "jp": {
        "domain": "co.jp",
        "market_place_id": "A1QAP3MOU4173J",
        "country": "Japan"
    },
    "es": {
        "domain": "es",
        "market_place_id": "ALMIKO4SZCSAR",
        "country": "Spain"
    }
}


def get_marketplaces_choices():
    mlist = []
    for country_code in MARKETPLACES_TEMPLATES:
        country = MARKETPLACES_TEMPLATES[country_code]['country']
        mlist.append([country_code, country])
    sorted_mlist = sorted(mlist, key=lambda x: x[0])
    return sorted_mlist


def search_template(key: str, value: str) -> Optional[Dict[str, str]]:
    for country_code in MARKETPLACES_TEMPLATES:
        market = MARKETPLACES_TEMPLATES[country_code]
        market['country_code'] = country_code

        if key not in market:
            msg = f"{key} is not a valid key to search for."
            logger.error(msg)
            raise Exception(msg)

        if market[key] == value:
            logger.debug(f"Found marketplace for {country_code}")
            return market

    msg = f"Can't find {value} in {key}"
    logger.info(msg)
    raise Exception(msg)


class Marketplace:
    """
    Instance for an Audible marketplace
    
    """

    def __init__(
            self,
            country_code: str,
            domain: str,
            market_place_id: str,
            country: str
    ) -> None:
        self.country_code = country_code
        self.domain = domain
        self.market_place_id = market_place_id
        self.country = country

    def __repr__(self):
        return (
            f"Audible marketplace for {self.country}"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "country_code": self.country_code,
            "domain": self.domain,
            "market_place_id": self.market_place_id,
            "country": self.country
        }

    @classmethod
    def from_country_code(cls, country_code: str) -> "Marketplace":
        market = search_template(key='country_code', value=country_code)
        market = cls(**market)
        return market
 

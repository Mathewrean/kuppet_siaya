VALID_SUBCOUNTIES = (
    "Alego Usonga",
    "Bondo",
    "Usigu",
    "Ugenya",
    "Rarieda",
    "Gem",
    "Siaya",
    "Ugunja",
)

SUBCOUNTY_ALIASES = {
    "alego usonga": "Alego Usonga",
    "bondo": "Bondo",
    "usigu": "Usigu",
    "ugenya": "Ugenya",
    "rarieda": "Rarieda",
    "gem": "Gem",
    "siaya": "Siaya",
    "ugunja": "Ugunja",
    "ukwala": "Ugunja",
}


def normalize_subcounty_name(value):
    if not value:
        return ""

    normalized = " ".join(str(value).split()).strip()
    return SUBCOUNTY_ALIASES.get(normalized.lower(), normalized)


def is_valid_subcounty(value):
    return normalize_subcounty_name(value) in VALID_SUBCOUNTIES

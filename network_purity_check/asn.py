DATACENTER_KEYWORDS = (
    "amazon",
    "aws",
    "google",
    "digitalocean",
    "azure",
    "linode",
    "ovh",
    "hetzner",
)

RESIDENTIAL_KEYWORDS = (
    "comcast",
    "verizon",
    "spectrum",
    "cox",
    "att",
    "china mobile",
    "china unicom",
    "china telecom",
)


def classify_asn(org: str) -> str:
    normalized = org.lower()
    if any(k in normalized for k in DATACENTER_KEYWORDS):
        return "datacenter"
    if any(k in normalized for k in RESIDENTIAL_KEYWORDS):
        return "residential"
    return "unknown"

"""Search metadata for the two native, Estonia-focused website versions.

Locale links follow Google's HTML hreflang guidance:
https://developers.google.com/search/docs/specialty/international/localized-versions
The graph describes the published organization and services without implying a
public shop, office address, reviews, or other unverified business attributes:
https://schema.org/Service and https://schema.org/WebPage
"""

from html import escape
import json
from pathlib import Path


BASE_URL = "https://lanehitus.ee"
PAGE_PATHS = {"et": "/", "ru": "/ru/"}
REGIONS = {"et": "et-EE", "ru": "ru-EE"}
SOCIAL_IMAGE_PATH = "/images/services/terrace-premium-townhouse-main-v1.jpg"
SOCIAL_IMAGE_URL = BASE_URL + SOCIAL_IMAGE_PATH
SOCIAL_IMAGE_ALTS = {
    "et": "Terrass ridaelamu juures — teenust illustreeriv foto",
    "ru": "Терраса у таунхауса — иллюстрация услуги",
}
SERVICE_NAMES = {
    "et": {
        "terraces": "Terrasside ehitus ja uuendamine",
        "drywall": "Kipsitööd",
        "flooring": "Parketi ja laminaadi paigaldus",
        "doors": "Uste paigaldus ja eemaldamine",
        "furniture": "Mööbli kokkupanek",
    },
    "ru": {
        "terraces": "Строительство и обновление террас",
        "drywall": "Монтаж гипсокартона",
        "flooring": "Укладка паркета и ламината",
        "doors": "Установка и демонтаж дверей",
        "furniture": "Сборка мебели",
    },
}


def _meta(attribute: str, name: str, value: str) -> str:
    """Build a metadata tag with quoted, HTML-escaped attribute values."""
    return f'<meta {attribute}="{escape(name, quote=True)}" content="{escape(value, quote=True)}">'


def _structured_data(language: str, title: str, description: str) -> dict:
    """Return factual Schema.org nodes linked by stable absolute identifiers."""
    page_url = BASE_URL + PAGE_PATHS[language]
    organization_id = BASE_URL + "/#organization"
    website_id = BASE_URL + "/#website"
    organization = {"@id": organization_id}
    service_ids = [page_url + "#" + slug for slug in SERVICE_NAMES[language]]
    country = {"@type": "Country", "name": "Estonia", "identifier": "EE"}
    area_served = [
        {"@type": "City", "name": "Tallinn", "containedInPlace": country},
        {"@type": "AdministrativeArea", "name": "Harjumaa", "containedInPlace": country},
    ]
    graph = [
        {
            "@type": "Organization",
            "@id": organization_id,
            "name": "LAN OÜ",
            "legalName": "LAN OÜ",
            "alternateName": "LAN Ehitus",
            "identifier": "17505187",
            "url": BASE_URL + "/",
            "logo": BASE_URL + "/images/brand/lan-ehitus-original.jpeg",
            "areaServed": area_served,
        },
        {
            "@type": "WebSite",
            "@id": website_id,
            "url": BASE_URL + "/",
            "name": "LAN Ehitus",
            "inLanguage": list(REGIONS.values()),
            "publisher": organization,
        },
        {
            "@type": "WebPage",
            "@id": page_url + "#webpage",
            "url": page_url,
            "name": title,
            "description": description,
            "inLanguage": REGIONS[language],
            "isPartOf": {"@id": website_id},
            "about": organization,
            "mainEntity": [{"@id": service_id} for service_id in service_ids],
        },
    ]
    for slug, name in SERVICE_NAMES[language].items():
        service_url = page_url + "#" + slug
        graph.append({
            "@type": "Service",
            "@id": service_url,
            "url": service_url,
            "name": name,
            "provider": organization,
            "areaServed": area_served,
        })
    return {"@context": "https://schema.org", "@graph": graph}


def render_metadata(language: str, title: str, description: str) -> str:
    """Render head tags for ``et`` or ``ru`` using already localized copy.

    This helper is pure: it does not read files, write files, or use a network.
    Escaping covers HTML attribute boundaries and literal script terminators in
    the JSON-LD payload, so callers can safely pass arbitrary title/description
    text without creating markup.
    """
    if language not in PAGE_PATHS:
        raise ValueError(f"Unsupported SEO language: {language!r}")
    page_url = BASE_URL + PAGE_PATHS[language]
    image_alt = SOCIAL_IMAGE_ALTS[language]
    tags = [f'<link rel="canonical" href="{page_url}">']
    tags.extend(
        f'<link rel="alternate" hreflang="{REGIONS[code]}" href="{BASE_URL}{path}">'
        for code, path in PAGE_PATHS.items()
    )
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/">')
    tags.append(_meta("name", "robots", "index,follow,max-image-preview:large"))
    for name, value in [
        ("og:type", "website"),
        ("og:site_name", "LAN Ehitus"),
        ("og:title", title),
        ("og:description", description),
        ("og:url", page_url),
        ("og:locale", REGIONS[language].replace("-", "_")),
        ("og:image", SOCIAL_IMAGE_URL),
        ("og:image:type", "image/jpeg"),
        ("og:image:width", "1536"),
        ("og:image:height", "1024"),
        ("og:image:alt", image_alt),
    ]:
        tags.append(_meta("property", name, value))
    for code, region in REGIONS.items():
        if code != language:
            tags.append(_meta("property", "og:locale:alternate", region.replace("-", "_")))
    for name, value in [
        ("twitter:card", "summary_large_image"),
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:image", SOCIAL_IMAGE_URL),
        ("twitter:image:alt", image_alt),
    ]:
        tags.append(_meta("name", name, value))
    payload = json.dumps(
        _structured_data(language, title, description),
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    tags.append(f'<script type="application/ld+json">{payload}</script>')
    return "\n".join(tags)


def write_crawler_files(root: Path) -> None:
    """Write deterministic crawler files alongside the generated site pages.

    Only the two canonical pages belong in this sitemap. Language alternatives
    live in HTML, and no modification dates or crawl priorities are fabricated.
    """
    root = Path(root)
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"
    (root / "robots.txt").write_text(robots, encoding="utf-8")
    entries = "\n".join(
        f"  <url><loc>{BASE_URL}{path}</loc></url>"
        for path in PAGE_PATHS.values()
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n"
    )
    (root / "sitemap.xml").write_text(sitemap, encoding="utf-8")

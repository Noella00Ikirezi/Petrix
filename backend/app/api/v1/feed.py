"""Proxy serveur-side pour les flux RSS CERT-FR (ANSSI) : alertes, avis, durcissement et IOC.
Contourne les restrictions CORS du navigateur, enrichit chaque item avec une sévérité déduite et corrèle
les vulnérabilités Petrix avec les avis CERT-FR par intersection des identifiants CVE.
"""
import asyncio
import re
from xml.etree import ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, Vulnerability, VulnStatus

router = APIRouter()

_FEEDS = {
    "alerte":   "https://cert.ssi.gouv.fr/alerte/feed/",
    "avis":     "https://cert.ssi.gouv.fr/avis/feed/",
    "dur":      "https://cert.ssi.gouv.fr/dur/feed/",
    "ioc":      "https://cert.ssi.gouv.fr/ioc/feed/",
    "actualite":"https://cert.ssi.gouv.fr/actualite/feed/",
}

_FEED_LABELS = {
    "alerte":   "Alertes de sécurité",
    "avis":     "Avis de sécurité",
    "dur":      "Durcissement (ANSSI)",
    "ioc":      "Indicateurs de compromission",
    "actualite":"Actualités CERT-FR",
}

_SEVERITY_KEYWORDS = {
    "CRITICAL": ["critique", "critical", "0-day", "zero-day", "ransomware",
                 "exploitation active", "exécution de code arbitraire à distance"],
    "HIGH":     ["élevé", "high", "important", "élévation de privilèges",
                 "contournement de sécurité"],
    "MEDIUM":   ["moyen", "medium", "modéré"],
    "LOW":      ["faible", "low"],
}


def _strip_html(text: str) -> str:
    """Supprime les balises HTML et les artéfacts Markdown résiduels pour produire un texte brut."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    # Nettoyer les balises Markdown résiduelles CERT-FR
    text = re.sub(r"\\\[([^\]]*)\\\]", r"[\1]", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _guess_severity(text: str) -> str:
    """Déduit la sévérité (CRITICAL/HIGH/MEDIUM/LOW) d'un texte CERT-FR par correspondance de mots-clés."""
    t = text.lower()
    for sev, keywords in _SEVERITY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return sev
    return "MEDIUM"


def _extract_cert_id(title: str, link: str) -> str:
    """Extrait l'identifiant CERTFR-XXXX-XXX-NNN depuis l'URL ou, en fallback, depuis le titre."""
    # L'identifiant CERTFR est dans l'URL : /alerte/CERTFR-2025-ALE-001/
    m = re.search(r"CERTFR-\d{4}-[A-Z]+-\d+", link, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    # Fallback : chercher dans le titre
    m = re.search(r"CERTFR-\d{4}-[A-Z]+-\d+", title, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    return ""


def _fetch_rss(feed_type: str) -> dict:
    """Télécharge et parse le flux RSS CERT-FR du type demandé ; retourne les 30 derniers items enrichis (sévérité, CVE)."""
    url = _FEEDS.get(feed_type)
    if not url:
        raise ValueError(f"Feed inconnu : {feed_type}")

    req = Request(url, headers={
        "User-Agent": "Petrix-Security-Platform/1.0 (+https://petrix.local)",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })

    try:
        with urlopen(req, timeout=15) as resp:
            raw = resp.read()
    except HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"CERT-FR HTTP {exc.code}: {exc.reason}")
    except URLError as exc:
        raise HTTPException(status_code=503, detail=f"CERT-FR inaccessible : {exc.reason}")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise HTTPException(status_code=502, detail=f"Flux RSS invalide : {exc}")

    channel = root.find("channel")
    if channel is None:
        return {"items": [], "feed_description": ""}

    feed_desc = (channel.findtext("description") or "").strip()
    items = []

    for item in channel.findall("item")[:30]:
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link")  or "").strip()
        pub   = (item.findtext("pubDate") or "").strip()
        desc  = _strip_html(item.findtext("description") or "")

        # Identifier le numéro CERTFR depuis le lien (plus fiable que le titre)
        cert_id = _extract_cert_id(title, link)

        # Extraire les CVE mentionnées dans la description
        cves = sorted(set(re.findall(r"CVE-\d{4}-\d{4,}", desc, re.IGNORECASE)))[:6]

        severity = _guess_severity(title + " " + desc)

        items.append({
            "cert_id":   cert_id or title[:40],
            "title":     title,
            "link":      link,
            "published": pub,
            "summary":   desc[:2000].strip(),
            "severity":  severity,
            "cves":      cves,
            "feed_type": feed_type,
        })

    return {
        "feed_type":        feed_type,
        "feed_label":       _FEED_LABELS.get(feed_type, feed_type),
        "feed_description": feed_desc,
        "source":           f"https://www.cert.ssi.gouv.fr/{feed_type}/",
        "items":            items,
    }


@router.get("/cert-fr")
async def get_cert_fr_feed(
    feed_type: str = Query("alerte", enum=["alerte", "avis", "dur", "ioc", "actualite"]),
    current_user: User = Depends(get_current_user),
):
    """Proxy les flux RSS CERT-FR (ANSSI) depuis le serveur — contourne les restrictions CORS côté navigateur."""
    result = await asyncio.to_thread(_fetch_rss, feed_type)
    return result


def _scrape_fiche(cert_id: str, feed_type: str = "alerte") -> dict:
    """Scrape la page HTML d'une alerte CERT-FR et retourne les sections structurées."""
    cert_id_clean = cert_id.upper().strip()
    url = f"https://www.cert.ssi.gouv.fr/{feed_type}/{cert_id_clean}/"

    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Petrix-Security/1.0)",
        "Accept-Language": "fr-FR,fr;q=0.9",
    })

    try:
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise HTTPException(status_code=404, detail=f"Fiche introuvable : {exc.code}")
    except URLError as exc:
        raise HTTPException(status_code=503, detail=f"CERT-FR inaccessible : {exc.reason}")

    def clean(text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text or "")
        text = re.sub(r"<p[^>]*>", "\n", text)
        text = re.sub(r"</p>", "", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&#\d+;", "", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def extract_list(html_block: str) -> list[str]:
        items = re.findall(r"<li[^>]*>(.*?)</li>", html_block, re.S)
        return [clean(i) for i in items if clean(i) and len(clean(i)) > 2]

    # Découper par sections h2
    parts = re.split(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)
    sections: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        title = re.sub(r"<[^>]+>", "", parts[i]).strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections[title] = content

    # Métadonnées depuis la table "Gestion du document"
    meta: dict[str, str] = {}
    for section_name, section_html in sections.items():
        if "Gestion" in section_name:
            for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", section_html, re.S):
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row.group(1), re.S)
                if len(cells) >= 2:
                    k = clean(cells[0])
                    v = clean(cells[1])
                    if k and v:
                        meta[k] = v
            break

    # Risques, systèmes affectés, textes
    risks    = extract_list(sections.get("Risque", ""))
    affected = extract_list(sections.get("Systèmes affectés", ""))
    summary  = clean(re.sub(r"<ul.*?</ul>", "", sections.get("Résumé", ""), flags=re.S))
    workaround = clean(sections.get("Contournement provisoire", ""))
    solution   = clean(sections.get("Solutions", "") or sections.get("Solution", ""))

    # CVE + références depuis Documentation
    doc_html = sections.get("Documentation", "")
    cves = sorted(set(re.findall(r"CVE-\d{4}-\d{4,}", doc_html, re.I)))
    refs = [r for r in extract_list(doc_html) if len(r) > 8]

    # Gravité déduite des risques
    combined = " ".join(risks).lower()
    if any(k in combined for k in ["arbitraire à distance", "0-day", "zero-day", "ransomware", "critique"]):
        severity = "CRITICAL"
    elif any(k in combined for k in ["élévation", "contournement", "déni de service"]):
        severity = "HIGH"
    else:
        severity = "MEDIUM"

    return {
        "cert_id":    cert_id_clean,
        "url":        url,
        "feed_type":  feed_type,
        "title":      meta.get("Titre", cert_id_clean),
        "reference":  meta.get("Référence", cert_id_clean),
        "published":  meta.get("Date de la première version", ""),
        "updated":    meta.get("Date de la dernière version", ""),
        "source":     meta.get("Source(s)", ""),
        "severity":   severity,
        "risks":      risks,
        "affected_systems": affected,
        "summary":    summary[:3000],
        "workaround": workaround[:2000],
        "solution":   solution[:2000],
        "cves":       cves,
        "references": refs[:20],
    }


@router.get("/cert-fr/fiche")
async def get_cert_fr_fiche(
    cert_id: str = Query(..., description="Ex: CERTFR-2024-ALE-004"),
    feed_type: str = Query("alerte", enum=["alerte", "avis", "dur", "ioc", "actualite"]),
    current_user: User = Depends(get_current_user),
):
    """Scrape et retourne la fiche complète d'une alerte CERT-FR."""
    if not re.match(r"^CERTFR-\d{4}-[A-Z]+-\d+$", cert_id.upper(), re.I):
        raise HTTPException(status_code=400, detail="Format cert_id invalide")
    return await asyncio.to_thread(_scrape_fiche, cert_id, feed_type)


@router.get("/cert-fr/multi")
async def get_cert_fr_multi(
    current_user: User = Depends(get_current_user),
):
    """Récupère alertes + avis en une seule requête."""
    alertes, avis = await asyncio.gather(
        asyncio.to_thread(_fetch_rss, "alerte"),
        asyncio.to_thread(_fetch_rss, "avis"),
    )

    combined = alertes["items"] + avis["items"]
    combined.sort(key=lambda x: x.get("published", ""), reverse=True)

    return {
        "items":   combined[:40],
        "sources": {
            "alerte":  alertes["source"],
            "avis":    avis["source"],
        },
    }


@router.get("/vuln-correlations")
async def get_vuln_correlations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Corrèle les vulnérabilités Petrix (ouvertes, avec CVE) avec les alertes CERT-FR
    en faisant une intersection sur les CVE IDs.
    Retourne uniquement les vulnérabilités ayant au moins une alerte CERT-FR associée.
    """
    # Vulns ouvertes avec au moins un CVE ID
    open_vulns = (
        db.query(Vulnerability)
        .filter(
            Vulnerability.status == VulnStatus.OPEN,
            Vulnerability.cve_ids.isnot(None),
        )
        .all()
    )
    # Garder seulement celles qui ont au moins un CVE
    vulns_with_cves = [v for v in open_vulns if v.cve_ids]
    if not vulns_with_cves:
        return {"correlations": [], "cert_items_fetched": 0}

    alertes, avis = await asyncio.gather(
        asyncio.to_thread(_fetch_rss, "alerte"),
        asyncio.to_thread(_fetch_rss, "avis"),
    )
    cert_items = alertes["items"] + avis["items"]

    # Indexation des items CERT-FR par CVE pour une corrélation en O(1)
    cve_to_certs: dict[str, list[dict]] = {}
    for item in cert_items:
        for cve in item.get("cves", []):
            cve_upper = cve.upper()
            cve_to_certs.setdefault(cve_upper, []).append({
                "cert_id":  item.get("cert_id", ""),
                "title":    item.get("title", ""),
                "link":     item.get("link", ""),
                "severity": item.get("severity", "MEDIUM"),
                "published":item.get("published", ""),
            })

    correlations = []
    for v in vulns_with_cves:
        matched_certs = []
        matched_cves = []
        for cve in v.cve_ids:
            cve_upper = cve.upper()
            if cve_upper in cve_to_certs:
                matched_certs.extend(cve_to_certs[cve_upper])
                matched_cves.append(cve_upper)

        if matched_certs:
            # Déduplication des alertes par cert_id
            seen = set()
            unique_certs = []
            for c in matched_certs:
                if c["cert_id"] not in seen:
                    seen.add(c["cert_id"])
                    unique_certs.append(c)

            correlations.append({
                "vuln_id":       str(v.id),
                "vuln_title":    v.title,
                "vuln_severity": v.severity.value if hasattr(v.severity, "value") else v.severity,
                "vuln_cve_ids":  v.cve_ids,
                "matched_cves":  matched_cves,
                "cert_alerts":   unique_certs[:5],
            })

    # Tri par nombre d'alertes CERT-FR correspondantes (les plus exposées en premier)
    correlations.sort(key=lambda x: len(x["cert_alerts"]), reverse=True)

    return {
        "correlations":      correlations,
        "cert_items_fetched": len(cert_items),
        "total_correlated":  len(correlations),
    }

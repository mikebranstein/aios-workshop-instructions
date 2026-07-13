import re
from dataclasses import dataclass
from typing import Iterable, Set


_URL_RE = re.compile(r"https?://[^\s)>\"]+")
_DOC_LINK_RE = re.compile(r"docs/adr/[^\s)>\"]+\.md", re.IGNORECASE)


@dataclass(frozen=True)
class EvidenceSnapshot:
    state_label: str
    closed_research_count: int
    relevant_links: frozenset[str]
    adr_links: frozenset[str]
    wiki_links: frozenset[str]


def extract_links(texts: Iterable[str]) -> Set[str]:
    links: Set[str] = set()
    for text in texts:
        for match in _URL_RE.findall(text or ""):
            links.add(match.strip())
        for match in _DOC_LINK_RE.findall(text or ""):
            links.add(match.strip())
    return links


def classify_wiki_links(links: Iterable[str]) -> Set[str]:
    result: Set[str] = set()
    for link in links:
        lowered = link.lower()
        if "/wiki/" in lowered or lowered.startswith("wiki/"):
            result.add(link)
    return result


def classify_adr_links(links: Iterable[str]) -> Set[str]:
    result: Set[str] = set()
    for link in links:
        lowered = link.lower()
        if "/adr/" in lowered or "docs/adr/" in lowered:
            result.add(link)
    return result

import posixpath
import re
from collections.abc import Callable

import defusedxml.ElementTree as ET

# A deck is read by namespace and resolved part path, never by the `p:` prefix or a `slides/` spelling:
# both are serialization choices, and a cleaner that trusts them deletes live slides
PML = "http://schemas.openxmlformats.org/presentationml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
SLIDE_REL = f"{REL}/slide"

PRESENTATION = "ppt/presentation.xml"


def rels_path(part: str) -> str:
    """The relationships part that belongs to `part`."""

    folder, name = posixpath.split(part)
    return posixpath.join(folder, "_rels", f"{name}.rels")


def owner_of(rels: str) -> str:
    """The part a relationships part belongs to (`ppt/_rels/presentation.xml.rels` -> `ppt/presentation.xml`)."""

    folder, name = posixpath.split(rels)
    return posixpath.join(posixpath.dirname(folder), name.removesuffix(".rels"))


def resolve_target(owner: str, target: str) -> str:
    """The package path a relationship target names: absolute from the package root, else relative to its owner's folder."""

    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner), target))


def relationships(rels_xml: bytes, owner: str) -> list[dict]:
    """Each internal relationship of `owner` with its id, type and resolved target. External ones (links) name no part."""

    out = []
    for rel in ET.fromstring(rels_xml).iter(f"{{{PKG_REL}}}Relationship"):
        if rel.get("TargetMode") == "External" or not rel.get("Target"):
            continue
        out.append({"id": rel.get("Id"), "type": rel.get("Type"), "part": resolve_target(owner, rel.get("Target"))})
    return out


def slide_list(read: Callable[[str], bytes]) -> list[dict]:
    """The deck's slides in `sldIdLst` order: part path, relationship id, slide id and whether hidden."""

    by_id = {rel["id"]: rel for rel in relationships(read(rels_path(PRESENTATION)), PRESENTATION)}
    slides = []
    for entry in ET.fromstring(read(PRESENTATION)).iter(f"{{{PML}}}sldId"):
        rid = entry.get(f"{{{REL}}}id")
        rel = by_id.get(rid)
        # Raised so a caller that deletes by this list stops instead of reading an unreadable list as empty
        if rel is None or rel["type"] != SLIDE_REL:
            raise ValueError(f"presentation.xml lists slide {rid!r}, which no slide relationship resolves")
        slides.append({"part": rel["part"], "rid": rid, "id": int(entry.get("id")), "hidden": entry.get("show") == "0"})
    return slides


def prefix_of(xml: str, namespace: str) -> str | None:
    """The prefix `xml` binds `namespace` to: "" for a default namespace, None when it is not bound."""

    for prefix, uri in re.findall(r'xmlns(?::([\w.-]+))?="([^"]+)"', xml):
        if uri == namespace:
            return prefix
    return None

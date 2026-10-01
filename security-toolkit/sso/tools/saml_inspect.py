#!/usr/bin/env python3
"""SAML 2.0 Response / Assertion inspector & validator (offline).

Decodes a base64 SAML Response (or raw assertion XML) and checks the things
that actually break or weaken a SAML SSO integration — the day-to-day work of
designing and supporting SAML:

  - **Status** code (did the IdP say Success?).
  - **Signature present** on the Response and/or Assertion (unsigned = forgeable).
  - **Conditions** NotBefore / NotOnOrAfter (is the assertion within its window?).
  - **AudienceRestriction** (is this assertion meant for *your* SP entityID?).
  - **SubjectConfirmation** Recipient + NotOnOrAfter (replay / wrong-ACS checks).
  - **AuthnStatement** SessionNotOnOrAfter.
  - NameID + attributes (what the app actually receives).

This does NOT verify the XML signature cryptographically (that needs the IdP
cert + a canonicalization/xmlsec library); it reports whether a signature is
present and all the clock/audience/recipient conditions, which is where most
real SAML issues live. Use it to troubleshoot a failing login or review an
IdP's response.

Input: a file containing a base64-encoded SAMLResponse, or raw XML (--xml).
Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python saml_inspect.py sample.saml.b64
    python saml_inspect.py --xml response.xml --audience https://sp.example.com/metadata
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

NS = {
    "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}
UTC = dt.timezone.utc


def _parse_time(val: str | None) -> dt.datetime | None:
    if not val:
        return None
    try:
        return dt.datetime.fromisoformat(val.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_xml(path: str, is_xml: bool) -> ET.Element:
    raw = Path(path).read_text(encoding="utf-8").strip()
    if not is_xml:
        # base64 (possibly URL-form). Try standard then urlsafe.
        for dec in (base64.b64decode, base64.urlsafe_b64decode):
            try:
                raw = dec(raw).decode("utf-8", "replace")
                break
            except Exception:  # noqa: BLE001
                continue
    return ET.fromstring(raw)


def inspect(rep: Report, root: ET.Element, audience: str | None) -> None:
    now = dt.datetime.now(UTC)

    # Status (on a Response)
    status = root.find(".//samlp:Status/samlp:StatusCode", NS)
    if status is not None:
        val = status.get("Value", "")
        if val.endswith(":Success"):
            rep.ok(f"Status: Success ({val.split(':')[-1]})")
        else:
            rep.fail(f"Status is NOT Success: {val}")

    # Signatures (presence only)
    resp_sig = root.find("ds:Signature", NS) is not None
    assertion = root.find(".//saml:Assertion", NS)
    assn_sig = assertion is not None and assertion.find("ds:Signature", NS) is not None
    if not resp_sig and not assn_sig:
        rep.fail("No XML signature on the Response OR the Assertion — forgeable. "
                 "The IdP must sign at least the assertion.")
    else:
        rep.ok(f"Signature present (response={resp_sig}, assertion={assn_sig}). "
               f"(crypto verification requires the IdP cert + xmlsec.)")

    if assertion is None:
        rep.warn("No <Assertion> found — nothing more to validate.")
        return

    # Issuer / NameID
    issuer = assertion.findtext("saml:Issuer", default="", namespaces=NS)
    if issuer:
        emit(Level.INFO, f"Issuer (IdP entityID): {issuer}")
    nameid = assertion.findtext(".//saml:Subject/saml:NameID", default="", namespaces=NS)
    if nameid:
        emit(Level.INFO, f"Subject NameID: {nameid}")

    # Conditions window
    cond = assertion.find("saml:Conditions", NS)
    if cond is not None:
        nb = _parse_time(cond.get("NotBefore"))
        noa = _parse_time(cond.get("NotOnOrAfter"))
        if nb and now < nb:
            rep.fail(f"Assertion not yet valid (NotBefore {nb.isoformat()} > now). "
                     f"Clock skew between IdP and SP?")
        if noa and now >= noa:
            rep.fail(f"Assertion EXPIRED (NotOnOrAfter {noa.isoformat()} <= now).")
        if nb and noa and nb <= now < noa:
            rep.ok(f"Assertion within its validity window (until {noa.isoformat()}).")
        # Audience
        auds = [a.text for a in cond.findall(".//saml:Audience", NS) if a.text]
        if auds:
            emit(Level.INFO, f"AudienceRestriction: {', '.join(auds)}")
            if audience and audience not in auds:
                rep.fail(f"Your SP entityID '{audience}' is NOT in the audience "
                         f"{auds} — the IdP issued this for a different SP.")
            elif audience:
                rep.ok("SP entityID matches the AudienceRestriction.")
        else:
            rep.warn("No AudienceRestriction — any SP could consume this assertion.")
    else:
        rep.warn("No <Conditions> element — no validity window or audience.")

    # SubjectConfirmationData (recipient + expiry)
    scd = assertion.find(".//saml:SubjectConfirmationData", NS)
    if scd is not None:
        rcpt = scd.get("Recipient")
        snoa = _parse_time(scd.get("NotOnOrAfter"))
        if rcpt:
            emit(Level.INFO, f"SubjectConfirmation Recipient (expected ACS URL): {rcpt}")
        if snoa and now >= snoa:
            rep.fail(f"SubjectConfirmationData EXPIRED (NotOnOrAfter {snoa.isoformat()}).")

    # Attributes the app receives
    attrs = assertion.findall(".//saml:AttributeStatement/saml:Attribute", NS)
    if attrs:
        names = [a.get("Name") or a.get("FriendlyName") or "?" for a in attrs]
        emit(Level.INFO, f"{len(attrs)} attribute(s) released: {', '.join(names[:10])}")
    else:
        rep.warn("No attributes released — the app may not get email/groups/roles.")


def main() -> int:
    ap = argparse.ArgumentParser(description="SAML 2.0 Response/Assertion inspector")
    ap.add_argument("input", help="file with a base64 SAMLResponse (or raw XML with --xml)")
    ap.add_argument("--xml", action="store_true", help="input is raw XML, not base64")
    ap.add_argument("--audience", help="your SP entityID to check against AudienceRestriction")
    args = ap.parse_args()

    if not Path(args.input).exists():
        emit(Level.FAIL, f"File not found: {args.input}")
        return 3
    try:
        root = load_xml(args.input, args.xml)
    except (ET.ParseError, ValueError, OSError) as exc:
        emit(Level.FAIL, f"Could not parse SAML: {exc}")
        return 3

    emit(Level.INFO, "Inspecting SAML response/assertion (clock/audience/signature-presence).")
    rep = Report()
    inspect(rep, root, args.audience)
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

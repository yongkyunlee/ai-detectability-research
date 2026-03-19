# [Security] The Python documentation recommends using `defusedxml` instead of `xml` because the native Python `xml` library is vulnerable to XML External Entity (XXE) attacks. These attacks can leak confidential data and "XML bombs" can cause denial of service.

**Issue #4865** | State: open | Created: 2026-03-14 | Updated: 2026-03-14
**Author:** tejasae-afk

**File:** `lib/crewai-tools/src/crewai_tools/rag/loaders/xml_loader.py` (line 2)

The Python documentation recommends using `defusedxml` instead of `xml` because the native Python `xml` library is vulnerable to XML External Entity (XXE) attacks. These attacks can leak confidential data and "XML bombs" can cause denial of service.

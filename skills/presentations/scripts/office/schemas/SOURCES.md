# OOXML schemas

The XML Schemas `validators/base.py` checks document parts against. Every file is a
verbatim copy of its published source. Nothing here is edited: where a schema imports
another by a remote URL or by namespace alone, the validator resolves it to the local
copy (`_REMOTE_SCHEMAS` and `_load_schema` in `validators/base.py`), so validation never
reaches the network.

| Directory | Source | Archive sha256 |
|---|---|---|
| `ISO-IEC29500-4_2016/` | ECMA-376 Part 4, 5th edition (December 2016), Transitional XML Schema, `OfficeOpenXML-XMLSchema-Transitional.zip` inside https://ecma-international.org/wp-content/uploads/ECMA-376-4_5th_edition_december_2016.zip. The same text as ISO/IEC 29500-4:2016. | outer `bd25da1109f73762356596918bf5ff8b74a1331642dba5f1c1d1dfc6bed34ecd`, inner `d34187520749998af306faf1b730e568b0ca6d88ad24638a407c0a9bb4ca04fc` |
| `ecma/fouth-edition/` | ECMA-376 Part 2, 4th edition (December 2012), Open Packaging Conventions XML Schema, `OpenPackagingConventions-XMLSchema.zip` inside https://ecma-international.org/wp-content/uploads/ECMA-376_4th_edition_december_2012.zip. The directory name is the one the validator's mappings use. | outer `cc7e6cead58205025a0e05e6d339137b99f3add55c435bf98c88987ae85c7f4f`, inner `e5a0a7c1f43ac8b8f66d850f48545c2ead09f6d632bb8539fab79962c7fd55df` |
| `external/xml.xsd` | W3C, https://www.w3.org/2001/xml.xsd | `61960fb3131e38022caad5360e2f33a3382578ab3c80cd58bd74320ede61b20c` |
| `external/dc.xsd`, `dcterms.xsd`, `dcmitype.xsd` | Dublin Core Metadata Initiative, https://www.dublincore.org/schemas/xmls/qdc/2003/04/02/ | `bc1d454db1bb20dfb1867a3fe0cf007775fc4afa33a5df425c12d854f049f1f6`, `6328c8b574c166f8ebc28d07231e6ee47121e9791689b70c3afa665f22099fed`, `4980845d0bedcf45e707fa64eb47492ae4f95ac4ae42f5c3c68b58c0bc9e8e49` |

Licenses. The ECMA-376 schemas are copied unmodified under Ecma's copyright notice and
license, which lets the standard be copied and distributed as long as the notice travels
with it: it is in `ECMA-NOTICE.txt`, taken from
https://ecma-international.org/policies/by-ipr/ecma-text-copyright-policy/. The Dublin
Core schemas are DCMI material under CC BY 4.0 (https://www.dublincore.org/about/copyright/).
`xml.xsd` is the W3C's own schema for the xml namespace, the one its specifications tell
other schemas to import.

Word's 2012 and later extension parts (`people.xml`, `commentsIds.xml`,
`commentsExtensible.xml`, `commentsExtended.xml`) have Microsoft schemas that are not
shipped, so the validator skips those parts.

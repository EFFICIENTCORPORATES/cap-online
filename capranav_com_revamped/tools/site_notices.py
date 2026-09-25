"""The wording of the site's copying and data-source notices, in one place.

Used by build_faq.py, build_discovery_files.py and apply_legal_notice.py so the pages, the FAQ, llms.txt and the
Excel exports always say the same thing. Change the text here, re-run the build scripts, deploy.

The data contact is 1LAVYA's admin address. Confirm it before publishing changes to it.
"""

DATA_CONTACT = "admin@1lavya.com"

COPY_NOTICE = (
    "© CA Pranav Pratik Tulshyan. Copying, scraping, mirroring, bulk downloading or republishing any content on this site "
    "(pages, questions, answers, analysis, datasets, books, slides) is not permitted without written permission. "
    "Search engines and AI search and answer systems may read this site and show short excerpts to their users with a link back to capranav.com."
)

DATA_NOTICE = (
    "The data and analysis are sourced from the 1LAVYA data repository. "
    f"To request API access to the data behind any topic, contact 1LAVYA at {DATA_CONTACT}."
)

# Longer wording for the Terms page.
TERMS_TEXT = (
    "All content on capranav.com, including the question and topic analysis, rankings, datasets, the question bank, answers, "
    "books, slides and videos, belongs to CA Pranav Pratik Tulshyan or is used with permission. Materials published by ICAI "
    "remain ICAI's property. You may read the content, use it for your own study, and quote short excerpts with a link to "
    "capranav.com. You may not copy, scrape, mirror, bulk download, republish, sell, or build a database or another website from "
    "it, by hand or with automated tools, without written permission. Search engines and AI search and answer systems may index "
    "the site and show short excerpts to their users with attribution."
)

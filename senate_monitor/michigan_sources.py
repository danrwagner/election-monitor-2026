"""Verified Michigan 2026 county election result landing pages.

These are official county-linked result pages, not yet validated structured APIs.
Do not treat page availability as evidence of reported votes.
"""
SOURCES = {
    "Wayne": {
        "url": "https://michigan.totalvote.com/Wayne",
        "status": "official result page; machine-readable feed not verified",
    },
    "Kent": {
        "url": "https://app.enhancedvoting.com/results/public/kent-county-mi/elections/11032026_20261005115447",
        "status": "official 2026 result page linked from Kent County; API not verified",
    },
    "Oakland": {
        "url": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
        "status": "official county directory; direct 2026 feed not verified",
    },
    "Macomb": {
        "url": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
        "status": "official county directory; direct 2026 feed not verified",
    },
    "Genesee": {
        "url": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
        "status": "official county directory; direct 2026 feed not verified",
    },
    "Washtenaw": {
        "url": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
        "status": "official county directory; direct 2026 feed not verified",
    },
}

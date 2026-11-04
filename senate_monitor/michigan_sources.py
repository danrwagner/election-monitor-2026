# Michigan 2026 county election source registry
# These are human-readable official county election pages, not validated machine-readable feeds.
# No vote totals are imported until each endpoint and race schema is verified.
SOURCES = {
    "Wayne": "https://michigan.totalvote.com/Wayne",
    "Oakland": "https://www.oakgov.com/government/clerk-register-of-deeds/elections-voting/election-results",
    "Macomb": "https://www.macombgov.org/departments/clerk-register-deeds/elections",
    "Kent": "https://www.kentcountymi.gov/335/Election-Results",
    "Genesee": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
    "Washtenaw": "https://www.michigan.gov/sos/elections/election-results-and-data/candidate-listings-and-election-results-by-county",
}
# Oakland path is a candidate page to validate before automation.

### Learning: Population 3σ anomaly detection requires n≥10 normal samples
- Context: Writing anomaly detection tests for token analyzer (Item 8)
- Discovery: With population stddev, a single outlier in a small dataset (n<10) can inflate the mean and stddev enough to keep itself below the threshold. The n≥10 requirement is a hard mathematical bound: threshold < M iff n > 9 (derived from n*(M-C) > 3*(M-C)*sqrt(n)).
- Rule: When testing 3σ anomaly detection with a crafted dataset, use at least 10 normal entries before the outlier to guarantee detection.

### Learning: Fixture timestamps and UTC date filtering
- Context: Implementing date filtering in cost log parser (Item 3)
- Discovery: Fixture cost.log entry 1 is `2026-03-19T08:00:00+09:00` which converts to UTC `2026-03-18T23:00:00Z` (date 2026-03-18). Tests that assume "all fixture entries are on 2026-03-19 UTC" will fail.
- Rule: When writing date filter tests, always calculate the UTC date of each fixture entry explicitly. Entries stored in +09:00 before 09:00 local time fall on the previous UTC date.
### Learning: Jinja2 autoescape escapes JSON embedded in templates
- Context: Embedding Python dict as JSON string in Jinja2 HTML template (Item 13)
- Discovery: With autoescape=True (required for HTML safety), `{{ data_json }}` HTML-escapes `"` to `&#34;`, breaking JSON.parse in the browser.
- Rule: When embedding server-generated JSON in a Jinja2 template, use `{{ data_json | safe }}`. Only use `| safe` for internally generated strings, never for user input.

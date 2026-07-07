# Database

This document describes the data storage responsibilities of Suraj Research
Engine. It describes responsibilities only — no schema, no SQL.

## Raw Research Database

Holds unverified research data as originally gathered by the Research
Execution Layer. Data here has not yet passed fact validation.

## Verified Research Database

Holds research data that has passed the Fact Validation Layer. This is the
only data considered trustworthy enough for analysis and generation.

## Future Cache

Reserved for a future caching layer to avoid redundant research execution for
previously researched topics.

## Future History

Reserved for a future historical record of research changes over time,
enabling comparison between past and present findings.

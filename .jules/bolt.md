## 2024-05-24 - [Django Template N+1 query optimization]
**Learning:** Accessing related objects properties in Django templates (e.g. `olympian.team.name` while iterating over `olympians` without prefetching) creates hidden N+1 queries that are difficult to spot unless specifically profiling the database queries.
**Action:** Always inspect loops in templates that render related object properties, and proactively use `.select_related()` (for foreign keys) or `.prefetch_related()` (for reverse foreign keys/M2M) in the `get_context_data` of the views to eagerly fetch the relationships.

## 2024-10-24 - Prefetching related objects for DetailView
**Learning:** When a DetailView template iterates over a related manager (e.g., `classroom.olympians.all()`) and accesses a nested foreign key (e.g., `olympian.team.name`), it causes an N+1 query problem. Using `prefetch_related` and `Prefetch` on the queryset inside `get_queryset` is necessary to optimize queries, even for a single DetailView object.
**Action:** Always check `DetailView` templates for loops that hit related objects with further foreign key lookups and optimize the `get_queryset` with `prefetch_related`.

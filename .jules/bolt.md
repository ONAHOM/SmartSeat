
## 2025-05-19 - [N+1 Queries in Detail Views with Related Managers]
**Learning:** In Django views where a template iterates over a related manager accessed through the context object (e.g., `classroom.olympians.all` in `OlympicClassroomDetailView`), accessing foreign keys on the related objects (like `olympian.team`) causes severe N+1 queries. We must optimize this at the view level.
**Action:** Always optimize `get_queryset` with `prefetch_related` using a `Prefetch` object configured with `select_related` for nested relationships when the template iterates over related objects. Avoid applying heavy prefetches blindly to UpdateView/DeleteView to prevent over-fetching.

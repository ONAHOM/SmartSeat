## 2026-10-20 - [N+1 Queries in Django Views]
**Learning:** [When templates iterate over related managers (e.g., `classroom.olympians.all`) and access nested foreign keys (e.g., `olympian.team`), it causes N+1 queries. Adding prefetch logic to UpdateView or DeleteView can cause over-fetching.]
**Action:** [Optimize the view's `get_queryset` using `prefetch_related` with a `Prefetch` object and `select_related` in views where the related data is iterated (like DetailView or ListView).]

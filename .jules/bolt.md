## 2024-10-17 - Optimize Django View Querysets with PrefetchRelated
**Learning:** In Django templates iterating over related items and accessing foreign keys (e.g. `classroom.olympians.all` and then `olympian.team.name`), it creates an N+1 query problem. Overriding `get_queryset` with `prefetch_related(Prefetch('olympians', queryset=Olympian.objects.select_related('team')))` effectively solves this.
**Action:** Use `prefetch_related` combined with `Prefetch` and `select_related` on querysets when iterating through related fields in templates.

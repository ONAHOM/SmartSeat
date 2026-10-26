## 2024-05-19 - [N+1 queries on nested iteration]
**Learning:** Found an N+1 query issue in templates when iterating over `classroom.olympians.all` and then accessing `olympian.team.name`. This happened because we weren't prefetching the `team` foreign key.
**Action:** Use `.select_related('team')` or `prefetch_related` on querysets passed to templates that will iterate over objects and access their related foreign key properties.

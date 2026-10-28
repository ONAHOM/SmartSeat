## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

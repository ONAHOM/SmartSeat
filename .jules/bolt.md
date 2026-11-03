## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-11-02 - N+1 Query in Django ListView via Template Iteration
**Learning:** Iterating over variables injected via global `context_processors` (e.g., `sidebar_classes`) in a main template instead of the view's specific context (e.g., `classrooms`) circumvents any queryset optimizations (like `.annotate()`) applied in the view, leading to N+1 queries.
**Action:** When solving N+1 issues in templates, ensure the template is iterating over the correct context variable provided by the view, not a generic one from a context processor, and apply `.annotate(Count('...'))` instead of using `.count()` inside the loop.

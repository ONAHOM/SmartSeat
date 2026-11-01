## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-11-01 - N+1 Query in Django Template Loops with .count() and .exists()
**Learning:** Found N+1 query bottlenecks when templates evaluate `.count()` and `.exists()` on related managers in loops (e.g., `event.classrooms.exists`). Also discovered that iterating over a global context variable (like `sidebar_classes`) in a main view template bypasses any queryset optimizations done in the `ListView`.
**Action:** When working on Django templates, use `.annotate(Count('...'))` in the `get_queryset` method and use the annotated property in the template (e.g., `event.classrooms_count`). Ensure main page templates iterate over the view-specific context (`classrooms`) instead of global context variables if query optimizations are needed.

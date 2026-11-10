## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2026-11-10 - Optimize ListView by eliminating N+1 queries with Count annotations
**Learning:** In Django templates, calling `.count()` and `.exists()` on related objects inside a loop leads to N+1 queries. We can optimize this by using `.annotate(Count(...))` in the `get_queryset` method and utilizing the annotated count in the template.
**Action:** When working on Django ListViews that render count or existence of related items in the template, look for  or  calls within loop and optimize them by moving the logic to the view using .

## 2024-11-10 - Optimize ListView by eliminating N+1 queries with Count annotations
**Learning:** In Django templates, calling `.count()` and `.exists()` on related objects inside a loop leads to N+1 queries. We can optimize this by using `.annotate(Count(...))` in the `get_queryset` method and utilizing the annotated count in the template. Also, `context_object_name` allows customizing context variables in templates when using generic class-based views.
**Action:** When working on Django ListViews that render count or existence of related items in the template, look for `.count()` or `.exists()` calls within loop and optimize them by moving the logic to the view using `.annotate(Count(...))`.

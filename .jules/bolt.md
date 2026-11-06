## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-11-06 - [Avoid N+1 queries using Annotate in ListViews]
**Learning:** Found an N+1 query issue in `ClassroomListView` and `OlympicEventListView` where templates called `.count()` and `.exists()` on related sets inside loops. Also discovered that replacing `.exists()` with checking a positive annotated count (e.g. `{% if event.classrooms_count %}`) evaluates correctly in Django templates.
**Action:** Use `.annotate(Count('...'))` in the view `get_queryset` and use the annotated field in templates instead of `.count()` or `.exists()` to prevent N+1 queries during iteration.

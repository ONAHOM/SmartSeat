## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-11-04 - N+1 Query in Django ListView via related manager count
**Learning:** Found N+1 query patterns in `ClassroomListView` and `OlympicEventListView` where `.count()` was called on related managers inside a loop over the view's querysets during template rendering (`templates/classroom/classroom_list.html` and `templates/olympiads/event_list.html`). Using `.annotate(Count('field'))` on the base queryset effectively resolves this.
**Action:** When working on similar Django apps, look for related manager calls like `item.related_objects.count` used inside template loops, and optimize them using `.annotate()` on the view's base queryset.

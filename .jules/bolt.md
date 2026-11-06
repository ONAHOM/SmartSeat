## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-10-27 - N+1 Query in Django ListView via count() and exists()
**Learning:** Calling `.count()` and `.exists()` inside a Django template loop triggers separate SQL queries for each iteration, causing an N+1 query problem. This can be efficiently resolved by using `.annotate(Count('related_model'))` in the view's `get_queryset` method and using the annotated property in the template. An integer greater than 0 evaluates to True in Django templates, cleanly replacing `.exists()` logic.
**Action:** When finding `.count()` or `.exists()` in template loops, use `.annotate()` with `Count` in the view instead of `prefetch_related` as it uses less memory and reduces queries to just one group-by query.

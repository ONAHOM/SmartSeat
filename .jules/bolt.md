## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-10-27 - N+1 Query in Django ListView via Template Counts
**Learning:** Calling `.count()` on related managers in Django templates (e.g., `cls.students.count`) within a loop triggers an N+1 query problem. This can be resolved efficiently by using `.annotate(students_count=Count('students'))` directly on the view's queryset and rendering the annotated variable (`cls.students_count`).
**Action:** When a template iterates through a queryset and displays the count of a related entity, always move the count operation to the view's `get_queryset` method using Django's `annotate(Count('...'))`.

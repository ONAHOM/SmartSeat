## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-10-27 - N+1 Query in Django ListView via count and exists
**Learning:** In Django templates, calling `related_set.count()` and `related_set.exists()` inside a loop (like in `event.classrooms.count`) creates an N+1 query problem by generating two extra queries per item.
**Action:** When working on Django apps, optimize list views by annotating the count in the queryset using `.annotate(my_count=Count('related_set'))`. Then, replace `.count()` with the annotated property `my_count`, and `.exists()` with `{% if my_count %}` in the template.

## 2024-10-27 - N+1 Query in Django DetailView
**Learning:** Found a specific N+1 query issue in `OlympicClassroomDetailView` where `olympians` and their associated `team` are accessed in `templates/olympiads/classroom_detail.html` rendering. Using `prefetch_related` along with a custom `Prefetch` containing `select_related` on the original queryset solves this effectively.
**Action:** When working on similar Django apps, look for nested relationships used inside template loops, and fetch them using custom `Prefetch` querysets.

## 2024-10-27 - N+1 Query in Django ListView via Template
**Learning:** Found an N+1 query issue in `OlympicEventListView` where `.count()` and `.exists()` were being called on a related manager (`event.classrooms.count`) inside a template loop in `templates/olympiads/event_list.html`.
**Action:** When a template loops over items and calls `.count()` or `.exists()` on a related manager for each item, optimize the view's queryset by using `.annotate(my_count=Count('related_model'))`. Then in the template, replace the `.count()` and `.exists()` method calls with the annotated property `my_count` (which works as a boolean check because it evaluates to >0).

## 2024-05-18 - N+1 in DetailView
**Learning:** Using `self.object.related_name.all()` in `get_context_data` of a `DetailView` results in an N+1 query issue. While the object is fetched in `get_object`, fetching related entities using `.all()` inside the template iterates query execution without prefetched related objects if it's not setup correctly via `get_queryset` with `prefetch_related`.
**Action:** When a `DetailView` needs related objects, override `get_queryset()` and use `.prefetch_related('related_field')` on it, then the template can access `object.related_field.all` efficiently.

## 2024-05-18 - View Optimization Bypassed by Context Processor Variable
**Learning:** If a template iterates over a variable injected by a context processor (like `sidebar_classes`) instead of the primary context object provided by the view (like `classrooms`), any queryset optimizations (such as `prefetch_related`) made in the view's `get_queryset` method will be bypassed, resulting in N+1 query issues.
**Action:** When fixing N+1 queries in templates by adding `prefetch_related` or `select_related` to the view's queryset, always ensure the template actually iterates over the view's context object and not a structurally similar context processor variable.

## 2024-05-18 - .count() Bypasses .prefetch_related() Cache
**Learning:** In Django templates, calling `{{ queryset.count }}` (or `.count()` in code) on a related manager always executes a `SELECT COUNT(*)` query, bypassing any prefetch cache populated by `.prefetch_related()`. This can cause N+1 queries even when data is prefetched.
**Action:** When you only need the count and want to avoid N+1 queries, use `.annotate(count_field=Count('related_field'))` in the view to perform the counting at the database level efficiently. If the related objects are already loaded in memory (via `prefetch_related`) and you need the objects anyway, use the `|length` template filter (`{{ queryset.all|length }}`) to count the objects in Python without hitting the database.

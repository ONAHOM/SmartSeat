from django.shortcuts import get_object_or_404, redirect
from classroom.models import Classroom
from .utils import SeatingGA, generate_seating_chart


from django.contrib import messages


def calculate_seating(request, classroom_id):
    classroom = get_object_or_404(Classroom, pk=classroom_id, teacher=request.user)
    students = classroom.students.all()

    if students:
        total_seats = classroom.rows_count * classroom.desks_per_row * 2

        # КРИТИЧЕСКАЯ ПРОВЕРКА: Если учеников больше, чем мест
        if students.count() > total_seats:
            messages.error(
                request,
                f"Невозможно распределить места: в классе всего {total_seats} мест, "
                f"а учеников добавлено {students.count()}. Увеличьте количество парт или рядов."
            )
            return redirect('classroom:detail', pk=classroom.pk)

        # Запуск алгоритма, если места хватает
        ga = SeatingGA(
            students_queryset=students,
            rows=classroom.rows_count,
            desks_per_row=classroom.desks_per_row
        )
        best_plan = ga.solve()

        # Генерируем картинку схемы рассадки
        chart_path = generate_seating_chart(best_plan, classroom)
        classroom.seating_chart = chart_path

        # Вычисляем полные метрики качества для лучшего плана и сохраняем в JSON-поле
        classroom.seating_metrics = ga.get_quality_metrics(best_plan)
        
        # Сохраняем изменения в БД
        classroom.save()
        messages.success(request, "Оптимальная рассадка класса успешно сгенерирована!")

    return redirect('classroom:detail', pk=classroom.pk)
import csv
import io
from django.contrib import messages
from .models import Student


def import_students_from_csv(request, classroom, csv_file):
    """
    Вспомогательный сервис для парсинга CSV-файла и пакетного сохранения учеников.
    Возвращает True в случае успеха, и False, если внутри файла были критические ошибки.
    """
    try:
        # Гарантированно сбрасываем указатель в начало файла перед чтением
        csv_file.seek(0)

        # Декодируем байты файла в текст, UTF-8-sig срезает BOM-байты Excel
        data_set = csv_file.read().decode('UTF-8-sig')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string, delimiter=';')

        # Пропускаем строку заголовков
        next(reader, None)

        students_to_create = []
        for line_num, row in enumerate(reader, start=2):
            if not row or len(row) < 7:
                continue  # Пропускаем пустые или недописанные строки

            try:
                # Очищаем строки от возможного Excel-форматирования вида ="4.50" или ="0.0"
                clean_eyesight = row[1].replace('="', '').replace('"', '').strip()
                clean_hearing = row[2].replace('="', '').replace('"', '').strip()
                clean_health_group = row[3].replace('="', '').replace('"', '').strip()
                clean_height = row[4].replace('="', '').replace('"', '').strip()
                clean_gpa = row[5].replace('="', '').replace('"', '').strip()
                clean_sociability = row[6].replace('="', '').replace('"', '').strip()

                # Валидируем типы на чистых данных
                students_to_create.append(Student(
                    classroom=classroom,
                    full_name=row[0].strip(),
                    eyesight=float(clean_eyesight),
                    hearing=int(clean_hearing),
                    health_group=int(clean_health_group),
                    height=int(clean_height),
                    gpa=float(clean_gpa),
                    sociability=int(clean_sociability)
                ))
            except (ValueError, IndexError):
                messages.error(request, f"Ошибка данных в строке {line_num}. Проверьте правильность заполнения чисел.")
                return False

        if students_to_create:
            # Отправляем пачку данных за 1 транзакцию
            Student.objects.bulk_create(students_to_create)
            messages.success(request, f"Успешно импортировано {len(students_to_create)} учеников из файла.")
            return True
        else:
            messages.warning(request, "Файл не содержит корректных строк для импорта.")
            return False

    except Exception as e:
        messages.error(request, f"Критическая ошибка при чтении CSV-файла: {str(e)}")
        return False
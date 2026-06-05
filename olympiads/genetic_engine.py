import random
import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from django.db import transaction

from .models import OlympicClassroom, Team


class OlympicSeatingGA:
    # =========================================================================
    # ПОЛНАЯ СИСТЕМА ОЛИМПИАДНЫХ И ПЕДАГОГИЧЕСКИХ ВЕСОВ
    # =========================================================================
    # 1. Олимпиадные доминанты (Высший приоритет)
    W_MIXED_TEAMS_PENALTY = 5000       # Две разные команды за одной партой
    W_SAME_SCHOOL_NEIGHBOR = 2000      # Одна школа за одной партой (индивидуалы)
    W_SAME_SCHOOL_BEHIND = 1000        # Одна школа друг за другом (индивидуалы)
    W_ANY_NEIGHBOR_DENSITY = 500       # Штраф за плотность для шахматного порядка

    # 2. Медицинские факторы (Второй приоритет)
    W_EYESIGHT_PENALTY = 150           # Плохое зрение (диоптрии < -3.0) дальше 3-й парты
    W_HEARING_PENALTY = 150            # Плохой слух (уровень >= 2) дальше 2-й парты
    W_HEALTH_DRAFT_PENALTY = 100       # Группа здоровья 2 (риск простуд) у окна (ряд 0)

    # 3. Физиология и педагогика (Третий приоритет)
    W_HEIGHT_OVERLAP = 8               # Высокий перед низким
    W_SOC_DOUBLE_TALK = 150            # Два гиперактивных (sociability=3) рядом
    W_GPA_DOUBLE_WEAK = 120            # Два слабоуспевающих (gpa < 3.5) рядом

    def __init__(self, classroom_id):
        self.classroom = OlympicClassroom.objects.get(id=classroom_id)
        self.event = self.classroom.event
        
        self.rows = self.classroom.rows_count
        self.desks = self.classroom.desks_per_row
        self.total_desks = self.rows * self.desks  
        self.total_seats = self.total_desks * 2
        
        self.pop_size = 120
        self.generations = 300

        if self.event.is_team_event:
            students_queryset = self.classroom.olympians.select_related('team')
            self.team_map = {}
            for s in students_queryset:
                if s.team_id:
                    if s.team_id not in self.team_map:
                        self.team_map[s.team_id] = []
                    self.team_map[s.team_id].append(s)
            
            self.pool_elements = list(Team.objects.filter(id__in=self.team_map.keys()))
        else:
            self.pool_elements = list(self.classroom.olympians.all())

    def fitness(self, chromosome):
        score = 0
        flat_seats = self._flatten_chromosome(chromosome)
        num_seats = len(flat_seats)

        # --- 1. АНАЛИЗ СОСЕДА ЗА ПАРТОЙ И ПЕДАГОГИЧЕСКИЙ БАЛАНС ---
        for i in range(0, num_seats, 2):
            s1 = flat_seats[i]
            s2 = flat_seats[i+1]
            
            if s1 and s2:
                if self.event.is_team_event:
                    # В командном режиме проверяем жесткий запрет смешивания команд за одной партой
                    if s1.team_id != s2.team_id:
                        score -= self.W_MIXED_TEAMS_PENALTY
                else:
                    # В индивидуальном режиме работает шахматный порядок и изоляция школ
                    score -= self.W_ANY_NEIGHBOR_DENSITY
                    if s1.school == s2.school:
                        score -= self.W_SAME_SCHOOL_NEIGHBOR

                # Общие медико-педагогические штрафы для смежных мест (для обоих режимов)
                if s1.sociability == 3 and s2.sociability == 3:
                    score -= self.W_SOC_DOUBLE_TALK
                    
                if s1.gpa and s2.gpa and s1.gpa < 3.50 and s2.gpa < 3.50:
                    score -= self.W_GPA_DOUBLE_WEAK

        # --- 2. АНАЛИЗ КОЛОНН (ИДУЩИЕ ДРУГ ЗА ДРУГОМ) И ЖИЗНЕННЫЕ ПОКАЗАТЕЛИ ---
        for i, student in enumerate(flat_seats):
            if student is None:
                continue
                
            row_idx = i // (self.desks * 2)       
            desk_idx = (i % (self.desks * 2)) // 2 
            is_window_side = (row_idx == 0)

            # Анализ участника сзади
            behind_idx = i + 2
            if behind_idx < num_seats:
                student_behind = flat_seats[behind_idx]
                if student_behind is not None:
                    # Накладываем штраф за одинаковую школу по вертикали (для индивидуалов)
                    if not self.event.is_team_event:
                        if student.school == student_behind.school:
                            score -= self.W_SAME_SCHOOL_BEHIND
                    
                    # Контроль перекрытия обзора по росту
                    if student.height > student_behind.height:
                        score -= (student.height - student_behind.height) * self.W_HEIGHT_OVERLAP

            # Проверка зрения
            if student.eyesight and student.eyesight < -3.0 and desk_idx > 2:
                score -= int(abs(student.eyesight) * self.W_EYESIGHT_PENALTY)
                
            # Проверка слуха
            if student.hearing and student.hearing >= 2 and desk_idx > 1:
                score -= int(student.hearing * self.W_HEARING_PENALTY)
                
            # Риск простудных заболеваний у окна (Ряд 0)
            if student.health_group == 2 and is_window_side:
                score -= self.W_HEALTH_DRAFT_PENALTY

        return score

    def _flatten_chromosome(self, chromosome):
        flat = []
        if self.event.is_team_event:
            for team in chromosome:
                if team is None:
                    flat.extend([None, None])
                else:
                    members = self.team_map[team.id]
                    m1 = members[0] if len(members) > 0 else None
                    m2 = members[1] if len(members) > 1 else None
                    flat.extend([m1, m2])
        else:
            flat = chromosome
        return flat

    def get_metrics(self, best_chromosome):
        flat_seats = self._flatten_chromosome(best_chromosome)
        count = max(len(self.classroom.olympians.all()), 1)
        f_med, f_phys, f_gpa, f_soc = 0, 0, 0, 0

        # Попарный анализ парт для вычисления олимпиадной честности
        for i in range(0, len(flat_seats), 2):
            s1 = flat_seats[i]
            s2 = flat_seats[i+1]
            
            if s1 and s2:
                if self.event.is_team_event:
                    # Штрафуем, только если за одной партой РЕАЛЬНО оказались разные команды
                    if s1.team_id != s2.team_id:
                        f_soc += self.W_MIXED_TEAMS_PENALTY
                else:
                    if s1.school == s2.school:
                        f_gpa += self.W_SAME_SCHOOL_NEIGHBOR
          
                if s1.sociability == 3 and s2.sociability == 3:
                    f_soc += self.W_SOC_DOUBLE_TALK

        # Поштучный анализ индивидуальных параметров
        for i, student in enumerate(flat_seats):
            if student is None:
                continue
            desk_idx = (i % (self.desks * 2)) // 2
            row_idx = i // (self.desks * 2)

            if student.eyesight and student.eyesight < -3.0 and desk_idx > 2:
                f_med += int(abs(student.eyesight) * 10)
            if student.hearing and student.hearing >= 2 and desk_idx > 1:
                f_med += int(student.hearing * 10)
            if student.health_group == 2 and row_idx == 0:
                f_med += 50

            if i + 2 < len(flat_seats):
                behind = flat_seats[i + 2]
                if behind and student.height > behind.height:
                    f_phys += (student.height - behind.height) * self.W_HEIGHT_OVERLAP

        # Нормализация метрик (0 - 100%)
        k_med = max(0, min(100, int((1 - f_med / (count * 50 + 1)) * 100)))
        k_phys = max(0, min(100, int((1 - f_phys / (count * 100 + 1)) * 100)))
        k_gpa = max(0, min(100, int((1 - f_gpa / (count * self.W_SAME_SCHOOL_NEIGHBOR + 1)) * 100)))

        # Расчет коэффициента социализации/командности без учета пустых парт
        k_soc = max(0, min(100, int((1 - f_soc / (count * self.W_MIXED_TEAMS_PENALTY + 1)) * 100)))

        if self.event.is_team_event:
            total_efficiency = int((k_med * 0.1) + (k_phys * 0.1) + (k_soc * 0.8))
        else:
            total_efficiency = int((k_med * 0.1) + (k_phys * 0.1) + (k_gpa * 0.8))

        return {
            'total_efficiency': max(0, min(100, total_efficiency)),
            'k_medical': k_med,
            'k_physical': k_phys,
            'k_gpa': k_gpa,
            'k_social': k_soc
        }

    def create_individual(self):
        ind = self.pool_elements[:]
        target_size = self.total_desks if self.event.is_team_event else self.total_seats
        while len(ind) < target_size:
            ind.append(None)
        random.shuffle(ind)
        return ind

    def crossover(self, parent1, parent2):
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[start:end] = parent1[start:end]

        placed_ids = {el.id for el in child[start:end] if el is not None}
        p2_pool = [el for el in parent2 if el is not None and el.id not in placed_ids]
        
        p2_idx = 0
        for i in range(size):
            if i < start or i >= end:
                if parent2[i] is None:
                    child[i] = None
                else:
                    if p2_idx < len(p2_pool):
                        child[i] = p2_pool[p2_idx]
                        p2_idx += 1
                    else:
                        child[i] = None
        return child

    def mutate(self, chromosome):
        idx1, idx2 = random.sample(range(len(chromosome)), 2)
        chromosome[idx1], chromosome[idx2] = chromosome[idx2], chromosome[idx1]

    def solve(self):
        if not self.pool_elements:
            return []
        population = [self.create_individual() for _ in range(self.pop_size)]

        for _ in range(self.generations):
            population = sorted(population, key=self.fitness, reverse=True)
            new_gen = population[:15]
            while len(new_gen) < self.pop_size:
                p1, p2 = random.sample(population[:40], 2)
                child = self.crossover(p1, p2)
                if random.random() < 0.25:
                    self.mutate(child)
                new_gen.append(child)
            population = new_gen
            
        population = sorted(population, key=self.fitness, reverse=True)
        return self._flatten_chromosome(population[0])


# =========================================================================
# ГЕНЕРАЦИЯ ГРАФИЧЕСКОЙ СХЕМЫ
# =========================================================================

def generate_olympic_seating_chart(best_plan, classroom_obj):
    cell_width, cell_height, padding, margin_top = 280, 140, 50, 120
    rows = classroom_obj.rows_count
    desks_per_row = classroom_obj.desks_per_row
        
    img_width = (cell_width * 2 + padding) * rows + padding * (rows + 1)
    img_height = (cell_height + padding) * desks_per_row + margin_top + padding

    img = Image.new('RGB', (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Ariral.TTF')
    font = ImageFont.truetype(font_path, 14)
    meta_font = ImageFont.truetype(font_path, 11)
    title_font = ImageFont.truetype(font_path, 26)

    all_olympians = classroom_obj.olympians.all()
    team_sizes = {}
    for student in all_olympians:
        if student.team_id:
            team_sizes[student.team_id] = team_sizes.get(student.team_id, 0) + 1

    event_mode = "Командный зачет" if classroom_obj.event.is_team_event else "Индивидуальный зачет"

    draw.text((img_width//2 - 200, 25), f"КАРТА РАССАДКИ: АУДИТОРИЯ №{classroom_obj.number}", fill=(44, 62, 80), font=title_font)
    draw.text((img_width//2 - 190, 65), f"Режим: {event_mode} | Смешивание разных команд за одной партой ЗАПРЕЩЕНО", fill=(127, 141, 142), font=font)

    for r in range(rows):
        x_offset = padding + r * (cell_width * 2 + padding + 20)
        draw.text((x_offset + cell_width - 25, 100), f"РЯД {r+1}", fill=(221, 107, 32), font=font)

        row_start = r * (desks_per_row * 2)
        for d in range(desks_per_row):
            y_offset = margin_top + d * (cell_height + padding)

            draw.rectangle([x_offset, y_offset, x_offset + cell_width * 2, y_offset + cell_height], outline=(221, 107, 32), width=2)
            draw.line([x_offset + cell_width, y_offset, x_offset + cell_width, y_offset + cell_height], fill=(226, 232, 240), width=2)

            s1 = best_plan[row_start + d*2] if (row_start + d*2) < len(best_plan) else None
            s2 = best_plan[row_start + d*2 + 1] if (row_start + d*2 + 1) < len(best_plan) else None

            if s1:
                draw.text((x_offset + 12, y_offset + 20), s1.full_name[:24], fill=(44, 62, 80), font=font)
                team_info = f"Кмд: {s1.team.name} ({team_sizes.get(s1.team_id, 0)} чел.)" if s1.team else "Индивидуально"
                info_text = f"Школа: {s1.school[:18]}\nКласс: {s1.origin_class}\n{team_info}"
                draw.text((x_offset + 12, y_offset + 50), info_text, fill=(113, 128, 150), font=meta_font)
                draw.text((x_offset + cell_width - 30, y_offset + 10), "В-1", fill=(160, 174, 192), font=meta_font)
            else:
                draw.text((x_offset + 12, y_offset + 45), "[ Свободно ]", fill=(160, 174, 192), font=font)

            if s2:
                draw.text((x_offset + cell_width + 12, y_offset + 20), s2.full_name[:24], fill=(44, 62, 80), font=font)
                team_info = f"Кмд: {s2.team.name} ({team_sizes.get(s2.team_id, 0)} чел.)" if s2.team else "Индивидуально"
                info_text = f"Школа: {s2.school[:18]}\nКласс: {s2.origin_class}\n{team_info}"
                draw.text((x_offset + cell_width + 12, y_offset + 50), info_text, fill=(113, 128, 150), font=meta_font)
                draw.text((x_offset + cell_width * 2 - 30, y_offset + 10), "В-2", fill=(160, 174, 192), font=meta_font)
            else:
                draw.text((x_offset + cell_width + 12, y_offset + 45), "[ Свободно ]", fill=(160, 174, 192), font=font)

            draw.text((x_offset - 35, y_offset + cell_height//2 - 10), f"П-{d+1}", fill=(74, 85, 104), font=font)

    filename = f"olympic_chart_{classroom_obj.pk}.png"
    relative_path = os.path.join('seating_charts', filename)
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    img.save(full_path)
    return relative_path


def run_genetic_algorithm_for_classroom(classroom_id):
    try:
        ga = OlympicSeatingGA(classroom_id)
        best_plan = ga.solve()
        
        if not best_plan:
            return False
            
        chart_path = generate_olympic_seating_chart(best_plan, ga.classroom)
        metrics_dict = ga.get_metrics(best_plan)
        
        with transaction.atomic():
            classroom = ga.classroom
            classroom.seating_chart = chart_path
            classroom.seating_metrics = metrics_dict
            classroom.save()
            
        return True
    except Exception:
        return False

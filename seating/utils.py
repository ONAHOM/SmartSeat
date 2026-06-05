import random
import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont


class SeatingGA:
    # =========================================================================
    # КОНСТАНТЫ СИСТЕМЫ ВЕСОВ И ШТРАФОВ
    # =========================================================================
    W_EYESIGHT_CRITICAL_BASE = 1000
    W_EYESIGHT_CRITICAL_MULT = 200
    W_EYESIGHT_MEDIUM_BASE = 500
    W_EYESIGHT_MEDIUM_MULT = 100
    W_EYESIGHT_LIGHT_BASE = 200
    W_EYESIGHT_LIGHT_MULT = 50

    W_HEARING_CRITICAL = 500
    W_HEARING_MEDIUM = 600
    W_HEARING_LIGHT = 300

    W_HEALTH_DRAFT = 100
    W_HEALTH_RISK = 50

    W_HEIGHT_OVERLAP = 15

    W_GPA_DOUBLE_WEAK = 120
    W_SOC_DOUBLE_TALK = 150
    W_PREF_BONUS = 200
    W_DISLIKED_PENALTY = 400

    W_EMPTY_SEAT_FRONT = 15

    def __init__(self, students_queryset, rows, desks_per_row):
        self.students = list(
            students_queryset.prefetch_related(
                'preferred_classmates',
                'disliked_classmates'
                )
            )
        self.rows = rows
        self.desks = desks_per_row
        self.total_seats = rows * desks_per_row * 2
        
        self.pop_size = 100  
        self.generations = 250 
        
        self.preferred_map = {}
        self.disliked_map = {}
        
        for s in self.students:
            self.preferred_map[s.id] = {p.id for p in s.preferred_classmates.all()}
            self.disliked_map[s.id] = {d.id for d in s.disliked_classmates.all()}

    def fitness(self, chromosome):
        score = 0
        for i, student in enumerate(chromosome):
            row_idx = i // (self.desks * 2)       
            desk_idx = (i % (self.desks * 2)) // 2 
            is_window_side = (row_idx == 0)
            is_door_side = (row_idx == self.rows - 1)

            if student is None:
                score -= (self.desks - desk_idx) * self.W_EMPTY_SEAT_FRONT
                continue

            # --- 1. ЗРЕНИЕ ---
            if student.eyesight < 0:
                dioptries = abs(student.eyesight)
                if dioptries >= 3.0 and desk_idx > 0:  
                    score -= int(self.W_EYESIGHT_CRITICAL_BASE + dioptries * self.W_EYESIGHT_CRITICAL_MULT)
                elif dioptries >= 1.5 and desk_idx > 2: 
                    score -= int(self.W_EYESIGHT_MEDIUM_BASE + dioptries * self.W_EYESIGHT_MEDIUM_MULT)
                elif desk_idx > 3:                                             
                    score -= int(self.W_EYESIGHT_LIGHT_BASE + dioptries * self.W_EYESIGHT_LIGHT_MULT)

            # --- 2. СЛУХ ---
            if student.hearing > 0:
                if student.hearing >= 3 and desk_idx > 0:
                    score -= (student.hearing * self.W_HEARING_CRITICAL)
                elif student.hearing == 2 and desk_idx > 1:
                    score -= self.W_HEARING_MEDIUM
                elif student.hearing == 1 and desk_idx > 2:
                    score -= self.W_HEARING_LIGHT

            # --- 3. ГРУППЫ ЗДОРОВЬЯ ---
            if student.health_group == 2 and (is_window_side or is_door_side):
                score -= self.W_HEALTH_DRAFT
            if student.health_group >= 4 and desk_idx > 2:
                score -= (student.health_group * self.W_HEALTH_RISK)

            # --- 4. РОСТ ---
            if desk_idx < self.desks - 1:
                behind_idx = i + 2
                if behind_idx < self.total_seats:
                    student_behind = chromosome[behind_idx]
                    if student_behind is not None:
                        if student.height > student_behind.height:
                            score -= int((student.height - student_behind.height) * self.W_HEIGHT_OVERLAP)

            # --- 5. УСПЕВАЕМОСТЬ, СОСЕДСТВО И СОЦИОМЕТРИЯ ---
            neighbor_idx = i + 1 if i % 2 == 0 else i - 1
            if neighbor_idx < self.total_seats:
                neighbor = chromosome[neighbor_idx]
                if neighbor is not None:
                    if student.gpa < 3.20 and neighbor.gpa < 3.20:
                        score -= self.W_GPA_DOUBLE_WEAK
                    
                    if student.sociability == 3 and neighbor.sociability == 3:
                        score -= self.W_SOC_DOUBLE_TALK

                    if neighbor.id in self.preferred_map[student.id]:
                        score += self.W_PREF_BONUS
                    
                    if neighbor.id in self.disliked_map[student.id]:
                        score -= self.W_DISLIKED_PENALTY
        return score

    def get_quality_metrics(self, best_chromosome):
        """
        Вычисляет интегральный показатель и частные коэффициенты эффективности
        для лучшей хромосомы (в процентах от 0 до 100).
        """
        f_eyesight = 0
        f_hearing = 0
        f_health = 0
        f_height = 0
        f_gpa = 0
        f_sociability = 0
        f_disliked_penalty = 0
        f_preferred_bonus = 0

        for i, student in enumerate(best_chromosome):
            if student is None:
                continue

            row_idx = i // (self.desks * 2)
            desk_idx = (i % (self.desks * 2)) // 2
            is_window_side = (row_idx == 0)
            is_door_side = (row_idx == self.rows - 1)

            # --- 1. ЗРЕНИЕ ---
            if student.eyesight < 0:
                dioptries = abs(student.eyesight)
                if dioptries >= 3.0 and desk_idx > 0:
                    f_eyesight += int(self.W_EYESIGHT_CRITICAL_BASE + dioptries * self.W_EYESIGHT_CRITICAL_MULT)
                elif dioptries >= 1.5 and desk_idx > 2: 
                    f_eyesight += int(self.W_EYESIGHT_MEDIUM_BASE + dioptries * self.W_EYESIGHT_MEDIUM_MULT)
                elif desk_idx > 3:                                                   
                    f_eyesight += int(self.W_EYESIGHT_LIGHT_BASE + dioptries * self.W_EYESIGHT_LIGHT_MULT)

            # --- 2. СЛУХ ---
            if student.hearing > 0:
                if student.hearing >= 3 and desk_idx > 0:
                    f_hearing += (student.hearing * self.W_HEARING_CRITICAL)
                elif student.hearing == 2 and desk_idx > 1:
                    f_hearing += self.W_HEARING_MEDIUM
                elif student.hearing == 1 and desk_idx > 2:
                    f_hearing += self.W_HEARING_LIGHT

            # --- 3. ГРУППЫ ЗДОРОВЬЯ ---
            if student.health_group == 2 and (is_window_side or is_door_side):
                f_health += self.W_HEALTH_DRAFT
            if student.health_group >= 4 and desk_idx > 2:
                f_health += (student.health_group * self.W_HEALTH_RISK)

            # --- 4. РОСТ ---
            if desk_idx < self.desks - 1:
                behind_idx = i + 2
                if behind_idx < self.total_seats:
                    student_behind = best_chromosome[behind_idx]
                    if student_behind is not None:
                        if student.height > student_behind.height:
                            f_height += int((student.height - student_behind.height) * self.W_HEIGHT_OVERLAP)
            
            # --- 5. СВЯЗИ С СОСЕДОМ И СОЦИОМЕТРИЯ ---
            neighbor_idx = i + 1 if i % 2 == 0 else i - 1
            if neighbor_idx < self.total_seats:
                neighbor = best_chromosome[neighbor_idx]
                if neighbor is not None:
                    if student.gpa < 3.20 and neighbor.gpa < 3.20:
                        f_gpa += self.W_GPA_DOUBLE_WEAK
                    
                    if student.sociability == 3 and neighbor.sociability == 3:
                        f_sociability += self.W_SOC_DOUBLE_TALK

                    if neighbor.id in self.preferred_map[student.id]:
                        f_preferred_bonus += self.W_PREF_BONUS
                    
                    if neighbor.id in self.disliked_map[student.id]:
                        f_disliked_penalty += self.W_DISLIKED_PENALTY

        # --- ДИНАМИЧЕСКАЯ НОРМАЛИЗАЦИЯ ---
        count = max(len(self.students), 1)

        max_med_shf = count * 800
        max_phys_shf = count * 400
        max_gpa_shf = (count // 2) * self.W_GPA_DOUBLE_WEAK
        max_soc_shf = (count // 2) * (self.W_SOC_DOUBLE_TALK + self.W_DISLIKED_PENALTY)

        k_med = max(0, min(100, int((1 - (f_eyesight + f_hearing) / max_med_shf) * 100)))
        k_phys = max(0, min(100, int((1 - (f_height + f_health) / max_phys_shf) * 100)))
        k_gpa = max(0, min(100, int((1 - f_gpa / max_gpa_shf) * 100)))
        
        raw_social_score = 1 - (f_sociability + f_disliked_penalty) / max_soc_shf
        if f_preferred_bonus > 0:
            raw_social_score += (f_preferred_bonus / (count * self.W_PREF_BONUS)) * 0.1
            
        k_soc = max(0, min(100, int(raw_social_score * 100)))

        total_efficiency = int((k_med * 0.4) + (k_phys * 0.3) + (k_gpa * 0.15) + (k_soc * 0.15))
        total_efficiency = max(0, min(100, total_efficiency))

        return {
            'total_efficiency': total_efficiency,
            'k_medical': k_med,
            'k_physical': k_phys,
            'k_gpa': k_gpa,
            'k_social': k_soc
        }

    def create_individual(self):
        ind = self.students[:]
        while len(ind) < self.total_seats:
            ind.append(None)
        random.shuffle(ind)
        return ind

    def crossover(self, parent1, parent2):
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[start:end] = parent1[start:end]

        placed_students = {s for s in child[start:end] if s is not None}
        p2_pool = [s for s in parent2 if s is not None and s not in placed_students]
        
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

        while p2_idx < len(p2_pool):
            for i in range(size):
                if child[i] is None and (i < start or i >= end):
                    child[i] = p2_pool[p2_idx]
                    p2_idx += 1
                    break
        return child

    def mutate(self, chromosome):
        idx1, idx2 = random.sample(range(len(chromosome)), 2)
        chromosome[idx1], chromosome[idx2] = chromosome[idx2], chromosome[idx1]

    def solve(self):
        if not self.students:
            return []
        population = [self.create_individual() for _ in range(self.pop_size)]

        for _ in range(self.generations):
            population = sorted(population, key=self.fitness, reverse=True)
            new_gen = population[:15]
            while len(new_gen) < self.pop_size:
                p1, p2 = random.sample(population[:35], 2)
                child = self.crossover(p1, p2)
                if random.random() < 0.30:
                    self.mutate(child)
                new_gen.append(child)
            population = new_gen
            
        population = sorted(population, key=self.fitness, reverse=True)
        return population[0]


def generate_seating_chart(best_plan, classroom_obj, filename=None):
    # Настройки размеров те же
    cell_width, cell_height, padding, margin_top = 250, 120, 50, 100
    rows = classroom_obj.rows_count
    desks_per_row = classroom_obj.desks_per_row
        
    img_width = (cell_width * 2 + padding) * rows + padding * (rows + 1)
    img_height = (cell_height + padding) * desks_per_row + margin_top + padding

    img = Image.new('RGB', (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Ariral.TTF')
    font = ImageFont.truetype(font_path, 16)
    title_font = ImageFont.truetype(font_path, 30)

    draw.text((img_width//2 - 100, 20), "СХЕМА РАССАДКИ КЛАССА", fill=(0, 0, 0), font=title_font)

    for r in range(rows):
        x_offset = padding + r * (cell_width * 2 + padding + 20)
        draw.text((x_offset + cell_width - 20, 70), f"РЯД {r+1}", fill=(100, 100, 100), font=font)

        row_start = r * (desks_per_row * 2)
        for d in range(desks_per_row):
            y_offset = margin_top + d * (cell_height + padding)

            # Рисуем парту
            draw.rectangle([x_offset, y_offset, x_offset + cell_width * 2, y_offset + cell_height], outline=(0, 0, 0), width=2)
            draw.line([x_offset + cell_width, y_offset, x_offset + cell_width, y_offset + cell_height], fill=(200, 200, 200))

            # Получаем данные учеников
            s1 = best_plan[row_start + d*2]
            s2 = best_plan[row_start + d*2 + 1]

            name1 = s1.full_name if s1 else "ПУСТО"
            name2 = s2.full_name if s2 else "ПУСТО"

            # Имена
            draw.text((x_offset + 10, y_offset + 40), name1[:25], fill=(0, 0, 0), font=font)
            draw.text((x_offset + cell_width + 10, y_offset + 40), name2[:25], fill=(0, 0, 0), font=font)

            # Номер парты
            draw.text((x_offset - 30, y_offset + cell_height//2), f"П{d+1}", fill=(150, 150, 150), font=font)
        # Сохранение в MEDIA_ROOT
        if not filename:
            filename = f"chart_{classroom_obj.pk}.png"
        
    relative_path = os.path.join('seating_charts', filename)
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Создаем папку, если её нет
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    img.save(full_path)
    return relative_path  # Возвращаем путь для базы данных
from collections import defaultdict


def distribute_olympians_to_classrooms(event, event_olympians, classrooms):
    """
    Распределяет пулл участников/команд по аудиториям турнира 
    с учетом регламента (командный или индивидуальный).
    """
    sorted_classrooms = sorted(
        classrooms, 
        key=lambda c: c.rows_count * c.desks_per_row * 2,
        reverse=True
    )
    
    allocation = {c.id: [] for c in sorted_classrooms}
    classroom_limits = {c.id: c.rows_count * c.desks_per_row * 2 for c in sorted_classrooms}
    
    total_capacity = sum(classroom_limits.values())
    if len(event_olympians) > total_capacity:
        raise ValueError(f"Недостаточно мест во всех аудиториях! Требуется: {len(event_olympians)}, Доступно: {total_capacity}")

    c_idx = 0
    num_classrooms = len(sorted_classrooms)

    if event.is_team_event:
        team_groups = defaultdict(list)
        for o in event_olympians:
            if o.team_id:
                team_groups[o.team_id].append(o)
            else:
                team_groups[f"SINGLE-{o.id}"].append(o)
        
        school_teams = defaultdict(list)
        for team_id, members in team_groups.items():
            lead_school = members[0].school
            school_teams[lead_school].append((team_id, members))
            
        mixed_teams = []
        while any(school_teams.values()):
            for school in list(school_teams.keys()):
                if school_teams[school]:
                    mixed_teams.append(school_teams[school].pop(0))

        for team_id, members in mixed_teams:
            team_size = len(members)
            attempts = 0
            
            while len(allocation[sorted_classrooms[c_idx].id]) + team_size > classroom_limits[sorted_classrooms[c_idx].id]:
                c_idx = (c_idx + 1) % num_classrooms
                attempts += 1
                if attempts > num_classrooms:
                    break
            
            for olympian in members:
                allocation[sorted_classrooms[c_idx].id].append(olympian)
            
            c_idx = (c_idx + 1) % num_classrooms

    else:
        school_groups = defaultdict(list)
        for o in event_olympians:
            school_groups[o.school].append(o)

        mixed_olympians = []
        while any(school_groups.values()):
            for school in list(school_groups.keys()):
                if school_groups[school]:
                    mixed_olympians.append(school_groups[school].pop(0))

        for olympian in mixed_olympians:
            attempts = 0
            while len(allocation[sorted_classrooms[c_idx].id]) >= classroom_limits[sorted_classrooms[c_idx].id]:
                c_idx = (c_idx + 1) % num_classrooms
                attempts += 1
                if attempts > num_classrooms:
                    break

            allocation[sorted_classrooms[c_idx].id].append(olympian)
            c_idx = (c_idx + 1) % num_classrooms

    return allocation

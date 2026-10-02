import csv
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# 1. Helper function to extract max marks from headers
def get_max_from_header(header_name):
    try:
        return float(header_name.split('/')[1].strip())
    except (IndexError, ValueError):
        return 0.0

students = {}

# 2. Open and load grades from the original files
def load_grades(filename, section_name):
    max_marks = 0.0
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for col in reader.fieldnames:
            if col and col not in ['Last name', 'First name', 'ID']:
                max_marks += get_max_from_header(col)
        for row in reader:
            sid = row.get('ID')
            if not sid: continue
            if sid not in students:
                students[sid] = {
                    'ID': sid, 'Last name': row.get('Last name', ''), 'First name': row.get('First name', ''),
                    'CA1 Marks': 0.0, 'CA2 Marks': 0.0, 'EXERCISE Marks': 0.0, 'FINAL Marks': 0.0, 'PROJECT Marks': 0.0
                }
            marks = 0.0
            for k, v in row.items():
                if k and k not in ['Last name', 'First name', 'ID']:
                    try: marks += float(v)
                    except (ValueError, TypeError): pass
            students[sid][f'{section_name} Marks'] = marks
    return max_marks

ca1_max = load_grades("Grades CA 1.csv", "CA1")
ca2_max = load_grades("Grades CA 2.csv", "CA2")
ex_max = load_grades("Grades Exercises.csv", "EXERCISE")
final_max = load_grades("Grades Final Exam.csv", "FINAL")
proj_max = 10.0

# 3. Load group project grades
group_map = {}
with open("Grades Groups.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        grp = row.get('Group')
        grade = row.get('Grade /10')
        if grp and grade:
            group_map[grp] = float(grade)

with open("Groups.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        sid = row.get('ID')
        grp = row.get('Group')
        if sid in students:
            students[sid]['PROJECT Marks'] = group_map.get(grp, 0.0)

# 4. Calculate final percentages and totals
for sid, s in students.items():
    s['CA1 %'] = (s['CA1 Marks'] / ca1_max * 15) if ca1_max else 0
    s['CA2 %'] = (s['CA2 Marks'] / ca2_max * 15) if ca2_max else 0
    s['EXERCISE %'] = (s['EXERCISE Marks'] / ex_max * 15) if ex_max else 0
    s['FINAL %'] = (s['FINAL Marks'] / final_max * 40) if final_max else 0
    s['PROJECT %'] = (s['PROJECT Marks'] / proj_max * 15) if proj_max else 0
    
    s['Total Marks'] = s['CA1 Marks'] + s['CA2 Marks'] + s['EXERCISE Marks'] + s['FINAL Marks'] + s['PROJECT Marks']
    s['Total %'] = s['CA1 %'] + s['CA2 %'] + s['EXERCISE %'] + s['FINAL %'] + s['PROJECT %']
    
    score = s['Total %']
    if score >= 85: grade = 'A+'
    elif score >= 80: grade = 'A'
    elif score >= 75: grade = 'A-'
    elif score >= 70: grade = 'B+'
    elif score >= 65: grade = 'B'
    elif score >= 60: grade = 'B-'
    elif score >= 55: grade = 'C+'
    elif score >= 50: grade = 'C'
    elif score >= 45: grade = 'D+'
    elif score >= 40: grade = 'D'
    else: grade = 'F'
    s['Grade'] = grade

# Sort by ID chronologically
sorted_students = sorted(students.values(), key=lambda x: str(x['ID']))


# ---------------------------------------------------------
# 5. DATA COMPILATION & EXPORT
# ---------------------------------------------------------
table_data = []

# Row 1: Main Headers
table_data.append([
    "Last name", "First name", "ID", 
    "CA1", "", "CA2", "", "Exercise", "", 
    "Finals", "", "Project", "", 
    "Total Percentage/ Marks", "", "Grade"
])

# Row 2: Sub-headers
table_data.append([
    "", "", "", 
    "Percentage", "Marks", "Percentage", "Marks", "Percentage", "Marks", 
    "Percentage", "Marks", "Percentage", "Marks", 
    "Percentage", "Marks", ""
])

# Rows 3+: Student Data
for s in sorted_students:
    table_data.append([
        s['Last name'], s['First name'], s['ID'],
        f"{s['CA1 %']:.2f}", f"{s['CA1 Marks']:.2f}", # <--- Shifted CA1 Marks here
        f"{s['CA2 %']:.2f}", f"{s['CA2 Marks']:.2f}",
        f"{s['EXERCISE %']:.2f}", f"{s['EXERCISE Marks']:.2f}",
        f"{s['FINAL %']:.2f}", f"{s['FINAL Marks']:.2f}",
        f"{s['PROJECT %']:.2f}", f"{s['PROJECT Marks']:.2f}",
        f"{s['Total %']:.2f}", f"{s['Total Marks']:.2f}", 
        s['Grade']
    ])

# Save CSV
csv_filename = "Final_Calculated_Grades_Formatted.csv"
with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',')
    for row in table_data:
        writer.writerow(row)

# ---------------------------------------------------------
# 6. REPORTLAB PDF GENERATION
# ---------------------------------------------------------
pdf_filename = "Student_Grades_Report.pdf"
pdf = SimpleDocTemplate(pdf_filename, pagesize=landscape(letter))
table = Table(table_data)

style = TableStyle([
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 7),
    
    # Updated span offsets to reflect new column layout
    ('SPAN', (3, 0), (4, 0)),   # Merge CA1 (Col D to E)
    ('SPAN', (5, 0), (6, 0)),   # Merge CA2 (Col F to G)
    ('SPAN', (7, 0), (8, 0)),   # Merge Exercise (Col H to I)
    ('SPAN', (9, 0), (10, 0)),  # Merge Finals (Col J to K)
    ('SPAN', (11, 0), (12, 0)), # Merge Project (Col L to M)
    ('SPAN', (13, 0), (14, 0)), # Merge Total (Col N to O)
])

table.setStyle(style)
pdf.build([table])

print(f"Success! Data saved to {csv_filename} and {pdf_filename}")
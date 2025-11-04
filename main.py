import json
import csv
import xml.etree.ElementTree as ET
import re
import os
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
last_generated_data = None
last_fields = None
last_category = None

# ---------- FIELD GENERATION PATTERNS ----------
field_patterns = [
    # Personal
    (r"name", lambda: fake.name()),
    (r"first_name", lambda: fake.first_name()),
    (r"last_name", lambda: fake.last_name()),
    (r"email", lambda: fake.email()),
    (r"user(name)?", lambda: fake.user_name()),
    (r"dob|birthdate|date_of_birth", None),  # handled in inter-field logic
    (r"age", None),  # handled in inter-field logic
    (r"phone", lambda: fake.phone_number()),
    (r"address", lambda: fake.address().replace("\n", ", ")),
    (r"registered_at", lambda: fake.date_time_this_year().isoformat()),

    # Location
    (r"state", lambda: fake.state()),
    (r"city", lambda: fake.city()),
    (r"country", lambda: fake.country()),
    (r"zipcode|postal", lambda: fake.postcode()),

    # Company / Job
    (r"company|organization|employer|bank", lambda: fake.company()),
    (r"job|title|position", lambda: fake.job()),
    (r"department", lambda: fake.bs()),

    # Banking
    (r"bank_account|account_number", lambda: str(random.randint(100000000000, 999999999999))),
    (r"aba|routing", lambda: "{:09d}".format(random.randint(0, 999999999))),
    (r"balance", lambda: round(random.uniform(1000, 100000), 2)),
    (r"ifsc|swift", lambda: fake.swift()),
    (r"bank_name", lambda: fake.company()),

    # School
    (r"grade", None),  # handled in inter-field logic
    (r"gpa", None),  # handled in college logic
    (r"school|university", lambda: fake.company()),

    # College
    (r"year", None),  # handled in college logic
    (r"major", None),  # handled in college logic

    # Fallback
    (r".*", lambda: fake.word()),
]

def generate_field_value(field_name, category=None):
    f = field_name.lower().strip().replace(" ", "_")
    for pattern, generator in field_patterns:
        if re.search(pattern, f):
            if generator:
                return generator()
            else:
                return None
    return fake.word()

# ---------- RECORD GENERATORS ----------
def generate_student_record(fields):
    """K-12 Student: DOB ↔ Age ↔ Grade"""
    record = {}
    age = None
    dob = None
    grade = None

    # DOB first if present
    if "DOB" in fields or "dob" in [f.lower() for f in fields]:
        dob = fake.date_of_birth(minimum_age=5, maximum_age=18)
        record["DOB"] = dob.strftime("%Y-%m-%d")
        age = (datetime.today().date() - dob).days // 365
        if "Age" in fields:
            record["Age"] = age

    # Age if present but DOB missing
    if "Age" in fields and age is None:
        age = random.randint(5, 18)
        record["Age"] = age
        if "DOB" in fields:
            dob = datetime.today().date() - timedelta(days=age*365 + random.randint(0,364))
            record["DOB"] = dob.strftime("%Y-%m-%d")

    # Grade mapping
    if "Grade" in fields:
        grade = min(max(age - 5 + 1, 1), 12) if age else random.randint(1,12)
        record["Grade"] = grade

    # Other fields
    for f in fields:
        if f not in record:
            record[f] = generate_field_value(f, "student")

    return record

def generate_college_student_record(fields):
    """College student: DOB ↔ Age ↔ Year ↔ GPA"""
    record = {}
    age = None
    dob = None
    year = None

    if "DOB" in fields or "dob" in [f.lower() for f in fields]:
        dob = fake.date_of_birth(minimum_age=17, maximum_age=25)
        record["DOB"] = dob.strftime("%Y-%m-%d")
        age = (datetime.today().date() - dob).days // 365
        if "Age" in fields:
            record["Age"] = age

    if "Age" in fields and age is None:
        age = random.randint(17,25)
        record["Age"] = age
        if "DOB" in fields:
            dob = datetime.today().date() - timedelta(days=age*365 + random.randint(0,364))
            record["DOB"] = dob.strftime("%Y-%m-%d")

    # Year mapping
    if "Year" in fields or "Grade" in fields:
        if age:
            if age <= 18:
                year = "Freshman"
            elif age == 19:
                year = "Sophomore"
            elif age == 20:
                year = "Junior"
            elif 21 <= age <= 22:
                year = "Senior"
            else:
                year = "Graduate"
        else:
            year = random.choice(["Freshman","Sophomore","Junior","Senior","Graduate"])
        record["Year"] = year

    # GPA
    if "GPA" in fields:
        record["GPA"] = round(random.uniform(2.0, 4.0),2)

    # Major / University
    if "Major" in fields:
        majors = ["Computer Science", "Business", "Economics", "Psychology", "Engineering", "Biology", "Mathematics"]
        record["Major"] = random.choice(majors)
    if "University" in fields:
        record["University"] = fake.company() + " University"

    # Other fields
    for f in fields:
        if f not in record:
            record[f] = generate_field_value(f, "college_student")

    return record

def generate_generic_record(fields, category=None):
    """Other categories (bank, employee, customer, user)"""
    record = {}
    for f in fields:
        record[f] = generate_field_value(f, category)
    return record

# ---------- FILE SAVE HELPERS ----------
def save_to_json(data, filename="data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved to {os.path.abspath(filename)}")

def save_to_csv(data, filename="data.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Saved to {os.path.abspath(filename)}")

def save_to_xml(data, filename="data.xml"):
    root = ET.Element("records")
    for record in data:
        item = ET.SubElement(root, "record")
        for key, value in record.items():
            child = ET.SubElement(item, key.replace(" ", "_"))
            child.text = str(value)
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"✅ Saved to {os.path.abspath(filename)}")

# ---------- DEFAULT FIELD SETS ----------
default_fields_by_category = {
    "student": ["Name","Age","Grade","GPA","DOB","City","State","Address","School"],
    "college_student": ["Name","Age","Year","GPA","DOB","Major","University","City","State","Address"],
    "bank": ["Name","DOB","Bank Name","ABA Number","Bank Account Number","Balance","City","State"],
    "employee": ["Name","Email","Phone","Job Title","Company","Department","City","State","Address"],
    "customer": ["Name","Email","Phone","Address","City","State","Loyalty Points","Membership Level"],
    "user": ["Name","Email","Username","Phone","Address","Registered At","City","State"],
}

# ---------- COMMAND PARSER ----------
def parse_generate_command(text):
    count_match = re.search(r"generate\s+(\d+)", text)
    count = int(count_match.group(1)) if count_match else 5

    category = None
    for c in default_fields_by_category.keys():
        if c in text.lower():
            category = c
            break

    fields_match = re.search(r"with\s+(.+)", text)
    if fields_match:
        raw_fields = [f.strip() for f in fields_match.group(1).split(",")]
        fields = []
        for f in raw_fields:
            num_match = re.match(r"(\d+)\s*fields", f)
            if num_match:
                n = int(num_match.group(1))
                default_fields = default_fields_by_category.get(category, ["Field1","Field2"])
                fields += default_fields[:n] if n <= len(default_fields) else default_fields + [f"CustomField{i}" for i in range(1,n-len(default_fields)+1)]
            else:
                fields.append(f.split(":")[0].strip())
    else:
        fields = default_fields_by_category.get(category, ["Name","Email","Phone","Address"])

    return count, fields, category

# ---------- AGENT LOGIC ----------
def run_agent(command):
    global last_generated_data, last_fields, last_category

    command_lower = command.lower()

    # --- GENERATE NEW RECORDS ---
    if command_lower.startswith("generate"):
        count, fields, category = parse_generate_command(command)
        data = []
        for _ in range(count):
            if category=="student":
                data.append(generate_student_record(fields))
            elif category=="college_student":
                data.append(generate_college_student_record(fields))
            else:
                data.append(generate_generic_record(fields, category))
        last_generated_data = data
        last_fields = fields.copy()
        last_category = category
        print(f"\n✅ Generated {count} {category or 'record(s)'}:\n")
        for d in data:
            for k,v in d.items():
                print(f"  - {k}: {v}")
            print()
        return

    # --- ADD FIELDS ---
    if command_lower.startswith("add "):
        if not last_generated_data or not last_fields:
            print("⚠️ No previous data to add fields to. Generate something first.")
            return
        add_fields_match = re.findall(r"add\s+(.+)", command, re.IGNORECASE)
        if add_fields_match:
            new_fields = [f.strip() for f in add_fields_match[0].split(",")]
            for i, record in enumerate(last_generated_data):
                if last_category=="student":
                    last_generated_data[i] = generate_student_record(list(record.keys())+new_fields)
                elif last_category=="college_student":
                    last_generated_data[i] = generate_college_student_record(list(record.keys())+new_fields)
                else:
                    for field in new_fields:
                        if field not in record:
                            record[field] = generate_field_value(field, last_category)
            last_fields += [f for f in new_fields if f not in last_fields]
            print(f"\n✅ Added fields {', '.join(new_fields)} to last generated records.\n")
            for d in last_generated_data:
                for k,v in d.items():
                    print(f"  - {k}: {v}")
                print()
        return

    # --- REMOVE FIELDS ---
    if command_lower.startswith("remove "):
        if not last_generated_data or not last_fields:
            print("⚠️ No previous data to remove fields from. Generate something first.")
            return
        remove_fields_match = re.findall(r"remove\s+(.+)", command, re.IGNORECASE)
        if remove_fields_match:
            rem_fields = [f.strip() for f in remove_fields_match[0].split(",")]
            for record in last_generated_data:
                for field in rem_fields:
                    if field in record:
                        del record[field]
            last_fields = [f for f in last_fields if f not in rem_fields]
            print(f"\n✅ Removed fields {', '.join(rem_fields)} from last generated records.\n")
            for d in last_generated_data:
                for k,v in d.items():
                    print(f"  - {k}: {v}")
                print()
        return

    # --- SAVE DATA ---
    if "save" in command_lower:
        if not last_generated_data:
            print("⚠️ No generated data available to save. Please generate something first.")
            return
        if "json" in command_lower:
            save_to_json(last_generated_data)
        elif "csv" in command_lower:
            save_to_csv(last_generated_data)
        elif "xml" in command_lower:
            save_to_xml(last_generated_data)
        else:
            print("⚠️ Please specify a valid format: JSON, CSV, or XML.")
        return

    # --- EXIT ---
    if command_lower in ["exit","quit"]:
        print("👋 Exiting Test Data Generator.")
        exit()

    print("⚠️ Unknown command. Try 'generate 5 students with 6 fields', 'add DOB', 'remove Phone', or 'save as csv'.")

# ---------- MAIN LOOP ----------
if __name__ == "__main__":
    print("💡 AI Test Data Generator v9.1 (Fully Dynamic, Stateful, Realistic Fields)")
    print("Examples:")
    print("   → generate 5 students with 6 fields")
    print("   → generate 5 college_students with 6 fields")
    print("   → add DOB, GPA")
    print("   → remove Age")
    print("   → save as csv/json/xml")
    print("   → exit\n")

    while True:
        user_input = input("You: ")
        run_agent(user_input)

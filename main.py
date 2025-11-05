import re
import json
import csv
import random
from datetime import datetime, timedelta
from faker import Faker
from xml.etree.ElementTree import Element, SubElement, ElementTree

fake = Faker()
session_data = {"last_generated": None, "last_type": None}

# -------------------- FIELD MAPS & ALIASES --------------------

FIELD_MAP = {
    "name": lambda: fake.name(),
    "email": lambda: fake.email(),
    "phone": lambda: fake.phone_number(),
    "address": lambda: fake.address().replace("\n", ", "),
    "city": lambda: fake.city(),
    "state": lambda: fake.state(),
    "country": lambda: fake.country(),
    "zipcode": lambda: fake.zipcode(),

    # Students
    "dob": lambda min_age=5, max_age=22: fake.date_of_birth(minimum_age=min_age, maximum_age=max_age),
    "age": lambda min_age=5, max_age=22: random.randint(min_age, max_age),
    "gpa": lambda: round(random.uniform(2.0, 4.0), 2),
    "grade": lambda age: max(1, min(12, age - 5 + 1)),
    "school name": lambda age: generate_school_name(age),
    "college name": lambda: random.choice([
        "MIT", "Stanford University", "Harvard University", "Yale University",
        "Princeton University", "UCLA", "UC Berkeley", "Columbia University"
    ]),
    "major": lambda: random.choice(["Computer Science", "Biology", "Business", "Engineering", "Mathematics", "Economics"]),
    "year": lambda age: random.randint(1, 4),

    # Bank
    "bank name": lambda: random.choice(["Chase", "Bank of America", "Citi", "Wells Fargo", "PNC"]),
    "aba number": lambda: f"{random.randint(100000000,999999999)}",
    "account number": lambda: f"{random.randint(1000000000,9999999999)}",
    "balance": lambda: round(random.uniform(1000, 100000),2),

    # Employee
    "job title": lambda: random.choice(["Software Engineer", "Manager", "Data Analyst", "Consultant", "Designer"]),
    "company": lambda: fake.company(),
}

FIELD_ALIASES = {
    "university": "college name",
    "college": "college name",
    "school": "school name",
    "bank": "bank name",
    "job": "job title",
    "aba": "aba number",
    "account": "account number",
}

ENTITY_ALIASES = {
    "student": "student",
    "students": "student",
    "college_student": "college_student",
    "college_students": "college_student",
    "bank_customer": "bank_customer",
    "bank_customers": "bank_customer",
    "employee": "employee",
    "employees": "employee",
}

DEFAULT_FIELDS = {
    "student": [
        "Name",
        "Age",
        "Grade",
        "GPA",
        "DOB",
        "City",
        "State",
        "Address",
        "School Name",
        "Country",
        "Zipcode",
    ],
    "college_student": [
        "Name",
        "Age",
        "DOB",
        "College Name",
        "Major",
        "Year",
        "GPA",
        "City",
        "State",
        "Country",
    ],
    "bank_customer": [
        "Name",
        "Age",
        "DOB",
        "Bank Name",
        "ABA Number",
        "Account Number",
        "Balance",
        "Email",
        "Phone",
        "Address",
        "City",
        "State",
        "Country",
    ],
    "employee": [
        "Name",
        "Age",
        "DOB",
        "Job Title",
        "Company",
        "Email",
        "Phone",
        "Address",
        "City",
        "State",
        "Country",
    ],
}

AGE_RANGES = {
    "student": (5, 18),
    "college_student": (18, 25),
    "bank_customer": (18, 80),
    "employee": (22, 65),
}


def calculate_age_from_dob(dob):
    if isinstance(dob, str):
        dob = datetime.fromisoformat(dob).date()
    elif isinstance(dob, datetime):
        dob = dob.date()
    today = datetime.today().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def generate_birthdate_for_age(age):
    age = int(age)
    today = datetime.today().date()
    start_date = today - timedelta(days=(age + 1) * 365)
    end_date = today - timedelta(days=age * 365)
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    delta_days = max((end_date - start_date).days, 0)
    for _ in range(20):
        candidate = start_date + timedelta(days=random.randint(0, delta_days if delta_days > 0 else 0))
        if calculate_age_from_dob(candidate) == age:
            return candidate
    # fallback to adjusting candidate if loop fails
    candidate = end_date
    age_delta = age - calculate_age_from_dob(candidate)
    if age_delta:
        try:
            candidate = candidate.replace(year=candidate.year - age_delta)
        except ValueError:
            # handle leap day adjustments gracefully
            candidate = candidate.replace(month=3, day=1, year=candidate.year - age_delta)
    return candidate


def random_age_and_dob(min_age, max_age):
    dob = fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)
    age = calculate_age_from_dob(dob)
    if age < min_age or age > max_age:
        # regenerate if faker returns outside the strict bounds (edge case)
        return random_age_and_dob(min_age, max_age)
    return age, dob


def find_field_key(record, field_name):
    target = field_name.lower()
    for key in list(record.keys()):
        if key.lower() == target:
            return key
    return None

# -------------------- GENERATORS --------------------

def generate_school_name(age):
    if age <= 10:
        school_type = "Elementary School"
    elif 11 <= age <= 14:
        school_type = "Middle School"
    else:
        school_type = "High School"

    prefixes = ["Greenwood", "Riverdale", "Sunrise", "St. Thomas", "Oakwood",
                "Blue Ridge", "Cedar Grove", "Hillcrest", "Maple Leaf", "Silver Lake"]

    return f"{random.choice(prefixes)} {school_type}"

def generate_student_record(fields):
    age, dob = random_age_and_dob(*AGE_RANGES["student"])
    grade = max(1, min(12, age - 5 + 1))
    record = {}
    for field in fields:
        f_lower = field.lower()
        f_lower = FIELD_ALIASES.get(f_lower, f_lower)  # map aliases
        if f_lower == "age":
            record[field] = age
        elif f_lower == "dob":
            record[field] = dob.isoformat()
        elif f_lower == "grade":
            record[field] = grade
        elif f_lower == "school name":
            record[field] = generate_school_name(age)
        else:
            record[field] = FIELD_MAP.get(f_lower, lambda: fake.word())()
    return record

def generate_college_student_record(fields):
    age, dob = random_age_and_dob(*AGE_RANGES["college_student"])
    year = random.randint(1,4)
    record = {}
    for field in fields:
        f_lower = field.lower()
        f_lower = FIELD_ALIASES.get(f_lower, f_lower)  # map aliases
        if f_lower == "age":
            record[field] = age
        elif f_lower == "dob":
            record[field] = dob.isoformat()
        elif f_lower == "year":
            record[field] = year
        elif f_lower == "college name":
            record[field] = FIELD_MAP["college name"]()
        elif f_lower == "major":
            record[field] = FIELD_MAP["major"]()
        elif f_lower == "gpa":
            record[field] = FIELD_MAP["gpa"]()
        else:
            record[field] = FIELD_MAP.get(f_lower, lambda: fake.word())()
    return record

def generate_bank_customer_record(fields):
    age, dob = random_age_and_dob(*AGE_RANGES["bank_customer"])
    record = {}
    for field in fields:
        f_lower = field.lower()
        f_lower = FIELD_ALIASES.get(f_lower, f_lower)
        if f_lower == "age":
            record[field] = age
        elif f_lower == "dob":
            record[field] = dob.isoformat()
        elif f_lower == "balance":
            record[field] = FIELD_MAP["balance"]()
        elif f_lower == "aba number":
            record[field] = FIELD_MAP["aba number"]()
        elif f_lower == "account number":
            record[field] = FIELD_MAP["account number"]()
        elif f_lower == "bank name":
            record[field] = FIELD_MAP["bank name"]()
        else:
            record[field] = FIELD_MAP.get(f_lower, lambda: fake.word())()
    return record

def generate_employee_record(fields):
    age, dob = random_age_and_dob(*AGE_RANGES["employee"])
    record = {}
    for field in fields:
        f_lower = field.lower()
        f_lower = FIELD_ALIASES.get(f_lower, f_lower)
        if f_lower == "age":
            record[field] = age
        elif f_lower == "dob":
            record[field] = dob.isoformat()
        elif f_lower == "job title":
            record[field] = FIELD_MAP["job title"]()
        elif f_lower == "company":
            record[field] = FIELD_MAP["company"]()
        else:
            record[field] = FIELD_MAP.get(f_lower, lambda: fake.word())()
    return record


ENTITY_GENERATORS = {
    "student": generate_student_record,
    "college_student": generate_college_student_record,
    "bank_customer": generate_bank_customer_record,
    "employee": generate_employee_record,
}


def normalize_entity_type(entity_type):
    """Normalize entity labels (including plural forms) to the canonical key."""

    if not entity_type:
        return None
    return ENTITY_ALIASES.get(entity_type.lower())


def generate_entity_record(entity_type, fields):
    normalized = normalize_entity_type(entity_type)
    if normalized in ENTITY_GENERATORS:
        return ENTITY_GENERATORS[normalized](fields)
    return {f: fake.word() for f in fields}

# -------------------- UPDATE LAST GENERATED --------------------

def update_last_generated(add_fields=None, remove_fields=None):
    if not session_data["last_generated"]:
        print("⚠️ No previous data to update. Please generate first.")
        return
    
    add_fields = [f.strip().title() for f in add_fields] if add_fields else []
    remove_fields = [f.strip().title() for f in remove_fields] if remove_fields else []

    updated_data = []
    entity_type = session_data.get("last_type", "student")
    normalized_type = normalize_entity_type(entity_type) or entity_type
    lower_add_fields = [f.lower() for f in add_fields]

    for record in session_data["last_generated"]:
        # Remove fields
        for field in remove_fields:
            existing_key = find_field_key(record, field)
            if existing_key:
                record.pop(existing_key, None)
        # Add new fields
        for field in add_fields:
            new_val = generate_entity_record(normalized_type, [field])[field]
            record[field] = new_val
            f_lower = field.lower()
            age_min, age_max = AGE_RANGES.get(normalized_type, (5, 80))
            if f_lower == "dob":
                age_key = find_field_key(record, "Age")
                age_value = None
                if age_key is not None:
                    age_value = record.get(age_key)
                    try:
                        age_value = int(age_value)
                    except (TypeError, ValueError):
                        age_value = None
                if age_value is not None:
                    dob = generate_birthdate_for_age(age_value)
                    record[field] = dob.isoformat()
                else:
                    age_value, dob = random_age_and_dob(age_min, age_max)
                    record[field] = dob.isoformat()
                    if age_key is not None:
                        record[age_key] = age_value
            elif f_lower == "age":
                dob_key = find_field_key(record, "Dob")
                dob_value = record.get(dob_key) if dob_key else None
                if dob_value is not None:
                    record[field] = calculate_age_from_dob(dob_value)
                else:
                    age_value, dob = random_age_and_dob(age_min, age_max)
                    record[field] = age_value
                    if "dob" not in lower_add_fields and dob_key is not None:
                        record[dob_key] = dob.isoformat()
                    elif "dob" in lower_add_fields and dob_key is None:
                        # ensure upcoming DOB addition uses the generated pair
                        record.setdefault("Dob", dob.isoformat())
        updated_data.append(record)

    session_data["last_generated"] = updated_data
    print(f"✅ Updated last generated data with additions/removals.\n")
    for d in updated_data:
        print(json.dumps(d, indent=2))

# -------------------- SAVE --------------------

def save_data(data, format_type):
    filename = f"generated_data.{format_type}"
    if format_type == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    elif format_type == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    elif format_type == "xml":
        root = Element("Records")
        for rec in data:
            rec_elem = SubElement(root, "Record")
            for k, v in rec.items():
                field_elem = SubElement(rec_elem, k.replace(" ", "_"))
                field_elem.text = str(v)
        ElementTree(root).write(filename, encoding="utf-8", xml_declaration=True)
    print(f"💾 Saved {len(data)} records to {filename}")

# -------------------- AGENT / COMMAND --------------------

def run_agent(command):
    global session_data
    command = command.strip()

    # --- Generate ---
    if match := re.search(r"generate\s+(\d+)\s+(\w+)(?:\s+with\s+(.*))?$", command, re.I):
        count = int(match.group(1))
        raw_entity_type = match.group(2)
        entity_type = raw_entity_type.lower()
        normalized_type = normalize_entity_type(entity_type)
        field_part = match.group(3)
        if field_part:
            fields = [f.strip().title() for f in re.split(r",|\band\b", field_part) if f.strip()]
        else:
            fields = DEFAULT_FIELDS.get(normalized_type, ["Name"])

        data = [generate_entity_record(entity_type, fields) for _ in range(count)]
        session_data["last_generated"] = data
        session_data["last_type"] = normalized_type or entity_type

        entity_label = normalized_type or entity_type
        print(f"\n✅ Generated {count} {entity_label}(s):\n")
        for d in data:
            print(json.dumps(d, indent=2))
        return

    # --- Update Fields ---
    if "add" in command.lower() or "remove" in command.lower():
        add_fields = re.findall(r"add\s+([a-zA-Z_ ]+)", command, re.I)
        remove_fields = re.findall(r"remove\s+([a-zA-Z_ ]+)", command, re.I)
        update_last_generated(add_fields=add_fields, remove_fields=remove_fields)
        return

    # --- Save ---
    if command.lower().startswith("save"):
        if not session_data["last_generated"]:
            print("⚠️ No generated data available to save. Please generate something first.")
            return
        if "json" in command.lower():
            save_data(session_data["last_generated"], "json")
        elif "csv" in command.lower():
            save_data(session_data["last_generated"], "csv")
        elif "xml" in command.lower():
            save_data(session_data["last_generated"], "xml")
        else:
            print("💡 Please specify format: csv/json/xml")
        return

    # --- Exit ---
    if command.lower() in ["exit","quit"]:
        print("👋 Exiting AI Test Data Generator.")
        exit()

    print("⚙️ Unknown command. Try 'generate 5 students with Name, State, School Name', 'add City', 'remove Age', or 'save as csv/json/xml'.")

# -------------------- CLI --------------------

def main():
    print("💡 AI Test Data Generator v2.1 (Dynamic, Multi-Entity, Stateful, Realistic Aliases)")
    print("Examples:")
    print("  → generate 5 students with Name, State, School Name")
    print("  → generate 5 college_students with Name, Major, University, GPA")
    print("  → generate 5 bank_customers with Name, DOB, Bank, ABA Number")
    print("  → generate 5 employees with Name, Job, Company, Email")
    print("  → add City")
    print("  → remove Age")
    print("  → save as csv/json/xml")
    print("  → exit\n")

    while True:
        command = input("You: ")
        run_agent(command)

if __name__ == "__main__":
    main()

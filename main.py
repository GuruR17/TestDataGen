import json
import csv
import xml.etree.ElementTree as ET
from faker import Faker
import re
import os
from datetime import datetime, timedelta
import random

fake = Faker()
last_generated_data = None  # memory between actions

# ---------- GENERATION HELPERS ----------

def random_dob(min_age=18, max_age=70):
    today = datetime.today()
    age = random.randint(min_age, max_age)
    dob = today - timedelta(days=age * 365 + random.randint(0, 364))
    return dob.strftime("%Y-%m-%d")

def generate_record(fields, category=None):
    record = {}
    for field in fields:
        f = field.lower().strip()
        if f in ["name", "full name"]:
            record[field] = fake.name()
        elif f in ["email", "mail"]:
            record[field] = fake.email()
        elif f in ["username", "user name"]:
            record[field] = fake.user_name()
        elif f in ["dob", "date of birth", "birthdate"]:
            record[field] = random_dob()
        elif f in ["age"]:
            record[field] = random.randint(18, 70)
        elif f in ["phone", "phone number"]:
            record[field] = fake.phone_number()
        elif f in ["address"]:
            record[field] = fake.address().replace("\n", ", ")
        elif f in ["company", "organization", "employer"]:
            record[field] = fake.company()
        elif f in ["job title", "title", "position"]:
            record[field] = fake.job()
        elif f in ["registered at", "registration date"]:
            record[field] = fake.date_time_this_decade().isoformat()
        elif f in ["bank name"]:
            record[field] = fake.company() + " Bank"
        elif f in ["aba number", "routing number"]:
            record[field] = fake.bban()[:9]
        elif f in ["account number"]:
            record[field] = str(fake.random_number(digits=12))
        elif f in ["balance", "account balance"]:
            record[field] = round(random.uniform(1000, 100000), 2)
        elif f in ["ifsc code", "swift code"]:
            record[field] = fake.swift()
        else:
            # Default fallback
            record[field] = fake.word()
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

# ---------- MAIN AGENT LOGIC ----------

def parse_generate_command(text):
    """
    Examples:
    "generate 5 users aged 30 to 40"
    "generate 10 bank customers with Name, DOB, Bank Name, ABA Number"
    """
    count_match = re.search(r"generate\s+(\d+)", text)
    count = int(count_match.group(1)) if count_match else 5

    fields_match = re.search(r"with\s+(.+)", text)
    if fields_match:
        fields = [f.strip() for f in fields_match.group(1).split(",")]
    else:
        fields = ["Name", "Email", "Phone", "Address"]

    # detect category
    category = None
    for c in ["bank", "employee", "customer", "student", "user"]:
        if c in text.lower():
            category = c
            break

    return count, fields, category


def run_agent(command):
    global last_generated_data

    if command.lower().startswith("generate"):
        count, fields, category = parse_generate_command(command)
        data = [generate_record(fields, category) for _ in range(count)]
        last_generated_data = data
        print(f"\n✅ Generated {count} {category or 'record(s)'}:\n")
        for d in data:
            for k, v in d.items():
                print(f"  - {k}: {v}")
            print()
        return

    if "save" in command.lower():
        if not last_generated_data:
            print("⚠️ No generated data available to save. Please generate something first.")
            return
        if "json" in command.lower():
            save_to_json(last_generated_data)
        elif "csv" in command.lower():
            save_to_csv(last_generated_data)
        elif "xml" in command.lower():
            save_to_xml(last_generated_data)
        else:
            print("⚠️ Please specify a valid format: JSON, CSV, or XML.")
        return

    if command.lower() in ["exit", "quit"]:
        print("👋 Exiting Test Data Generator.")
        exit()

    print("⚠️ Unknown command. Try 'generate 5 users aged 25 to 35' or 'save as csv'.")


# ---------- MAIN LOOP ----------
if __name__ == "__main__":
    print("💡 Type commands like:")
    print("   → generate 10 bank customers with Name, DOB, Bank Name, ABA Number")
    print("   → save as csv")
    print("   → exit\n")

    while True:
        user_input = input("You: ")
        run_agent(user_input)

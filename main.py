import warnings
import os
import json
import random
from typing import List
from datetime import datetime, timedelta
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Suppress warnings before other imports
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

load_dotenv()

# -------- Tool Functions --------
def write_json(filepath: str, data: dict) -> str:
    """Write a Python dictionary as JSON to a file with pretty formatting."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return f"✅ Successfully wrote JSON data to '{filepath}' ({len(json.dumps(data))} characters)."
    except Exception as e:
        return f"❌ Error writing JSON: {str(e)}"


def write_xml(filepath: str, data: dict) -> str:
    """Write a Python dictionary as XML to a file."""
    def dict_to_xml(tag, d):
        """Convert a dict to an XML Element."""
        elem = ET.Element(tag)
        for key, val in d.items():
            if isinstance(val, dict):
                elem.append(dict_to_xml(key, val))
            elif isinstance(val, list):
                list_container = ET.Element(key)
                for item in val:
                    if isinstance(item, dict):
                        list_container.append(dict_to_xml("item", item))
                    else:
                        item_elem = ET.Element("item")
                        item_elem.text = str(item)
                        list_container.append(item_elem)
                elem.append(list_container)
            else:
                child = ET.Element(key)
                child.text = str(val)
                elem.append(child)
        return elem

    try:
        root = dict_to_xml("data", data)
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        return f"✅ Successfully wrote XML data to '{filepath}'."
    except Exception as e:
        return f"❌ Error writing XML: {str(e)}"


def read_json(filepath: str) -> str:
    """Read and return the contents of a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return f"❌ Error: File '{filepath}' not found."
    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON in file - {str(e)}"
    except Exception as e:
        return f"❌ Error reading JSON: {str(e)}"


def generate_sample_users(
    first_names: List[str],
    last_names: List[str],
    domains: List[str],
    min_age: int,
    max_age: int
) -> dict:
    """
    Generate sample user data including address info. 
    Count is determined by the length of first_names.
    """

    # Validation
    if not first_names:
        return {"error": "first_names list cannot be empty"}
    if not last_names:
        return {"error": "last_names list cannot be empty"}
    if not domains:
        return {"error": "domains list cannot be empty"}
    if min_age > max_age:
        return {"error": f"min_age ({min_age}) cannot be greater than max_age ({max_age})"}
    if min_age < 0 or max_age < 0:
        return {"error": "ages must be non-negative"}

    # Sample address components
    streets = ["Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Elm St", "Pine Rd", "Birch Blvd"]
    cities = ["Greenville", "Austin", "Seattle", "Boston", "San Diego", "Denver", "Charlotte"]
    states = ["SC", "TX", "WA", "MA", "CA", "CO", "NC"]

    users = []
    count = len(first_names)

    for i in range(count):
        first = first_names[i]
        last = last_names[i % len(last_names)]
        domain = domains[i % len(domains)]
        email = f"{first.lower()}.{last.lower()}@{domain}"

        address = {
            "street": f"{random.randint(100, 9999)} {random.choice(streets)}",
            "city": random.choice(cities),
            "state": random.choice(states),
            "zip": f"{random.randint(10000, 99999)}"
        }

        user = {
            "id": i + 1,
            "firstName": first,
            "lastName": last,
            "email": email,
            "username": f"{first.lower()}{random.randint(100, 999)}",
            "age": random.randint(min_age, max_age),
            "registeredAt": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "address": address
        }
        users.append(user)

    return {"users": users, "count": len(users)}


# -------- Create LlamaIndex Tools --------
write_json_tool = FunctionTool.from_defaults(fn=write_json)
write_xml_tool = FunctionTool.from_defaults(fn=write_xml)
read_json_tool = FunctionTool.from_defaults(fn=read_json)
generate_users_tool = FunctionTool.from_defaults(fn=generate_sample_users)

TOOLS = [write_json_tool, write_xml_tool, read_json_tool, generate_users_tool]

# -------- Initialize LLM and Agent --------
llm = OpenAI(model="gpt-4", temperature=0)

SYSTEM_PROMPT = (
    "You are DataGen, a helpful assistant that generates sample data for applications. "
    "You can generate user data in either JSON or XML format. "
    "To generate users, you need: first_names (list), last_names (list), domains (list), min_age, max_age. "
    "Fill in these values yourself without asking for them. "
    "Only save data to a file if the user explicitly asks to 'save' or 'write' to a file. "
    "If the user asks for XML, use the 'write_xml' tool. If the user asks for JSON, use 'write_json'. "
    "If the user just says 'show me the users', display them directly in the terminal. "
    "When saving, first generate users with the tool, then write them using the appropriate file format. "
    "If the user refers to 'those users' from a previous request, recall the latest generated data."
)

agent = ReActAgent.from_tools(
    tools=TOOLS,
    llm=llm,
    verbose=False,
)

# -------- Memory-Aware Chat --------
chat_history = []
last_generated_users = None


def run_agent(user_input: str) -> str:
    """Run the agent with memory of past interactions."""
    global chat_history, last_generated_users

    try:
        # Maintain chat history
        chat_history.append({"role": "user", "content": user_input})

        # If user says "save" or "write" and we have stored users, handle it directly
        if ("save" in user_input.lower() or "write" in user_input.lower()) and last_generated_users:
            if "xml" in user_input.lower():
                filepath = "users.xml"
                result = write_xml(filepath, last_generated_users)
            else:
                filepath = "users.json"
                result = write_json(filepath, last_generated_users)
            return result

        # Build conversation context
        conversation = SYSTEM_PROMPT + "\n\n"
        for msg in chat_history:
            conversation += f"{msg['role'].capitalize()}: {msg['content']}\n"

        response = agent.chat(conversation)

        # Store last generated users if response looks like JSON
        try:
            parsed = json.loads(str(response))
            if isinstance(parsed, dict) and "users" in parsed:
                last_generated_users = parsed
            return json.dumps(parsed, indent=2)
        except Exception:
            last_generated_users = None
            return str(response)

    except Exception as e:
        return f"Error: {str(e)}\n\nPlease try rephrasing your request or provide more specific details."


# -------- Interactive Console --------
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 DataGen Agent - Sample Data Generator")
    print("=" * 60)
    print("Generate sample user data and optionally save to JSON or XML files.")
    print()
    print("Examples:")
    print("  - Generate 5 users aged 25–35 with company.com emails")
    print("  - Save this as JSON")
    print("  - Save this as XML")
    print()
    print("Commands: 'quit' or 'exit' to end")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["quit", "exit", "q", ""]:
            print("👋 Goodbye!")
            break

        print("\nAgent: ", end="", flush=True)
        response = run_agent(user_input)
        print(response)

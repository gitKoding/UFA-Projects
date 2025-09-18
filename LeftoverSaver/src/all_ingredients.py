import openai
import json
import os

ai_client = openai
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
print(f"Data directory set to: {DATA_DIR}")
def read_file(filename):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def read_json(filename):
    content = read_file(filename)
    if content:
        try:
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
    return {}

def get_api_key():
    return read_file("api_key.txt") or ""


def get_ingredients():
    data = read_json("ingredients_data.json")
    return data.get("ingredients", [])


def load_model_settings():
    settings = read_json("settings.json")
    return (
        settings.get("ai_model", "gpt-3.5-turbo"),
        settings.get("recipes_count", 3),
        settings.get("max_tokens", 500),
        settings.get("temperature", 0.7)
    )


def get_recipes_from_ai(ingredients, prompt_text=None):
    model_name, recipes_count, max_tokens, temperature = load_model_settings()
    if not prompt_text:
        prompt_text = (
            f"Suggest {recipes_count} recipes I can make using only below listed ingredients. "
            "List each recipe with its name, ingredients, and steps."
        )
        print(f"\nUsing default prompt:\n{prompt_text}\n")
    print(f"\nUsing ingredients:\n{', '.join(ingredients)}\n")
    print(f"\nFetching recipe suggestions from AI Model - {model_name}...\n")
    prompt_text += f"Suggest from these ingredients only: {', '.join(ingredients)}"
    try:
        if model_name == "gpt-5":
            response = openai.responses.create(
                model=model_name,
                input=prompt_text
            )
            return getattr(response, "output_text", None)
        else:
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error fetching recipes from AI: {e}")
        return None


def run():
    ingredients = get_ingredients()
    if not ingredients:
        print("No ingredients found.")
        return
    openai_api_key = get_api_key()
    if not openai_api_key:
        print("Please set your OPENAI_API_KEY in data/api_key.txt.")
        return
    openai.api_key = openai_api_key
    user_prompt = input("Enter Leftover Saver prompt (or press Enter to use default): ").strip()
    recipes = get_recipes_from_ai(ingredients, user_prompt)
    print(recipes if recipes else "No recipes returned.")
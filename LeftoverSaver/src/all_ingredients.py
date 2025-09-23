import openai
import json
import os
import data.get_set_ing_data as ingredient_data
#import data.get_set_ing_data as update_ingredients
#import data.get_app_settings as get_ai_models
import data.get_app_settings as app_settings

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

def get_api_key():
    return read_file("api_key.txt") or ""


def fetch_ingredients():
    ingredients_data = ingredient_data.read_ingredients()
    return [
        {"ingredient_name": item.get("ingredient_name"), "quantity": item.get("quantity")}
        for item in ingredients_data
        if "ingredient_name" in item and "quantity" in item
    ]

def get_model_name():
    ai_models_list = app_settings.get_ai_models()
    if ai_models_list:
        return ai_models_list[0]
    # Default settings if none found
    return ("gpt-4")

def get_other_settings():
    settings = app_settings.get_other_settings()
    if len(settings) >= 3:
        try:
            #settings_dict = {item.split('=')[0].strip(): item.split('=')[1].strip() for item in settings if '=' in item}
            settings_dict = {}
            for item in settings:
                #if ':' in item:
                #    key, value = item.split(':', 1)
                settings_dict[item['name'].strip()] = item['value']
            recipes_count = int(settings_dict.get("recipes_count", 3))
            max_tokens = int(settings_dict.get("max_tokens", 500))
            temperature = float(settings_dict.get("temperature", 0.7))
            return (recipes_count, max_tokens, temperature)
        except ValueError:
            pass
    # Default values
    return (3, 500, 0.7)

def get_recipes_from_ai(ingredients, prompt_text=None):
    model_name = get_model_name()
    recipes_count, max_tokens, temperature = get_other_settings()  
    if not prompt_text:
        prompt_text = (
            f"Suggest {recipes_count} recipes I can make using only below listed ingredients. "
            "List each recipe with its name, ingredients, and steps."
        )
        print(f"\nUsing default prompt:\n{prompt_text}\n")
    print(f"\nIngredients available to use:\n{ingredients}\n")
    print(f"\nFetching recipe suggestions from AI Model - {model_name}...\n")
    prompt_text += f"Suggest from these ingredients and based on their quantities only:\n {ingredients}"
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
    ingredients = fetch_ingredients()
    ingredients_qty = [f"{item['ingredient_name']} - {item['quantity']}" for item in ingredients]
    ingredients_str = ", ".join(ingredients_qty)
    if not ingredients:
        print("No ingredients found.")
        return
    openai_api_key = get_api_key()
    if not openai_api_key:
        print("Please set your OPENAI_API_KEY in data/api_key.txt.")
        return
    openai.api_key = openai_api_key
    user_prompt = input("Enter Leftover Saver prompt (or press Enter to use default): ").strip()
    recipes = get_recipes_from_ai(ingredients_str, user_prompt)
    print(recipes if recipes else "No recipes returned.")
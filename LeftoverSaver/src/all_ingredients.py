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

def get_recipes_from_ai(ingredients, user_prompt_text=None):
    model_name = get_model_name()
    recipes_count, max_tokens, temperature = get_other_settings()
    def_prompt_txt = ""
    if not user_prompt_text:
        user_prompt_text = (
            f"Suggest {recipes_count} recipes I can make using only below listed ingredients. "
            "List each recipe with its name, ingredients, and steps."
        )
        def_prompt_txt = f"\nUsing default prompt:\n"
    model_details = f"Fetching recipe suggestions from AI Model - {model_name.upper()}..."
    print(def_prompt_txt + model_details)
    prompt_json_txt = "Your response should be a JSON format with a 'recipes' key containing a list of recipes. Each recipe should have 'name', 'ingredients', and 'steps' keys."

    user_prompt_text += f". Suggest from these ingredients and based on their quantities only:\n {ingredients}"
    final_prompt = user_prompt_text + ". " + prompt_json_txt
    display_prompt = def_prompt_txt + user_prompt_text
    try:
        if model_name == "gpt-5":
            response = openai.responses.create(
                model=model_name,
                input=final_prompt,
                response_format={"type": "json_object"}
            )
            return display_prompt, model_details, getattr(response, "output_text", None)
        else:
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": final_prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                #response_format={"type": "json_object"}
            )
            return display_prompt, model_details, response.choices[0].message.content
    except Exception as e:
        print(f"Error fetching recipes from AI: {e}")
        return None, None, None

def run(user_prompt=None):
    ingredients = fetch_ingredients()
    ingredients_qty = [f"{item['ingredient_name']} - {item['quantity']}" for item in ingredients]
    ingredients_str = ", ".join(ingredients_qty)
    if not ingredients:
        print("No ingredients found.")
        return "", "No ingredients found.", ""
    openai_api_key = get_api_key()
    if not openai_api_key:
        print("Please set your OPENAI_API_KEY in data/api_key.txt.")
        return user_prompt or "", "Missing API key.", ""
    openai.api_key = openai_api_key
    #user_prompt = input("Enter Leftover Saver prompt (or press Enter to use default): ").strip()
    user_prompt, model_details, recipes = get_recipes_from_ai(ingredients_str, user_prompt)
    return user_prompt or "", model_details or "", recipes or ""
    #print(recipes if recipes else "No recipes returned.")
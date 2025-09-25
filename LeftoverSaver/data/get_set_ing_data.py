import json
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ingredients_data.json')

# Read and return the ingredients data from the JSON file.
# Only include items with quantity > 0.
# Example return: [{'ingredient_name': 'Tomato', 'quantity': 3}, {'ingredient_name': 'Onion', 'quantity': 2}]
def read_ingredients():
    """Read and return the ingredients data from the JSON file, excluding items with quantity = 0."""
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            ingredients = data.get('ingredients', [])
            # Only include items with quantity > 0
            return [
                {
                    'ingredient_name': item.get('ingredient_name', ''),
                    'quantity': item.get('quantity', 0)
                }
                for item in ingredients
                if item.get('quantity', 0) > 0
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Update the ingredients data in the JSON file.
# If ingredient exists, update its quantity; if not, add it to the list.
# Expects a list of ingredient dicts.
# Example input: [{'ingredient_name': 'Tomato', 'quantity': 3}, {'ingredient_name': 'Onion', 'quantity': 2}]
def update_ingredients(new_ingredients):
	"""Update the ingredients data in the JSON file. Expects a list of ingredient dicts.
	If ingredient exists, update its quantity; if not, add it to the list."""
	try:
		with open(DATA_PATH, 'r', encoding='utf-8') as f:
			data = json.load(f)
			ingredients = data.get('ingredients', [])
	except (FileNotFoundError, json.JSONDecodeError):
		ingredients = []

	# Create a dict for fast lookup
	ing_dict = {item['ingredient_name']: item for item in ingredients if 'ingredient_name' in item}

	for new_item in new_ingredients:
		name = new_item.get('ingredient_name')
		quantity = new_item.get('quantity', 0)
		if name in ing_dict:
			ing_dict[name]['quantity'] += quantity
		else:
			ing_dict[name] = {'ingredient_name': name, 'quantity': quantity}

	# Write back as a list
	updated_list = list(ing_dict.values())
	with open(DATA_PATH, 'w', encoding='utf-8') as f:
		json.dump({"ingredients": updated_list}, f, ensure_ascii=False, indent=4)
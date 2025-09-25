from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.get_set_ing_data import update_ingredients, read_ingredients
import src.all_ingredients as all_ingredients

app = Flask(__name__)
@app.route('/recipes')
def recipes_page():
    return render_template('recipes.html')

@app.route('/get_recipes', methods=['POST'])
def get_recipes():
    data = request.get_json()
    prompt = data.get('prompt', None)
    prompt_text, model_details, result = all_ingredients.run(prompt)
    recipes = []
    if result:
        try:
            recipes = [r.replace('\n', '').strip() for r in result.split('\n\n') if r.strip()]
        except Exception:
            recipes = []
    return jsonify({
        'recipes': recipes,
        'final_prompt': prompt_text or "",
        'model_details': model_details or ""
    })

@app.route('/', methods=['GET', 'POST'])
def index():
    success_message = None
    if request.method == 'POST':
        ingredient = request.form.get('ingredient')
        quantity = request.form.get('quantity')
        if ingredient and quantity:
            update_data = {'ingredient_name': ingredient, 'quantity': int(quantity)}
            update_ingredients([update_data])
            success_message = f"Ingredient '{ingredient}' added successfully!"
        return redirect(url_for('index', success=success_message))
    success_message = request.args.get('success')
    return render_template('index.html', ingredients=read_ingredients(), success=success_message)

if __name__ == '__main__':
    app.run(debug=True)
import src.all_ingredients 

if __name__ == "__main__":
   prompt_text, other_details, result = src.all_ingredients.run()

   # If result is already a dict, use it directly; otherwise, call .json()
   if hasattr(result, "json"):
       data = result.json()
   else:
       data = result

   #if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list) and len(data["recipes"]) > 0:
       for r in data:
           name = r.get("name", "No name")
           ingredients = r.get("ingredients", [])
           steps = r.get("steps", [])
           print(name)
           print([i for i in ingredients])
           print([s for s in steps])
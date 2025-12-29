-- data/extra_recipes.sql
-- Tiny dataset of additional recipes, tags, and ingredients.
USE pantrywise;

-- New tags if missing
INSERT IGNORE INTO tags (name) VALUES ('vegan'), ('keto'), ('low-carb'), ('dessert'), ('salad');

-- New recipes (created_by = 1 for simplicity)
INSERT INTO recipes (title, description, steps_md, created_by) VALUES
('Caprese Salad', 'Tomato, mozzarella, basil', '1. Slice tomatoes\n2. Add mozzarella and basil\n3. Drizzle olive oil', 1),
('Garlic Butter Shrimp', 'Quick skillet shrimp', '1. Melt butter\n2. Add garlic\n3. Sear shrimp', 1),
('Overnight Oats', 'No-cook breakfast', '1. Mix oats + milk + chia\n2. Refrigerate overnight', 1),
('Avocado Toast', 'Simple breakfast/snack', '1. Toast bread\n2. Mash avocado\n3. Season and serve', 1),
('Tomato Soup', 'Comforting soup', '1. Saute onion + garlic\n2. Add tomatoes + stock\n3. Blend smooth', 1),
('Banana Pancakes', 'Fluffy pancakes', '1. Mix batter\n2. Cook on griddle\n3. Serve warm', 1)
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- Ingredients
INSERT INTO recipe_ingredients (recipe_id, ingredient_name, amount, unit) VALUES
((SELECT id FROM recipes WHERE title='Caprese Salad'), 'Tomato', 2, 'pcs'),
((SELECT id FROM recipes WHERE title='Caprese Salad'), 'Mozzarella', 150, 'g'),
((SELECT id FROM recipes WHERE title='Caprese Salad'), 'Basil', 10, 'leaf'),
((SELECT id FROM recipes WHERE title='Garlic Butter Shrimp'), 'Shrimp', 300, 'g'),
((SELECT id FROM recipes WHERE title='Garlic Butter Shrimp'), 'Garlic', 4, 'clove'),
((SELECT id FROM recipes WHERE title='Garlic Butter Shrimp'), 'Butter', 2, 'tbsp'),
((SELECT id FROM recipes WHERE title='Overnight Oats'), 'Oats', 60, 'g'),
((SELECT id FROM recipes WHERE title='Overnight Oats'), 'Milk', 200, 'ml'),
((SELECT id FROM recipes WHERE title='Overnight Oats'), 'Chia Seeds', 1, 'tbsp'),
((SELECT id FROM recipes WHERE title='Avocado Toast'), 'Bread', 2, 'slice'),
((SELECT id FROM recipes WHERE title='Avocado Toast'), 'Avocado', 1, 'pcs'),
((SELECT id FROM recipes WHERE title='Tomato Soup'), 'Tomato', 6, 'pcs'),
((SELECT id FROM recipes WHERE title='Tomato Soup'), 'Onion', 1, 'pcs'),
((SELECT id FROM recipes WHERE title='Tomato Soup'), 'Garlic', 3, 'clove'),
((SELECT id FROM recipes WHERE title='Banana Pancakes'), 'Banana', 2, 'pcs'),
((SELECT id FROM recipes WHERE title='Banana Pancakes'), 'Flour', 150, 'g'),
((SELECT id FROM recipes WHERE title='Banana Pancakes'), 'Milk', 200, 'ml');

-- Tags links
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='salad' WHERE r.title='Caprese Salad';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='quick' WHERE r.title='Garlic Butter Shrimp';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='breakfast' WHERE r.title='Overnight Oats';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='breakfast' WHERE r.title='Avocado Toast';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='dinner' WHERE r.title='Tomato Soup';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name='dessert' WHERE r.title='Banana Pancakes';

-- -----------------------------------------
-- PantryWise MySQL Schema with seed data (fixed)
-- -----------------------------------------

-- Recommended strictness (optional but good for catching issues)
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

-- create database if not exists and use it
CREATE DATABASE IF NOT EXISTS pantrywise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pantrywise;

-- users table to store accounts
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- recipes table stores base recipes
CREATE TABLE IF NOT EXISTS recipes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  steps_md MEDIUMTEXT NULL,
  created_by INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_recipes_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- tags dictionary
CREATE TABLE IF NOT EXISTS tags (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- junction between recipes and tags
CREATE TABLE IF NOT EXISTS recipe_tags (
  recipe_id INT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (recipe_id, tag_id),
  CONSTRAINT fk_rt_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  CONSTRAINT fk_rt_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- recipe ingredients table normalized
CREATE TABLE IF NOT EXISTS recipe_ingredients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  ingredient_name VARCHAR(100) NOT NULL,
  amount DECIMAL(10,2) DEFAULT 0,
  unit VARCHAR(20) NULL,
  INDEX idx_ri_name (ingredient_name),
  CONSTRAINT fk_ri_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- pantry items owned by users
CREATE TABLE IF NOT EXISTS pantry_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  item_name VARCHAR(100) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  unit VARCHAR(20) NULL,
  expires_on DATE NULL,
  INDEX idx_pantry_exp (expires_on),
  INDEX idx_pantry_user_item (user_id, item_name),
  CONSTRAINT fk_pantry_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- shopping list per user
CREATE TABLE IF NOT EXISTS shopping_list (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  item_name VARCHAR(100) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  unit VARCHAR(20) NULL,
  done TINYINT(1) NOT NULL DEFAULT 0,
  INDEX idx_shop_done (done),
  CONSTRAINT fk_shop_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- favourites per user
CREATE TABLE IF NOT EXISTS favourites (
  user_id INT NOT NULL,
  recipe_id INT NOT NULL,
  PRIMARY KEY (user_id, recipe_id),
  CONSTRAINT fk_fav_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_fav_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- usage history
CREATE TABLE IF NOT EXISTS history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  recipe_id INT NOT NULL,
  used_at DATETIME NOT NULL,
  INDEX idx_hist_user_time (user_id, used_at),
  CONSTRAINT fk_hist_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_hist_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- optional unit conversion (basic factors to a base unit per family)
CREATE TABLE IF NOT EXISTS unit_conversion (
  id INT AUTO_INCREMENT PRIMARY KEY,
  family VARCHAR(50) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  to_base_factor DECIMAL(18,6) NOT NULL,
  UNIQUE KEY uniq_family_unit (family, unit)
) ENGINE=InnoDB;

-- ----------------
-- seed data (idempotent)
-- ----------------

-- Users (use MySQL 8+ row alias for ON DUPLICATE)
INSERT INTO users (name, email, password_hash)
VALUES
  ('Alice', 'alice@example.com', 'pbkdf2:sha256:600000$seed$alicehash'),
  ('Bob',   'bob@example.com',   'pbkdf2:sha256:600000$seed$bobhash')
AS new
ON DUPLICATE KEY UPDATE
  name = new.name,
  password_hash = new.password_hash;

-- Tags
INSERT IGNORE INTO tags (name) VALUES
('vegetarian'), ('high-protein'), ('breakfast'), ('dinner'), ('quick'), ('gluten-free');

-- Recipes (link to users by email; avoids assuming user IDs)
INSERT INTO recipes (title, description, steps_md, created_by)
SELECT * FROM (
  SELECT 'Veggie Omelette' AS title, 'Quick breakfast eggs with veggies' AS description,
         '1. Beat eggs\n2. Saute veggies\n3. Cook and fold' AS steps_md,
         (SELECT id FROM users WHERE email='alice@example.com') AS created_by
  UNION ALL
  SELECT 'Pasta Arrabbiata', 'Spicy tomato pasta',
         '1. Boil pasta\n2. Make sauce\n3. Toss together',
         (SELECT id FROM users WHERE email='alice@example.com')
  UNION ALL
  SELECT 'Chicken Stir Fry', 'Lean protein with veggies',
         '1. Prep chicken\n2. Stir fry with sauce\n3. Serve with rice',
         (SELECT id FROM users WHERE email='bob@example.com')
  UNION ALL
  SELECT 'Peanut Butter Smoothie', 'Protein smoothie',
         '1. Blend milk + PB + banana\n2. Serve cold',
         (SELECT id FROM users WHERE email='bob@example.com')
) AS seed
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  steps_md = VALUES(steps_md),
  created_by = VALUES(created_by);

-- Recipe ingredients (resolve recipe_id by title to avoid hard-coded IDs)
INSERT INTO recipe_ingredients (recipe_id, ingredient_name, amount, unit)
SELECT r.id, x.ingredient_name, x.amount, x.unit
FROM (
  SELECT 'Veggie Omelette' AS title, 'Eggs' AS ingredient_name, 3 AS amount, 'pcs' AS unit
  UNION ALL SELECT 'Veggie Omelette','Onion',0.25,'pcs'
  UNION ALL SELECT 'Veggie Omelette','Bell Pepper',0.25,'pcs'
  UNION ALL SELECT 'Pasta Arrabbiata','Pasta',200,'g'
  UNION ALL SELECT 'Pasta Arrabbiata','Tomato',3,'pcs'
  UNION ALL SELECT 'Pasta Arrabbiata','Garlic',3,'clove'
  UNION ALL SELECT 'Chicken Stir Fry','Chicken Breast',300,'g'
  UNION ALL SELECT 'Chicken Stir Fry','Soy Sauce',2,'tbsp'
  UNION ALL SELECT 'Chicken Stir Fry','Bell Pepper',1,'pcs'
  UNION ALL SELECT 'Peanut Butter Smoothie','Peanut Butter',2,'tbsp'
  UNION ALL SELECT 'Peanut Butter Smoothie','Milk',250,'ml'
  UNION ALL SELECT 'Peanut Butter Smoothie','Banana',1,'pcs'
) x
JOIN recipes r ON r.title = x.title
-- ignore duplicates if this seed re-runs
ON DUPLICATE KEY UPDATE ingredient_name = VALUES(ingredient_name);

-- Recipe tags (already title-based; keep as-is)
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name IN ('breakfast','quick') WHERE r.title='Veggie Omelette';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name IN ('dinner') WHERE r.title='Pasta Arrabbiata';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name IN ('high-protein','dinner') WHERE r.title='Chicken Stir Fry';
INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
SELECT r.id, t.id FROM recipes r JOIN tags t ON t.name IN ('breakfast','high-protein','quick') WHERE r.title='Peanut Butter Smoothie';

-- Pantry for Alice (resolve user_id by email; avoid assuming id=1)
INSERT INTO pantry_items (user_id, item_name, quantity, unit, expires_on)
SELECT u.id, x.item_name, x.quantity, x.unit, x.expires_on
FROM (
  SELECT 'Eggs' AS item_name, 6 AS quantity, 'pcs' AS unit, DATE_ADD(CURDATE(), INTERVAL 3 DAY) AS expires_on
  UNION ALL SELECT 'Onion',2,'pcs',DATE_ADD(CURDATE(), INTERVAL 2 DAY)
  UNION ALL SELECT 'Bell Pepper',1,'pcs',DATE_ADD(CURDATE(), INTERVAL 4 DAY)
  UNION ALL SELECT 'Pasta',500,'g',NULL
  UNION ALL SELECT 'Tomato',2,'pcs',DATE_ADD(CURDATE(), INTERVAL 1 DAY)
  UNION ALL SELECT 'Garlic',5,'clove',NULL
  UNION ALL SELECT 'Milk',1000,'ml',DATE_ADD(CURDATE(), INTERVAL 5 DAY)
) x
JOIN users u ON u.email='alice@example.com';

-- Unit conversion (idempotent)
INSERT IGNORE INTO unit_conversion (family, unit, to_base_factor) VALUES
('volume','ml',1.0), ('volume','tsp',5.0), ('volume','tbsp',15.0), ('volume','cup',240.0),
('weight','g',1.0), ('weight','kg',1000.0), ('weight','lb',453.592), ('weight','oz',28.3495);

-- Substitutions
CREATE TABLE IF NOT EXISTS substitutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL,
    substitute_name VARCHAR(255) NOT NULL,
    ratio VARCHAR(50) DEFAULT '1:1',
    note TEXT,
    UNIQUE KEY unique_sub (ingredient_name, substitute_name)
);

INSERT IGNORE INTO substitutions (ingredient_name, substitute_name, ratio, note) VALUES
('Butter', 'Margarine', '1:1', 'Direct swap'),
('Butter', 'Oil', '1:0.75', 'Use 3/4 cup oil for 1 cup butter'),
('Milk', 'Yogurt', '1:1', 'Thinned with water if needed'),
('Milk', 'Water', '1:1', 'Add a little butter for richness'),
('Cream', 'Milk', '1:1', 'Add butter'),
('Egg', 'Banana', '1:0.5', '1/2 mashed banana per egg (baking)'),
('Egg', 'Applesauce', '1:0.25', '1/4 cup per egg'),
('Lemon Juice', 'Vinegar', '1:0.5', 'Use half amount'),
('Sugar', 'Honey', '1:0.75', 'Reduce liquid in recipe'),
('Breadcrumbs', 'Oats', '1:1', 'Pulse in blender'),
('Sour Cream', 'Yogurt', '1:1', 'Greek yogurt works best');


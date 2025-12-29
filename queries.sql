
-- 1. Search by title/ingredient/tag ('Pasta')
SELECT DISTINCT r.id, r.title
FROM recipes r
LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
LEFT JOIN recipe_tags rt ON rt.recipe_id = r.id
LEFT JOIN tags t ON t.id = rt.tag_id
WHERE r.title LIKE '%Pasta%'
   OR ri.ingredient_name LIKE '%Pasta%'
   OR t.name LIKE '%Pasta%'
ORDER BY r.title;

-- 2. Recipes with their tags (include untagged)
SELECT r.title, GROUP_CONCAT(t.name ORDER BY t.name) AS tags
FROM recipes r
LEFT JOIN recipe_tags rt ON rt.recipe_id = r.id
LEFT JOIN tags t ON t.id = rt.tag_id
GROUP BY r.id, r.title
ORDER BY r.title;

-- 3. Count ingredients per recipe 
SELECT r.title, COUNT(ri.id) AS ingredient_count
FROM recipes r
LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
GROUP BY r.id, r.title
ORDER BY ingredient_count DESC, r.title ASC;

-- 4. Recipes having at least 3 ingredients
SELECT r.title, COUNT(ri.id) AS ingredient_count
FROM recipes r
JOIN recipe_ingredients ri ON ri.recipe_id = r.id
GROUP BY r.id, r.title
HAVING COUNT(ri.id) >= 3;

-- 5. Alice’s items expiring in next 5 days
SELECT item_name, quantity, unit, expires_on
FROM pantry_items
WHERE user_id = (SELECT id FROM users WHERE email='alice@example.com')
  AND expires_on IS NOT NULL
  AND expires_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 5 DAY)
ORDER BY expires_on;

-- 6. Pantry totals per item/unit (Alice)
SELECT item_name, unit, SUM(quantity) AS qty
FROM pantry_items
WHERE user_id = (SELECT id FROM users WHERE email='alice@example.com')
GROUP BY item_name, unit
ORDER BY item_name;

-- 7. Missing ingredients for recipe Pasta Arrabbiata vs Alice’s pantry
SELECT
  ri.ingredient_name,
  GREATEST(ri.amount - IFNULL(p.qty,0), 0) AS missing_amount,
  ri.unit
FROM recipe_ingredients ri
LEFT JOIN (
  SELECT item_name, unit, SUM(quantity) AS qty
  FROM pantry_items
  WHERE user_id = (SELECT id FROM users WHERE email='alice@example.com')
  GROUP BY item_name, unit
) p
  ON p.item_name = ri.ingredient_name
 AND (p.unit <=> ri.unit)
WHERE ri.recipe_id = (SELECT id FROM recipes WHERE title='Pasta Arrabbiata')
ORDER BY ri.ingredient_name;

-- 8. Alice’s favourites
SELECT r.id, r.title
FROM favourites f
JOIN recipes r ON r.id = f.recipe_id
WHERE f.user_id = (SELECT id FROM users WHERE email='alice@example.com')
ORDER BY r.title;

-- 9. Alice’s history in last 30 days
SELECT r.title, h.used_at
FROM history h
JOIN recipes r ON r.id = h.recipe_id
WHERE h.user_id = (SELECT id FROM users WHERE email='alice@example.com')
  AND h.used_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY h.used_at DESC;

-- 10. Weekly meal plan: fewest missing first (Alice)
SELECT
  r.id,
  r.title,
  SUM( (GREATEST(ri.amount - IFNULL(p.qty,0), 0) > 0) ) AS missing_count
FROM recipes r
JOIN recipe_ingredients ri ON ri.recipe_id = r.id
LEFT JOIN (
  SELECT item_name, unit, SUM(quantity) AS qty
  FROM pantry_items
  WHERE user_id = (SELECT id FROM users WHERE email='alice@example.com')
  GROUP BY item_name, unit
) p
  ON p.item_name = ri.ingredient_name
 AND (p.unit <=> ri.unit)
GROUP BY r.id, r.title
ORDER BY missing_count ASC, r.title ASC
LIMIT 7;


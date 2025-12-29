# PantryWise

A web app that helps you manage your pantry, find recipes based on what you have, and automatically build shopping lists. Built with Flask and MySQL.

## Why I Built This

I got tired of forgetting what's in my pantry and letting food expire. This app tracks your ingredients, shows you recipes you can make with what you have, and helps plan meals around expiring items. It also generates shopping lists automatically when you find a recipe you want to make but are missing ingredients.

## Main Features

**Pantry Management**
- Track what you have, how much, and when it expires
- Get alerts for items expiring in the next 5 days
- Add, edit, or remove items easily

**Smart Recipe Search**
- Search by title, ingredient, or tags
- See which ingredients you have vs. what's missing
- Get recipe recommendations ranked by how many ingredients you already have
- One-click to add missing ingredients to your shopping list

**Shopping List**
- Auto-generated from recipes you want to make
- Mark items as purchased
- Move purchased items directly to your pantry

**Meal Planning**
- Weekly meal planner suggests recipes based on what you have
- Prioritizes recipes that use expiring ingredients
- Uses a greedy algorithm to minimize shopping needs

**Extras**
- Save favorite recipes
- Track recipe history (when you last made something)
- AI recipe generation using Google Gemini (optional)

## Getting Started

**Requirements:**
- Python 3.8+
- MySQL 8.0+
- Google Gemini API key (optional, only for AI features)

**Installation:**

```bash
# Clone and navigate
git clone https://github.com/ParjanyaReddy/PantryWise.git
cd PantryWise

# Set up virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up database
mysql -u root -p
CREATE DATABASE pantrywise;
USE pantrywise;
SOURCE schema.sql;
exit;

# Configure environment
# Copy .env.example to .env and fill in your details:
# - Database credentials
# - Flask secret key
# - Gemini API key (optional)

# Run the app
python app.py
```

Open `http://localhost:5000` and create an account to get started.

## How It Works

The app uses Flask for the backend and MySQL for data storage. Each user has their own pantry, shopping list, and favorites. When you search for recipes, it compares the recipe ingredients against your pantry to show you what you have and what you're missing.

**Recipe Matching:**
- Fetches your pantry ingredients
- For each recipe, calculates how many ingredients you have
- Ranks recipes by match percentage
- Shows "Have" vs "Missing" for each recipe

**Shopping List Intelligence:**
- Aggregates duplicate ingredients
- Tracks purchase status
- Merges quantities when moving to pantry

## Tech Stack

**Backend:**
- Flask 3.0 - web framework
- MySQL - database
- Werkzeug - password hashing
- Google Gemini API - AI recipe generation

**Frontend:**
- HTML/CSS with Jinja2 templates
- Vanilla JavaScript for interactions
- Custom CSS with animations

## Project Structure

```
PantryWise/
├── app.py              # Main Flask app and routes
├── db.py               # Database connection and queries
├── schema.sql          # Database schema
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── templates/          # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── pantry.html
│   ├── recipes.html
│   └── ...
└── static/
    └── styles.css      # Custom styling
```

## Database Schema

Core tables:
- `users` - authentication and profiles
- `ingredients` - master ingredient list
- `recipes` - recipe details
- `recipe_ingredients` - links recipes to ingredients
- `pantry_items` - user's inventory
- `shopping_list` - per-user shopping items
- `favourites` - saved recipes
- `recipe_history` - usage tracking

All queries use parameterized statements to prevent SQL injection.

## What I Learned

Building this taught me:
- Designing a relational database schema with proper foreign keys
- Implementing user authentication and session management
- Working with many-to-many relationships (recipes ↔ ingredients)
- Building a recommendation system based on user data
- Integrating third-party APIs (Google Gemini)

## Known Issues

- Meal planner uses a greedy algorithm (not globally optimal)
- Unit conversion table exists but isn't fully integrated yet
- AI features require an API key

## Future Improvements

Things I'd like to add:
- Barcode scanning for adding pantry items
- Nutritional information tracking
- Recipe ratings and reviews
- Better meal planning algorithm
- Mobile app version

## Security Notes

- Passwords are hashed with Werkzeug
- All database queries use parameterized statements
- `.env` file keeps sensitive data out of version control
- Session-based authentication

## License

MIT License - use this however you want for learning or your own projects.

---

Built as a learning project to practice full-stack development with Flask and MySQL.

# 🍳 PantryWise — Smart Recipe & Pantry Manager

A **full-stack web application** built with Flask and MySQL to intelligently manage your pantry inventory, discover recipes based on available ingredients, auto-generate shopping lists, and plan weekly meals with AI assistance.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 🔐 **User Authentication**
- Secure registration and login system
- Password hashing with Werkzeug
- Session-based authentication
- Per-user data isolation

### 🥫 **Smart Pantry Management**
- Add, edit, and delete pantry items
- Track quantity, unit, and expiration dates
- **Expiry Alerts** - Get notified of items expiring within 5 days
- Visual inventory tracking

### 🔍 **Intelligent Recipe Search**
- Search by title, ingredients, or tags
- **Ingredient Matching** - See which ingredients you have vs. missing
- **One-Click Shopping** - Add missing ingredients to shopping list instantly
- Recipe recommendations ranked by ingredient match percentage

### 🛒 **Auto-Generated Shopping Lists**
- Per-user shopping lists
- Mark items as done/purchased
- **Smart Pantry Integration** - Move purchased items to pantry automatically
- Quantity aggregation for duplicate items

### ⭐ **Personalization**
- **Favorites** - Save your go-to recipes
- **Recipe History** - Track when you used each recipe
- **AI Recipe Generation** - Create custom recipes with Google Gemini AI

### 📅 **Meal Planning**
- **Weekly Meal Planner** - Greedy algorithm suggests 5-7 recipes
- Optimizes for fewest missing ingredients
- Reduces food waste by prioritizing expiring items

### 🎨 **Modern UI/UX**
- Responsive design with smooth animations
- Glassmorphism effects and gradient backgrounds
- Micro-animations for enhanced user experience
- Premium, professional aesthetic

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)
- Google Gemini API key (optional, for AI features)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PantryWise.git
   cd PantryWise
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   ```bash
   # Log into MySQL
   mysql -u root -p
   
   # Create database
   CREATE DATABASE pantrywise;
   USE pantrywise;
   
   # Import schema
   SOURCE schema.sql;
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your credentials
   # DB_HOST=localhost
   # DB_USER=your_mysql_username
   # DB_PASSWORD=your_mysql_password
   # DB_NAME=pantrywise
   # SECRET_KEY=your-secret-key
   # GEMINI_API_KEY=your-api-key (optional)
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the app**
   - Open your browser and navigate to `http://localhost:5000`
   - Register a new account and start managing your pantry!

---

## 📁 Project Structure

```
PantryWise/
├── app.py                   # Main Flask application & routes
├── db.py                    # Database connection & query functions
├── requirements.txt         # Python dependencies
├── schema.sql               # MySQL database schema
├── queries.sql              # Sample SQL queries
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── README.md                # This file
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template with navbar
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── home.html           # Dashboard with expiry alerts
│   ├── pantry.html         # Pantry inventory management
│   ├── recipes.html        # Recipe search & browse
│   ├── recipe_detail.html  # Individual recipe view
│   ├── shopping.html       # Shopping list
│   ├── favourites.html     # Saved favorite recipes
│   ├── history.html        # Recipe usage history
│   ├── add_recipe.html     # Add new recipe form
│   └── meal_plan.html      # Weekly meal planner
│
├── static/                  # Static assets
│   └── styles.css          # Custom CSS with animations
│
└── data/                    # Data files (gitignored)
    └── recipes.json        # Sample recipe data
```

---

## 🛠️ Tech Stack

### Backend
- **Flask 3.0.0** - Lightweight Python web framework
- **MySQL 8.0+** - Relational database
- **mysql-connector-python** - Official MySQL driver
- **Werkzeug** - Password hashing & security utilities
- **python-dotenv** - Environment variable management

### Frontend
- **HTML5 & CSS3** - Semantic markup & modern styling
- **Jinja2** - Server-side templating
- **Vanilla JavaScript** - Interactive elements
- **Google Fonts** - Custom typography

### AI Integration
- **Google Gemini API** - AI-powered recipe generation
- **Markdown** - Safe rendering of AI-generated content

---

## 🎯 Key Functionalities

### Pantry Management
```python
# Add item to pantry
INSERT INTO pantry_items (user_id, ingredient_id, quantity, unit, expires_on)
VALUES (?, ?, ?, ?, ?)

# Check expiring items (≤ 5 days)
SELECT * FROM pantry_items 
WHERE user_id = ? AND expires_on <= DATE_ADD(CURDATE(), INTERVAL 5 DAY)
```

### Recipe Matching Algorithm
1. Fetch user's pantry ingredients
2. For each recipe, calculate:
   - **Have**: Ingredients in pantry
   - **Missing**: Ingredients not in pantry
   - **Match %**: (Have / Total) × 100
3. Rank recipes by match percentage

### Shopping List Intelligence
- Aggregates duplicate ingredients
- Tracks purchase status
- One-click transfer to pantry with quantity merging

---

## 📊 Database Schema Highlights

### Core Tables
- `users` - User authentication & profiles
- `ingredients` - Master ingredient list
- `recipes` - Recipe metadata (title, instructions, tags)
- `recipe_ingredients` - Many-to-many recipe-ingredient mapping
- `pantry_items` - User inventory with expiration tracking
- `shopping_list` - Per-user shopping items
- `favourites` - User-recipe favorites
- `recipe_history` - Usage timestamps

### Advanced Features
- `unit_conversions` - Future-proof unit harmonization
- Parameterized queries for SQL injection prevention
- Foreign key constraints for data integrity

---

## 🎨 UI/UX Highlights

- **Glassmorphism Cards** - Frosted glass effect with backdrop blur
- **Gradient Backgrounds** - Dynamic color schemes
- **Micro-Animations** - Smooth hover effects and transitions
- **Responsive Design** - Mobile-friendly layouts
- **Accessibility** - Semantic HTML and ARIA labels

---

## 🔒 Security Features

- ✅ Password hashing with Werkzeug's `generate_password_hash`
- ✅ Parameterized SQL queries (no SQL injection)
- ✅ Session-based authentication
- ✅ Environment variable protection (`.env`)
- ✅ CSRF protection ready (can integrate Flask-WTF)

---

## 📈 Future Enhancements

- [ ] Nutritional information tracking
- [ ] Barcode scanning for pantry items
- [ ] Recipe rating and reviews
- [ ] Social sharing features
- [ ] Mobile app (React Native)
- [ ] Advanced meal planning with calorie tracking
- [ ] Integration with grocery delivery APIs

---

## 🐛 Known Issues

- Meal planner uses greedy algorithm (not globally optimal)
- Unit conversion table implemented but not fully integrated
- AI recipe generation requires API key

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)
- Portfolio: [yourwebsite.com](https://yourwebsite.com)

---

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Database powered by [MySQL](https://www.mysql.com/)
- AI features by [Google Gemini](https://ai.google.dev/)
- Icons from [Font Awesome](https://fontawesome.com/)

---

## 📸 Screenshots

*Add screenshots of your application here!*

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Recipe Search
![Recipe Search](screenshots/recipes.png)

### Pantry Management
![Pantry](screenshots/pantry.png)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/PantryWise/issues).

---

**⭐ If you found this project helpful, please consider giving it a star!**


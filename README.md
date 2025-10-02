# 📚 Academic Resource Integration Portal

A Flask-based web application for managing and discovering academic resources including books, videos, and research papers.
This portal is designed to provide students, researchers, and educators with a centralized hub for accessing and organizing learning materials.

## 🚀 Features

- **Resource Management** – Add, store, and organize academic resources with metadata.
- **Search & Discovery** – Browse resources by type, tags, and keywords (search integration with Whoosh planned).
- **Admin Interface** – Secure admin dashboard for uploading and managing resources (under development).
- **Responsive Design** – Modern, mobile-friendly UI powered by Bootstrap 5.

## 📂 Project Structure

```
IR Project/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy database models
├── requirements.txt    # Python dependencies
├── whoosh_index.py     # Placeholder for search functionality
├── templates/          # Jinja2 templates
│   ├── base.html       # Base template with navigation
│   ├── home.html       # Homepage
│   ├── admin.html      # Admin upload page
│   └── resources.html  # Resources listing page
└── static/             # CSS, JS, and image assets
```

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Shru2653/Academic-Resource-Integration-Portal.git
cd "IR Project"
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

### 5. Access in Browser
Open: http://localhost:5000

## 🗄️ Database Schema

### Resource Model
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| title | String | Resource title (required) |
| description | Text | Detailed description (required) |
| type | String | Resource type: Book, Video, or Paper |
| tags | String | Comma-separated tags |
| image_url | String | Optional image/thumbnail URL |
| link | String | URL to the actual resource (required) |

## 🌐 Routes

- `/` → Homepage with welcome message & feature overview
- `/resources` → Browse all resources with search & filtering (coming soon)
- `/admin` → Admin panel for uploading/managing resources (restricted access)

## 🛠️ Technologies Used

- **Backend**: Flask (Python), SQLAlchemy ORM
- **Database**: SQLite (default), PostgreSQL (recommended for production)
- **Frontend**: Bootstrap 5, Font Awesome, Jinja2
- **Search**: Whoosh (planned integration)

## 🔮 Future Enhancements

- Resource upload functionality with image auto-fetch
- Full-text search & filtering with Whoosh
- Authentication & role-based authorization
- Resource categories & tagging system
- File upload support (PDFs, Docs)
- Rating & review system
- REST API endpoints for external integrations

## 👨‍💻 Development Notes

- Currently runs in debug mode (`debug=True` in app.py)
- For production:
  - Set `debug=False`
  - Use a WSGI server like Gunicorn or uWSGI
  - Switch to PostgreSQL or MySQL for scalability
  - Configure environment variables for sensitive settings

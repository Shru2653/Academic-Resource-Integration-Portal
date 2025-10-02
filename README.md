# Academic Resource Integration Portal

A Flask-based web application for managing and discovering academic resources including books, videos, and research papers.

## Features

- **Resource Management**: Store and organize academic resources with detailed metadata
- **Search & Discovery**: Browse resources by type, tags, and keywords (coming soon)
- **Admin Interface**: Upload and manage resources through a web interface (coming soon)
- **Responsive Design**: Modern, mobile-friendly interface using Bootstrap

## Project Structure

```
IR Project/
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── whoosh_index.py       # Search functionality (placeholder)
├── templates/            # Jinja2 templates
│   ├── base.html         # Base template with navigation
│   ├── home.html         # Homepage
│   ├── admin.html        # Admin upload page
│   └── resources.html    # Resources listing page
└── static/               # CSS, JS, and image files (empty)
```

## Installation

1. **Clone or download the project**
   ```bash
   cd "d:\IR Project"
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Database Schema

### Resource Model
- `id`: Primary key (Integer)
- `title`: Resource title (String, required)
- `description`: Detailed description (Text, required)
- `type`: Resource type - Book, Video, or Paper (String, required)
- `tags`: Comma-separated tags (String)
- `image_url`: URL to resource image (String, optional)
- `link`: URL to the actual resource (String, required)

## Routes

- `/` - Homepage with welcome message and feature overview
- `/admin` - Admin interface for uploading resources (placeholder)
- `/resources` - Browse all resources with search and filtering (placeholder)

## Technologies Used

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Database
- **Bootstrap 5**: CSS framework
- **Font Awesome**: Icons
- **Jinja2**: Template engine

## Future Enhancements

- [ ] Implement resource upload functionality
- [ ] Add search and filtering capabilities using Whoosh
- [ ] User authentication and authorization
- [ ] Resource categories and advanced tagging
- [ ] File upload support for PDFs and documents
- [ ] Resource rating and review system
- [ ] API endpoints for programmatic access

## Development

The application is currently in development mode with debug enabled. For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server like Gunicorn
3. Configure a production database (PostgreSQL recommended)
4. Set up proper environment variables for sensitive configuration

## License

This project is open source and available under the MIT License.

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import tfidf_index

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///academic_portal.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize database
from models import db, Resource
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ======================
# DATABASE MODEL
# ======================
# Admin model for authentication
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ======================
# HELPER FUNCTIONS
# ======================
def fetch_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    books = []

    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            volume = item.get("volumeInfo", {})
            # Use book-specific placeholder if no image available
            image_url = volume.get("imageLinks", {}).get("thumbnail")
            if not image_url:
                image_url = None  # Will use placeholder in template
            
            books.append({
                "title": volume.get("title", "Untitled"),
                "description": volume.get("description", "No description available."),
                "type": "Book",
                "link": volume.get("infoLink", "#"),
                "image_url": image_url,
                "tags": ", ".join(volume.get("categories", [])) if "categories" in volume else "book"
            })
    return books


def fetch_papers(query):
    url = f"https://api.crossref.org/works?query={query}&rows=5"
    response = requests.get(url, headers={"User-Agent": "AcademicPortal/1.0 (mailto:youremail@example.com)"})
    papers = []

    if response.status_code == 200:
        data = response.json()
        for item in data.get("message", {}).get("items", []):
            papers.append({
                "title": item.get("title", ["Untitled"])[0],
                "description": item.get("abstract", "No abstract available."),
                "type": "Paper",
                "link": item.get("URL", "#"),
                "image_url": None,  # Will use research paper placeholder in template
                "tags": ", ".join(item.get("subject", [])) if "subject" in item else "research"
            })
    return papers


def fetch_videos(query):
    api_key = os.getenv("YOUTUBE_API_KEY")
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=6&key={api_key}"
    response = requests.get(url)
    videos = []

    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
            videos.append({
                "title": snippet["title"],
                "description": snippet["description"],
                "type": "Video",
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "image_url": snippet["thumbnails"]["high"]["url"],
                "tags": "YouTube, video"
            })
    return videos


# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/resources")
def resources():
    # Handle search and filtering
    search_query = request.args.get('q', '').strip()
    filter_type = request.args.get('type', '')
    
    # Get counts for filter buttons (from database, not search results)
    book_count = Resource.query.filter_by(type='Book').count()
    video_count = Resource.query.filter_by(type='Video').count()
    paper_count = Resource.query.filter_by(type='Paper').count()
    total_count = Resource.query.count()
    
    if search_query:
        # First, try to fetch new resources from APIs
        try:
            books = fetch_books(search_query)
            papers = fetch_papers(search_query)
            videos = fetch_videos(search_query)
            
            all_new_resources = books + papers + videos
            new_count = 0
            
            # Save new resources to database if not already present
            for item in all_new_resources:
                existing = Resource.query.filter_by(title=item["title"]).first()
                if not existing:
                    new_res = Resource(**item)
                    db.session.add(new_res)
                    new_count += 1
            
            if new_count > 0:
                db.session.commit()
                flash(f"Found {new_count} new resources for '{search_query}'!", "success")
            
        except Exception as e:
            current_app.logger.error(f"API fetch error: {e}")
            flash("Note: Could not fetch new resources from APIs, showing existing results only.", "warning")
        
        # Now perform TF-IDF search on all resources (including newly added ones)
        tfidf_index.build_index(Resource.query.all())
        results = tfidf_index.search_index(search_query, type_filter=filter_type if filter_type in ['Book', 'Video', 'Paper'] else None)
        
        # Add score attribute to each resource for template display
        resources_for_template = []
        for resource, score in results:
            resource.score = score
            resources_for_template.append(resource)
            
        current_app.logger.info(f"Search q={search_query!r} with filter={filter_type} returned {len(results)} results. Index size: {tfidf_index.index_size()}")
        
        # Update counts after potential new additions
        book_count = Resource.query.filter_by(type='Book').count()
        video_count = Resource.query.filter_by(type='Video').count()
        paper_count = Resource.query.filter_by(type='Paper').count()
        total_count = Resource.query.count()
        
        return render_template('resources.html', 
                             resources=resources_for_template, 
                             search_query=search_query,
                             filter_type=filter_type,
                             book_count=book_count,
                             video_count=video_count,
                             paper_count=paper_count,
                             total_count=total_count,
                             is_search=True,
                             search_results_count=len(resources_for_template))
    else:
        # No search query - just apply filter if present
        if filter_type and filter_type in ['Book', 'Video', 'Paper']:
            filtered_resources = Resource.query.filter_by(type=filter_type).all()
        else:
            filtered_resources = Resource.query.all()
            
        return render_template('resources.html', 
                             resources=filtered_resources,
                             search_query=search_query,
                             filter_type=filter_type,
                             book_count=book_count,
                             video_count=video_count,
                             paper_count=paper_count,
                             total_count=total_count,
                             is_search=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("resources"))

@app.route("/admin")
@login_required
def admin_panel():
    resources = Resource.query.all()
    return render_template("admin.html", resources=resources)

@app.route('/search')
def search():
    """Redirect search requests to resources route for unified handling"""
    # Redirect to resources route with the same parameters
    return redirect(url_for('resources', **request.args))


# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # Clean up existing resources with invalid image URLs
        try:
            resources_to_update = Resource.query.all()
            updated_count = 0
            for resource in resources_to_update:
                if (resource.image_url and 
                    (resource.image_url.strip() == '' or 
                     resource.image_url == 'None' or 
                     resource.image_url.startswith('https://via.placeholder.com') or
                     resource.image_url.startswith('/static/images/placeholder'))):
                    resource.image_url = None
                    updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                print(f"Cleaned up {updated_count} resources with invalid image URLs.")
        except Exception as e:
            print(f"Warning: Could not clean up image URLs: {e}")
        
        # Initialize TF-IDF index with existing resources
        try:
            all_resources = Resource.query.all()
            tfidf_index.build_index(all_resources)
            print(f"TF-IDF index initialized with {tfidf_index.index_size()} resources.")
        except Exception as e:
            print(f"Warning: Could not initialize TF-IDF index: {e}")
            
    app.run(debug=True)

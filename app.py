from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, URLField, SubmitField
from wtforms.validators import DataRequired, URL, Optional
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import tfidf_index
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin
import re

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///academic_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize database
from models import db, Resource
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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

# --- auto_preview_image helper (replace existing) ---
YOUTUBE_PLAYLIST_FALLBACK = "https://www.gstatic.com/youtube/img/promos/growth/ytp-anotations-playlist.png"
PLACEHOLDER_IMAGE = "/static/images/placeholder.svg"

def _extract_youtube_id(url):
    """Return YouTube video id or None. Handles watch?v=, youtu.be/, embed/, shorts/"""
    if not url:
        return None
    url = url.strip()
    # 1) query param v=
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if 'v' in qs:
        vid = qs['v'][0]
        if vid:
            return vid.split('&')[0]
    # 2) path-based patterns
    patterns = [
        r'youtu\.be\/([^?&\/]+)',        # youtu.be/VIDEOID
        r'youtube\.com\/embed\/([^?&\/]+)',  # /embed/VIDEOID
        r'youtube\.com\/v\/([^?&\/]+)',      # /v/VIDEOID
        r'youtube\.com\/shorts\/([^?&\/]+)'  # /shorts/VIDEOID
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None

def fetch_preview_image(link):
    """
    Robust preview fetcher:
    - returns YouTube video thumbnail URL for single videos
    - returns a playlist fallback for playlists
    - tries OG:image or favicon for generic pages
    - always returns a safe placeholder if nothing found
    """
    try:
        link = (link or "").strip()
        if not link:
            return PLACEHOLDER_IMAGE

        parsed = urlparse(link)
        qs = parse_qs(parsed.query)

        # If playlist present and no video id in query, return playlist fallback
        if 'list' in qs and 'v' not in qs:
            return YOUTUBE_PLAYLIST_FALLBACK

        # Try to extract a youtube video id from common patterns
        vid = _extract_youtube_id(link)
        if vid:
            # sanitize id (remove trailing params)
            vid = vid.split('?')[0].split('&')[0]
            # Validate video ID format (should be 11 characters, alphanumeric + _ -)
            if len(vid) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', vid):
                # return static YouTube thumbnail (no HTTP request needed)
                return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
            else:
                print(f"Invalid YouTube video ID format: {vid}")
                return PLACEHOLDER_IMAGE

        # NOT a youtube video -> try open graph meta image
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(link, headers=headers, timeout=6)
        except Exception as e:
            # network failed — return placeholder
            print("fetch_preview_image: requests.get failed:", e)
            return PLACEHOLDER_IMAGE

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            og = (soup.find("meta", property="og:image") or
                  soup.find("meta", attrs={"name": "og:image"}))
            if og and og.get("content"):
                img = og["content"]
                # make absolute if necessary
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    img = urljoin(f"{parsed.scheme}://{parsed.netloc}", img)
                return img

            # fallback: favicon link
            icon = (soup.find("link", rel="icon") or
                    soup.find("link", rel="shortcut icon"))
            if icon and icon.get("href"):
                href = icon["href"]
                if href.startswith("//"):
                    return "https:" + href
                if href.startswith("http"):
                    return href
                return urljoin(f"{parsed.scheme}://{parsed.netloc}", href)

        # final fallback
        return PLACEHOLDER_IMAGE

    except Exception as e:
        print("fetch_preview_image: unexpected error:", e)
        return PLACEHOLDER_IMAGE

# WTF Form for Resource Upload
class ResourceForm(FlaskForm):
    title = StringField('Resource Title', validators=[DataRequired()], 
                       render_kw={'placeholder': 'Enter resource title'})
    description = TextAreaField('Description', validators=[DataRequired()], 
                               render_kw={'placeholder': 'Enter resource description', 'rows': 4})
    type = SelectField('Resource Type', validators=[DataRequired()], 
                      choices=[('', 'Select type'), ('Book', 'Book'), ('Video', 'Video'), ('Paper', 'Research Paper')])
    tags = StringField('Tags', render_kw={'placeholder': 'Enter comma-separated tags'})
    image_url = URLField('Image URL', validators=[Optional(), URL()], 
                        render_kw={'placeholder': 'https://example.com/image.jpg'})
    link = URLField('Resource Link', validators=[DataRequired(), URL()], 
                   render_kw={'placeholder': 'https://example.com/resource'})
    submit = SubmitField('Upload Resource')

# Create tables and initialize TF-IDF index
with app.app_context():
    db.create_all()
    
    # Initialize TF-IDF index with existing resources
    try:
        all_resources = Resource.query.all()
        tfidf_index.build_index(all_resources)
        print(f"TF-IDF index initialized with {tfidf_index.index_size()} resources.")
    except Exception as e:
        print(f"Warning: Could not initialize TF-IDF index: {e}")

@app.route('/')
def home():
    """Home page route"""
    return render_template('home.html')

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

@app.route("/add_resource", methods=['GET', 'POST'])
@login_required
def add_resource():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        rtype = request.form.get('type','').strip()
        tags = request.form.get('tags','').strip()
        link = request.form.get('link','').strip()
        image_url = request.form.get('image_url','').strip()

        # Auto-fetch if admin left image blank
        if not image_url:
            image_url = fetch_preview_image(link)
        # Debug log to console
        print(f"[add_resource] link={link}, extracted_image={image_url}")

        new_resource = Resource(
            title=title,
            description=description,
            type=rtype,
            tags=tags,
            image_url=image_url,
            link=link
        )
        db.session.add(new_resource)
        db.session.commit()

        # Rebuild TF-IDF index after adding
        all_resources = Resource.query.all()
        tfidf_index.build_index(all_resources)
        current_app.logger.info(f"Index rebuilt after adding resource. New size: {tfidf_index.index_size()}")

        flash("Resource added successfully!", "success")
        return redirect(url_for('admin_panel'))

    return render_template('add_resource.html')

@app.route("/edit_resource/<int:resource_id>", methods=["GET", "POST"])
@login_required
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if request.method == "POST":
        resource.title = request.form.get("title", "").strip()
        resource.description = request.form.get("description", "").strip()
        resource.link = request.form.get("link", "").strip()
        resource.type = request.form.get("type", "").strip()
        resource.tags = request.form.get("tags", "").strip()
        
        # Handle image URL update
        image_url = request.form.get('image_url', '').strip()
        if not image_url:
            image_url = fetch_preview_image(resource.link)
        resource.image_url = image_url
        
        db.session.commit()
        
        # Rebuild TF-IDF index after editing
        all_resources = Resource.query.all()
        tfidf_index.build_index(all_resources)
        
        flash("Resource updated successfully.", "success")
        return redirect(url_for("admin_panel"))
    return render_template("edit_resource.html", resource=resource)

@app.route("/delete_resource/<int:resource_id>", methods=["POST"])
@login_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    
    # Rebuild TF-IDF index after deletion
    all_resources = Resource.query.all()
    tfidf_index.build_index(all_resources)
    
    flash("Resource deleted successfully.", "success")
    return redirect(url_for("admin_panel"))

@app.route('/resources')
def resources():
    """Resources page route with combined search and filtering"""
    # Get search query and filter type from query parameters
    search_query = request.args.get('q', '').strip()
    filter_type = request.args.get('type', '')
    
    # Get counts for filter buttons (from database, not search results)
    book_count = Resource.query.filter_by(type='Book').count()
    video_count = Resource.query.filter_by(type='Video').count()
    paper_count = Resource.query.filter_by(type='Paper').count()
    total_count = Resource.query.count()
    
    if search_query:
        # Use TF-IDF search with optional type filter
        tfidf_index.build_index(Resource.query.all())
        results = tfidf_index.search_index(search_query, type_filter=filter_type if filter_type in ['Book', 'Video', 'Paper'] else None)
        
        # Add score attribute to each resource for template display
        resources_for_template = []
        for resource, score in results:
            resource.score = score
            resources_for_template.append(resource)
            
        current_app.logger.info(f"Search q={search_query!r} with filter={filter_type} returned {len(results)} results. Index size: {tfidf_index.index_size()}")
        
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

@app.route('/debug_last')
def debug_last():
    r = Resource.query.order_by(Resource.id.desc()).first()
    if not r:
        return "no resources yet"
    return f"Last resource: title={r.title}, link={r.link}, image_url={r.image_url}"

@app.route('/search')
def search():
    """Redirect search requests to resources route for unified handling"""
    # Redirect to resources route with the same parameters
    return redirect(url_for('resources', **request.args))


if __name__ == '__main__':
    app.run(debug=True)

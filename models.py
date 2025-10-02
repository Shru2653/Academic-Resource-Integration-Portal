from flask_sqlalchemy import SQLAlchemy

# This will be imported and used by app.py
db = SQLAlchemy()

class Resource(db.Model):
    """Resource model for academic materials"""
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Book, Video, Paper
    tags = db.Column(db.String(500))  # Comma-separated tags
    image_url = db.Column(db.String(500))
    link = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<Resource {self.title}>'
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags_from_list(self, tags_list):
        """Set tags from a list"""
        self.tags = ', '.join(tags_list) if tags_list else ''

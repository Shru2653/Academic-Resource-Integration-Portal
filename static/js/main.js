// Handle image loading errors
function handleImageError(img) {
  // Get the placeholder URL from a data attribute or use a default
  const placeholderUrl = img.dataset.placeholder || '/static/images/placeholder.svg';
  
  // Prevent infinite loop by checking if we're already showing the placeholder
  if (img.src !== window.location.origin + placeholderUrl) {
    img.onerror = null; // Remove the error handler to prevent infinite loop
    img.src = placeholderUrl;
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Set up image error handling for all resource images
  const resourceImages = document.querySelectorAll('.card-img-top');
  resourceImages.forEach(img => {
    img.dataset.placeholder = '/static/images/placeholder.svg';
  });
});

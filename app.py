from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import rembg
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'background-remover-secret-key'

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate unique filename with UUID
        unique_id = str(uuid.uuid4())
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{unique_id}.{original_extension}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file
        file.save(filepath)
        
        try:
            # Process the image with rembg
            processed_filename = f"{unique_id}.png"  # Always save as PNG for transparency
            processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            
            # Open the image
            input_image = Image.open(filepath)
            
            # Remove background
            output_image = rembg.remove(input_image)
            
            # Save the processed image
            output_image.save(processed_filepath, format='PNG')
            
            # Return success page with image preview and download link
            return render_template('index.html', 
                                  processed_image=processed_filename,
                                  unique_id=unique_id)
        
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload JPG or PNG images only.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename), 
                         mimetype='image/png',
                         as_attachment=True,
                         download_name='background_removed.png')
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename), 
                         mimetype='image/png')
    except Exception as e:
        flash(f'Error previewing file: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
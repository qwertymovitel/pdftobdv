from flask import Flask, render_template, request, jsonify, send_file
import os
import fitz
import cv2
import numpy as np
from PIL import Image
import tempfile
import uuid

app = Flask(__name__)

# Configure upload and output directories
UPLOAD_FOLDER = '/data/uploads'
OUTPUT_FOLDER = '/data/output'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class SchematicProcessor:
    def __init__(self):
        self.components = []
        self.connections = []

    def process_pdf(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            all_components = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                
                # Convert to numpy array
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_np = np.array(img)
                
                # Process the page
                components = self.process_page(img_np)
                all_components.extend(components)
            
            return all_components
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def process_page(self, img):
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        components = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                component_type = self.classify_component(w, h)
                components.append({
                    'type': component_type,
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                })
        
        return components

    def classify_component(self, width, height):
        aspect_ratio = width / height if height != 0 else 0
        
        if aspect_ratio > 2:
            return 'resistor'
        elif 0.8 < aspect_ratio < 1.2:
            return 'ic'
        else:
            return 'unknown'

    def export_brd(self, components, output_path):
        with open(output_path, 'w') as f:
            f.write("BRD 1.0\n")
            f.write(f"Components: {len(components)}\n")
            
            for i, comp in enumerate(components):
                f.write(f"Component {i}: {comp['type']} {comp['x']} {comp['y']}\n")
            
            f.write("Connections: 0\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create unique filename
        filename = str(uuid.uuid4()) + '.pdf'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Process the schematic
            processor = SchematicProcessor()
            components = processor.process_pdf(filepath)
            
            # Generate output filename
            output_filename = os.path.splitext(filename)[0] + '.brd'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # Export BRD file
            processor.export_brd(components, output_path)
            
            return jsonify({
                'status': 'success',
                'message': 'File processed successfully',
                'output_file': output_filename
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up upload
            os.remove(filepath)
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/')
def download_file(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        as_attachment=True,
        attachment_filename=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
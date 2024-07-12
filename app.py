from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageFilter
import io
import base64
import uuid

app = Flask(__name__)

# Mock database of smartphone models
SMARTPHONE_MODELS = {
    "iphone12": {"width": 1170, "height": 2532},
    "galaxys21": {"width": 1080, "height": 2400},
    "iphone13": {"width": 1170, "height": 2532},
    "iphone13Pro": {"width": 1170, "height": 2532},
    "galaxyS22": {"width": 1080, "height": 2400},
    "pixel6": {"width": 1080, "height": 2400},
    "onePlus9": {"width": 1080, "height": 2400},
    "xiaomiMi11": {"width": 1440, "height": 3200},
    "sonyXperia1III": {"width": 1644, "height": 3840},
    "huaweiP40Pro": {"width": 1200, "height": 2640},
    "oppoFindX3Pro": {"width": 1440, "height": 3216},
    "galaxyNote20Ultra": {"width": 1440, "height": 3088},
    "iphoneSE2020": {"width": 750, "height": 1334},
    "pixel5": {"width": 1080, "height": 2340},
    # Add more models here
}

# Store processed images temporarily
PROCESSED_IMAGES = {}

@app.route('/')
def index():
    return render_template('index.html', models=SMARTPHONE_MODELS)

@app.route('/preview', methods=['POST'])
def preview_image():
    if 'image' not in request.files:
        app.logger.error("No image file in request")
        return jsonify({"error": "No image uploaded"}), 400
    
    image = request.files['image']
    model = request.form.get('model')
    
    if model not in SMARTPHONE_MODELS:
        app.logger.error(f"Invalid model: {model}")
        return jsonify({"error": "Invalid smartphone model"}), 400
    
    # Open the image
    img = Image.open(image)
    
    # Convert image to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    app.logger.info(f"Image processed successfully for model: {model}")
    
    return jsonify({
        "image": img_str, 
        "id": str(uuid.uuid4()),
        "screenWidth": SMARTPHONE_MODELS[model]["width"],
        "screenHeight": SMARTPHONE_MODELS[model]["height"]
    })

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    image_data = request.json['image']
    filter_type = request.json['filter']
    
    # Decode base64 image
    image_data = base64.b64decode(image_data.split(',')[1])
    img = Image.open(io.BytesIO(image_data))
    
    # Apply filter
    if filter_type == 'blur':
        img_filtered = img.filter(ImageFilter.BLUR)
    elif filter_type == 'contour':
        img_filtered = img.filter(ImageFilter.CONTOUR)
    elif filter_type == 'emboss':
        img_filtered = img.filter(ImageFilter.EMBOSS)
    else:
        return jsonify({"error": "Invalid filter type"}), 400
    
    # Convert filtered image to base64
    buffered = io.BytesIO()
    img_filtered.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate a unique ID for this processed image
    image_id = str(uuid.uuid4())
    PROCESSED_IMAGES[image_id] = buffered.getvalue()
    
    return jsonify({"image": img_str, "id": image_id})

@app.route('/crop', methods=['POST'])
def crop_image():
    image_id = request.json['imageId']
    crop_data = request.json['cropData']
    model = request.json['model']
    
    if image_id not in PROCESSED_IMAGES:
        return jsonify({"error": "Image not found"}), 404
    
    img = Image.open(io.BytesIO(PROCESSED_IMAGES[image_id]))
    
    # Crop the image
    cropped_img = img.crop((crop_data['x'], crop_data['y'], 
                            crop_data['x'] + crop_data['width'], 
                            crop_data['y'] + crop_data['height']))
    
    # Resize to fit the screen
    screen_size = SMARTPHONE_MODELS[model]
    resized_img = cropped_img.resize((screen_size['width'], screen_size['height']))
    
    # Convert cropped and resized image to base64
    buffered = io.BytesIO()
    resized_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate a new unique ID for this processed image
    new_image_id = str(uuid.uuid4())
    PROCESSED_IMAGES[new_image_id] = buffered.getvalue()
    
    return jsonify({"image": img_str, "id": new_image_id})

@app.route('/download/<image_id>', methods=['GET'])
def download_image(image_id):
    if image_id not in PROCESSED_IMAGES:
        return jsonify({"error": "Image not found"}), 404
    
    return send_file(
        io.BytesIO(PROCESSED_IMAGES[image_id]),
        mimetype='image/png',
        as_attachment=True,
        download_name='edited_image.png'
    )

if __name__ == '__main__':
    app.run(debug=True)
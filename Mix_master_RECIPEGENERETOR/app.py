from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os, mysql.connector, google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DB')
}

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        image = request.files['image']
        ingredients = request.form['ingredients']
        gastronomy = request.form['gastronomy']

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        prompt = f"""
        Analyze the provided image and use these details:
        Ingredients: {ingredients}
        Gastronomy Suggestions: {gastronomy}

        Provide a structured cocktail recipe including:
        - Cocktail name
        - Short description
        - Ingredients list clearly with amounts
        - Step by step preparation
        - Food pairing recommendations
        - Safety warnings if necessary
        """

        model = genai.GenerativeModel('gemini-2.0-flash')
        with open(image_path, 'rb') as img:
            img_data = img.read()

        response = model.generate_content([prompt, {"mime_type":"image/png","data":img_data}])
        recipe_response = response.text

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recipes (image, ingredients, gastronomy, recipe)
            VALUES (%s, %s, %s, %s)
        """, (filename, ingredients, gastronomy, recipe_response))
        conn.commit()
        cursor.close()
        conn.close()

        return render_template('index.html', recipe=recipe_response)

    return render_template('index.html', recipe=None)

if __name__ == '__main__':
    app.run(debug=True)
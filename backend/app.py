from flask import Flask, request, jsonify, send_from_directory
import bcrypt
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
import time
from werkzeug.utils import secure_filename
from sqlalchemy import text
import pymysql
from verify import verify_documents

# Initialize Flask app
app = Flask(__name__)

# --- Configurations ---
app.config['SECRET_KEY'] = 'demo'
app.config['JWT_SECRET_KEY'] = 'supersecret-jwt-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Subash%4025@localhost:3306/invoice_processor'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Add SQL logging

# Define upload directories
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
AADHAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'aadhar')
PAN_FOLDER = os.path.join(UPLOAD_FOLDER, 'pan')

# Create folders if they don't exist
for folder in [UPLOAD_FOLDER, AADHAR_FOLDER, PAN_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size

# --- Extensions ---
bcrypt = Bcrypt(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
jwt = JWTManager(app)
db = SQLAlchemy(app)

# --- User Model ---
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.BigInteger, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    aadhar_file = db.Column(db.String(50), nullable=False)  # Path to stored Aadhar file
    pan_file = db.Column(db.String(255), nullable=False)     # Path to stored PAN file
    status = db.Column(db.Enum('pending', 'rejected', 'verified', name='status_enum'),default='pending',nullable=False)
    uploaded_time = db.Column(db.DateTime,default=db.func.current_timestamp(),nullable=False)
    
    def __repr__(self):
        return f'<Users {self.email}>'

# --- Helper Functions ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DB Initialization --- 
with app.app_context():
    # Only create tables if they don't exist
    db.create_all()

# --- Routes ---
@app.route("/check-db")
def check_db():
    try:
        # Use text() to properly wrap SQL queries
        result = db.session.execute(text('SELECT 1')).fetchone()
        return jsonify({"status": "Database connected", "result": str(result[0])})
    except Exception as e:
        return jsonify({"status": "Database error", "error": str(e)}), 500

@app.route("/users")
def list_users():
    try:
        users = Users.query.all()
        user_list = [{"id": user.id, "name": user.name, "email": user.email, "phone": user.phone} for user in users]
        return jsonify({"count": len(user_list), "users": user_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET": 
        return "This is the Signup API endpoint. Please POST your form here.", 200
    try:
        print("Signup request received")
        print("Content-Type:", request.headers.get('Content-Type'))
        
        # Get form data (multipart/form-data from frontend)
        name = request.form.get('name')
        dob = request.form.get('dob')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # ✅ Use file data
        aadhar_file = request.files.get('aadhar')
        pan_file = request.files.get('pan')

        print("Signup request received")
        print(f"Name: {name}, Email: {email}, Phone: {phone}, DOB: {dob}")
        
        # Validate required fields
        if not all([name, dob, email, phone, password]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Check if user already exists
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email already exists"}), 409
        
        if not aadhar_file or not pan_file:
            return jsonify({"error": "Aadhar and PAN documents are required"}), 400
        
        # Validate file types
        if not allowed_file(aadhar_file.filename) or not allowed_file(pan_file.filename):
            return jsonify({"error": "Invalid file type. Allowed types: PDF, JPG, PNG"}), 400
            
        # Create unique filenames using timestamp + email
        timestamp = int(time.time())
        
        aadhar_filename = f"{timestamp}_{secure_filename(email)}_{secure_filename(aadhar_file.filename)}"
        pan_filename = f"{timestamp}_{secure_filename(email)}_{secure_filename(pan_file.filename)}"
        
        aadhar_path = os.path.join(AADHAR_FOLDER, aadhar_filename)
        pan_path = os.path.join(PAN_FOLDER, pan_filename)
        
        # Save files
        aadhar_file.save(aadhar_path)
        pan_file.save(pan_path)
        
        # Store relative paths in database
        db_aadhar_path = os.path.join('uploads/aadhar', aadhar_filename)
        db_pan_path = os.path.join('uploads/pan', pan_filename)

        # ✅ Verify documents using your Gemini + email script
        result = verify_documents(db_aadhar_path, db_pan_path, email)
        print(result)

        if result["Status"] == "Rejected":
            return jsonify({"message": "Document verification failed!"}), 400
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = Users(
            name=name,
            dob=dob,
            email=email,
            phone=phone,
            password=hashed_password,
            aadhar_file=result['Aadhaar'],
            pan_file=result['PAN'],
            status=result["Status"],

        )
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        print(f"User created: ID={new_user.id}, email={new_user.email}")
        print("done")
        # Generate token
        access_token = create_access_token(identity=new_user.id)
        return jsonify({
            "token": access_token,
            "email": new_user.email,
            "name": new_user.name,
            "user_id": new_user.id,
            "message": "User created successfully"
        }), 201
        
    except Exception as e:
        print("Signup Error:", str(e))
        db.session.rollback()  # Roll back the session on error
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        print("Login request received")
        
        # Handle different content types
        if request.headers.get('Content-Type') == 'application/json':
            data = request.get_json(force=True)
        else:
            data = request.form
        
        email = data.get("email")
        password = data.get("password")
        
        print(f"Login attempt: email={email}")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        user = Users.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            token = create_access_token(identity=user.id)
            return jsonify({
                "token": token, 
                "email": user.email,
                "name": user.name,
                "message": "Login successful"
            })
        
        return jsonify({"error": "Invalid credentials"}), 401
    
    except Exception as e:
        print("Login Error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    try:
        user_id = get_jwt_identity()
        user = Users.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "message": f"Welcome {user.name}!",
            "user_id": user_id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone
        })
    
    except Exception as e:
        print("Dashboard Error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({"message": f"File uploaded: {filename}", "path": filepath}), 200
    
    except Exception as e:
        print("Upload Error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# --- Run ---
if __name__ == "__main__":
    print("Starting Flask application...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(debug=True,port=5000)
import logging
import os
import uuid
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from web3 import Web3

# Configure logging for local development
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and configurations
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'supersecretflaskskey'

# Configure SQLite database for local use
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loyalty_points.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the ABI and contract address
with open('./build/contracts/LoyaltyPoints.json') as f:
    contract_data = json.load(f)
    contract_address = contract_data['networks']['5777']['address']  # Adjust if using a different network
    contract_abi = contract_data['abi']

# Initialize Web3
ganache_url = 'http://127.0.0.1:7545'  # Ganache default URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Define the contract instance
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# User Model
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    points_balance = db.Column(db.Integer, default=0)
    wallet_address = db.Column(db.String(42), unique=True, nullable=False)

# Company Model
class Company(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# Initialize the database and create tables
with app.app_context():
    db.create_all()
    logger.info("Database and tables created successfully.")

# Home Page
@app.route("/")
def home_route():
    return render_template("home.html")

# User Routes
@app.route("/user/login", methods=['GET'])
def user_login_page():
    return render_template("user_login.html")

@app.route("/user/register", methods=['GET'])
def user_register_page():
    return render_template("user_register.html")

@app.route("/user/dashboard", methods=['GET'])
def user_dashboard():
    user_id = session.get('user_id')  # Get user ID from session
    if not user_id:
        return redirect(url_for('home_route'))  # Redirect to home if user is not logged in
    
    user = User.query.get(user_id)  # Retrieve user by ID
    if not user:
        return redirect(url_for('home_route'))  # Redirect if user is not found
    
    points_balance = user.points_balance  # Get user's points balance
    user_name = user.name  # Assuming you have a name field in the User model
    
    return render_template("user_dashboard.html", user_name=user_name, points_balance=points_balance, user_email=user.email)

@app.route("/login/user", methods=['POST'])
def login_user():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password == data['password']:
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful!', 'user_id': user.id})
    return jsonify({'message': 'Invalid credentials!'}), 401

from sqlalchemy.exc import IntegrityError

@app.route("/register/user", methods=['POST'])
def register_user():
    data = request.get_json()
    required_fields = ['name', 'email', 'password', 'wallet_address']
    
    # Check if all required fields are provided
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create new user object
    new_user = User(
        id=str(uuid.uuid4()), 
        name=data['name'], 
        email=data['email'], 
        password=data['password'],
        wallet_address=data['wallet_address']
    )
    
    try:
        # Add user to the database
        db.session.add(new_user)
        db.session.commit()

        # Call the smart contract's registerUser function
        user_wallet = data['wallet_address']  # Extract the wallet address
        try:
            tx_hash = contract.functions.registerUser().transact({'from': user_wallet})
            web3.eth.waitForTransactionReceipt(tx_hash)

        except Exception as e:
            return jsonify({'error': 'Failed to register user in smart contract: ' + str(e)}), 500


        return jsonify({'message': 'User registered successfully!'}), 201
    except IntegrityError:
        db.session.rollback()  # Rollback the session in case of an error
        return jsonify({'error': 'User with this email or wallet address already exists!'}), 400
    except Exception as e:
        db.session.rollback()  # Rollback in case of other errors
        return jsonify({'error': str(e)}), 500


# Company Routes
@app.route("/company/login", methods=['GET'])
def company_login_page():
    return render_template("company_login.html")

@app.route("/company/register", methods=['GET'])
def company_register_page():
    return render_template("company_register.html")

@app.route("/company/dashboard", methods=['GET'])
def company_dashboard():
    company_id = session.get('company_id')
    if not company_id:
        return redirect(url_for('home_route'))
    
    company = Company.query.get(company_id)
    # Fetch all registered users
    users = User.query.all()
    
    return render_template("company_dashboard.html", company=company, users=users)
@app.route("/login/company", methods=['POST'])
def login_company():
    data = request.json
    company = Company.query.filter_by(email=data['email']).first()
    if company and company.password == data['password']:
        session['company_id'] = company.id
        return jsonify({'message': 'Login successful!', 'company_id': company.id})
    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route("/register/company", methods=['POST'])
def register_company():
    data = request.json
    new_company = Company(id=str(uuid.uuid4()), name=data['name'], email=data['email'], password=data['password'])
    db.session.add(new_company)
    db.session.commit()
    return jsonify({'message': 'Company registered successfully!'})

@app.route("/issue_points", methods=['POST'])
def issue_points():
    data = request.get_json()
    user_email = data.get('user_email')
    points = data.get('points')

    logger.info(f"Received request to issue points. User email: {user_email}, Points: {points}")

    # Retrieve user by email
    user = User.query.filter_by(email=user_email).first()
    if not user:
        logger.error("User not found")
        return jsonify({'message': 'User not found'}), 404

    user_wallet = user.wallet_address
    if user_wallet is None:
        logger.error("User wallet address is not available")
        return jsonify({'message': 'User wallet address is not available'}), 400

    try:
        # Convert points to an integer (uint256)
        points = int(points)  # Ensure points is an integer
        tx_hash = contract.functions.issuePoints(user_wallet, points).transact({'from': user_wallet})
        logger.info(f"Points issued successfully. Transaction hash: {tx_hash.hex()}")

        # Update user's points balance in the database
        user.points_balance += points
        db.session.commit()  # Commit the changes to the database

        logger.info(f"User's points balance updated in the database. New balance: {user.points_balance}")
        return jsonify({'message': 'Points issued successfully', 'tx_hash': tx_hash.hex()}), 200
    except Exception as e:
        logger.error(f"Error during transaction: {str(e)}")
        return jsonify({'message': str(e)}), 500



@app.route("/redeem_points", methods=["POST"])
def redeem_points():
    data = request.json
    redeem_points = int(data.get('redeem_points'))

    # Get user_id from session
    user_id = session.get('user_id')  # Retrieve user_id from session
    if not user_id:
        return jsonify({"message": "User not logged in!"}), 401  # Check if user is logged in

    # Retrieve the user object using user_id
    user = User.query.get(user_id)  # Fetch the user by their ID
    if user:
        if user.points_balance >= redeem_points:
            # Interact with the smart contract to redeem points
            user_wallet = user.wallet_address  # Get user's wallet address from the user object
            tx_hash = contract.functions.redeemPoints(redeem_points).transact({'from': user_wallet})

            # Log the transaction
            logger.info(f"Successfully redeemed {redeem_points} points. Transaction hash: {tx_hash.hex()}")
            
            user.points_balance -= redeem_points  # Deduct points from user balance
            db.session.commit()  # Commit the changes to the database
            return jsonify({"message": f"Successfully redeemed {redeem_points} points!"}), 200
        else:
            return jsonify({"message": "Insufficient points!"}), 400
    else:
        return jsonify({"message": "User not found!"}), 404


# Run the Flask app locally
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)  # Run on localhost

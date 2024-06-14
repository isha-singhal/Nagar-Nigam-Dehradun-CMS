from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from datetime import datetime



app = Flask(__name__)
app.secret_key = '6440ec0229ea084314725f77af57dfd56dc9abcba52f0028fbef1de774bbba7f'


app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "3306"
app.config['MYSQL_DB'] = "flask_db"

mysql = MySQL(app)
login_manage = LoginManager()
login_manage.init_app(app)
bcrypt = Bcrypt(app)

#User Loader function
@login_manage.user_loader
def load_user(user_id):
    return User.get(user_id)

class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email
    
    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name, email FROM admin WHERE id =%s",(user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return User(user_id, result[0], result[1])
        

class Complaint:
    @staticmethod
    def fetch_all():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM complaints")
        complaints = cursor.fetchall()
        cursor.close()
        return complaints

    @staticmethod
    def update_status(complaint_id, status):
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (status, complaint_id))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def update_escalation(complaint_id, escalated):
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE complaints SET escalated=%s WHERE id=%s", (escalated, complaint_id))
        mysql.connection.commit()
        cursor.close()

# Assuming KoboToolbox form details
KOBO_URL = "https://kf.kobotoolbox.org/api/v2/assets/axwuBkrNP3bJWRSSukj7Vs/data.json"
KOBO_TOKEN = '86ce8000b5a7075efac7c6dbf1db99ffdc25b858'

# Complaint Status choices
COMPLAINT_STATUS = ['Resolved', 'Unresolved', 'In Progress']
ESCALATION_STATUS = ['Yes', 'No']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        phone_no = request.form.get('phone_no')
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id, kobo_id, name, phone_number, mail_id, date, type_of_hazard, 
            Geolocation_latitude, Geolocation_longitude, status, escalated 
            FROM complaints WHERE phone_number = %s
            """, (phone_no,))
        complaints_data = cursor.fetchall()
        cursor.close()
        return render_template('check_status.html', complaints=complaints_data)
    return render_template('check_status.html', complaints=[])

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, email, password FROM admin WHERE email=%s",(email,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2] )
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/fetch_complaints')
@login_required
def fetch_complaints():
    headers = {'Authorization': f'Token {KOBO_TOKEN}'}
    response = requests.get(KOBO_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for item in data['results']:
            kobo_id = item['_id']
            name = item['Name']
            phone_number = item['Phone_Number']
            mail_id = item['Mail_Id']
            date = item['Date']
            type_of_hazard = item['Type_of_hazard']
            geolocation = item['_geolocation']
            geolocation_latitude = geolocation[0]
            geolocation_longitude = geolocation[1]
            status = 'Unresolved'
            escalated = 'No'

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id FROM complaints WHERE kobo_id = %s", (kobo_id,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(
                    "INSERT INTO complaints (kobo_id, name, phone_number, mail_id, date, type_of_hazard, geolocation_latitude, geolocation_longitude, status, escalated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (kobo_id, name, phone_number, mail_id, date, type_of_hazard, geolocation_latitude, geolocation_longitude, status, escalated)
                )
                mysql.connection.commit()
            cursor.close()
        
        return jsonify({"message": "Complaints fetched and stored successfully"}), 200
    else:
        return jsonify({"error": "Failed to fetch complaints from KoboToolbox"}), 500

@app.route('/update_status', methods=['POST'])
@login_required
def update_status():
    complaint_id = request.form['complaint_id']
    status = request.form['status']

    if status not in COMPLAINT_STATUS:
        return jsonify({"error": "Invalid status"}), 400

    Complaint.update_status(complaint_id, status)
    return redirect(url_for('view_complaints'))

@app.route('/update_escalate_status', methods=['POST'])
@login_required
def update_escalate_status():
    complaint_id = request.form['complaint_id']
    escalated = request.form['escalated']

    if escalated not in ESCALATION_STATUS:
        return jsonify({"error": "Invalid escalation status"}), 400

    Complaint.update_escalation(complaint_id, escalated)
    return redirect(url_for('view_complaints'))

@app.route('/view_complaints')
@login_required
def view_complaints():
    complaints = Complaint.fetch_all()
    return render_template('view_complaints.html', complaints=complaints, statuses=COMPLAINT_STATUS)


# Additional routes for map visualization using Leaflet.js
@app.route('/map')
@login_required
def map():
    complaints = Complaint.fetch_all()
    return render_template('map.html', complaints=complaints)

# @app.route('/view_complaints')
# def dash():
#     return render_template('view_complaints.html')


if __name__ == '__main__':
    app.run(debug=False)
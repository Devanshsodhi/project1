from flask import Flask, render_template, request
from pymongo import MongoClient
from flask_mail import Mail, Message
import qrcode
import os
from bson import ObjectId 
app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
registration_collection = db['registration']
feedback_collection = db['feedback']
admin_collection = db['admin']
attendance_collection = db['attendance']

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'f20220091@dubai.bits-pilani.ac.in' 
app.config['MAIL_PASSWORD'] = 'raaj0978'
app.config['MAIL_DEFAULT_SENDER'] = 'f20220091@dubai.bits-pilani.ac.in'

@app.route('/scan/', methods=['POST'])
def scan_qr():
    try:
        qr_data = request.form['_id']
        
        # Identify the user based on the QR code data
        user = registration_collection.find_one({"_id": ObjectId(qr_data)})

        if user:
            # Update attendance in the "attendance" collection
            attendance_collection.insert_one({"user_id": user["_id"], "attended": True})
            return "Attendance updated successfully"
        else:
            return "User not found"

    except Exception as e:
        print("Error:", str(e))
        return "An error occurred while scanning the QR code."



@app.route('/')  # Route for the navigation page
def navig():
    return render_template('navig.html')

mail = Mail(app)

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    return qr_image

@app.route('/registration/')
def index():
    return render_template('registration.html')

@app.route('/email_form', methods=["POST"])
def send_email():
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        message = request.form['message']
        session = request.form.get('session')
        msg = Message(subject='Registration Confirmation', recipients=[email])

        mail.send(msg)
        return "Email sent successfully"
    except Exception as e:
        print("Error:", str(e))
        return "An error occurred while sending the email."

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        company = request.form['company']
        designation = request.form['designation']
        session = request.form.get('session')
        session_mapping = {
            'dot-1': 'Session 1',
            'dot-2': 'Session 2',
            'dot-3': 'Session 3'
        }
        session_value = session_mapping.get(session, 'Unknown Session')
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'company': company,
            'designation': designation,
            'session': session_value  
        }
        inserted_data = registration_collection.insert_one(data)
        print("Data inserted into MongoDB:", data)

        # Generate a QR code image
        qr_code_image = generate_qr_code(str(inserted_data.inserted_id))
        
        # Save the QR code image directly in the qrcodes folder
        qr_image_filename = f"{inserted_data.inserted_id}.png"
        qr_image_path = os.path.join("C:/Users/sodhi/Desktop/testing/__pycache__", qr_image_filename)
        qr_code_image.save(qr_image_path)

         # Save the QR code filename or path in the database
        qr_code_db_path = f"static/qrcodes/{qr_image_filename}"
        registration_collection.update_one(
            {"_id": inserted_data.inserted_id},
            {"$set": {"qr_code_path": qr_code_db_path}}
        )

        # Send registration confirmation email with QR code attached
        msg = Message(subject='Registration Confirmation', recipients=[email])
        msg.body = f"Hello {first_name} {last_name}, Thank you for registering for the event!. Your scheduled session is {session_value} , Please download the QR code provided as attachement"
        with open(qr_image_path, "rb") as qr_image_file:
            msg.attach(
                "qr_code.png",
                "image/png",
                qr_image_file.read(),
                "inline",
                headers=[("Content-ID", "<qr_code_image>")],
            )
        mail.send(msg)

        return render_template('registration.html')
    except Exception as e:
        print("Error:", str(e))
        return "An error occurred while submitting the form."

@app.route('/feedback/', methods=['GET', 'POST'])
def feedback_form():
    if request.method == 'POST':
        try:
            first_name = request.form['firstname']
            last_name = request.form['lastname']
            email = request.form['email']
            session = request.form['session']
            phone = request.form['phonenumber']
            review = request.form['review']
            area_of_improvement = request.form['areaofimprovement']
            session = request.form.get('session')
            session_mapping = {
                'dot-1': 'Very Satisfied',
                'dot-2': 'Satisfied',
                'dot-3': 'Neutral'
            }
            session_value = session_mapping.get(session, 'Unknown Session')
            feedback_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'review': review,
                'area_of_improvement': area_of_improvement,
                'session': session_value 
            }
            
            feedback_collection.insert_one(feedback_data)

            print("Feedback data inserted into MongoDB:", feedback_data)

            # Send feedback confirmation email
            msg = Message(subject='Feedback Confirmation', recipients=[email])
            msg.body = f"Hello {first_name}, Thank you for providing your feedback!"
            mail.send(msg)

            return render_template('feedback.html', feedback_message="Thank you for your feedback!")
        except Exception as e:
            print("Error:", str(e))
            return "An error occurred while submitting the feedback form."

    return render_template('feedback.html')

@app.route('/admin/')  # Change this route to '/admin/'
def admin_index():  # Change the function name to 'admin_index'
    return render_template('admin2.html')

@app.route('/get_ip', methods=['GET'])
def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        print(request.environ['REMOTE_ADDR'])
    else:
        print(request.environ['HTTP_X_FORWARDED_FOR'])  # if behind a proxy

@app.route('/admin/', methods=['POST'])
def submit_adminform():
    try:
        event_name = request.form['event_name']
        print('got name', event_name)

        event_datetime = request.form['event_datetime']
        event_venue = request.form.get('event_venue')
        event_presenters = request.form.getlist('event_presenters')
        event_sponsors = request.form.getlist('event_sponsors')
        event_agenda = request.form['event_agenda']

        data = {
            'eventname': event_name,
            'agenda': event_agenda,
            'datetime': event_datetime,
            'venue': event_venue,
            'event_presenters': event_presenters,
            'event_sponsors': event_sponsors
        }

        # Insert data into a MongoDB collection (e.g., admin_collection)
        admin_collection.insert_one(data)

        print('Data inserted to admin collection:', data)
        return render_template('admin2.html')

    except Exception as e:
        print('Error:', str(e))
        return 'Error'

if __name__ == '__main__':
    app.run(debug=True)

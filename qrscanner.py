import cv2
from pyzbar.pyzbar import decode
import time
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['qr_codes']
qr_collection = db['qrcodes']
user_db = client['mydatabase']  # Change this to the actual database name
registration_collection = user_db['registration']  # Change this to the actual collection name

cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Camera not opened!")
    camera = False
else:
    cam.set(5, 640)
    cam.set(6, 480)
    camera = True

while camera:
    success, frame = cam.read()

    for qr_code in decode(frame):
        qr_data = qr_code.data.decode('utf-8')
        print("QR Code ID:", qr_data)

        # Check if the QR code ID matches a user in the registration collection
        user = registration_collection.find_one({"_id": ObjectId(qr_data)})
        if user:
            print("User found:", user)
            # Save QR code data in MongoDB with user details
            qr_collection.insert_one({
                "qr_id": qr_data,
                "user_id": user["_id"],
                "user_present": True,
                "user_name": user["first_name"] + " " + user["last_name"],
                "user_email": user["email"]
            })
        else:
            print("User not found")

        time.sleep(10)

    cv2.imshow("Qr_Code_Scanner", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        break

# Release the camera and close the OpenCV windows
cam.release()
cv2.destroyAllWindows()

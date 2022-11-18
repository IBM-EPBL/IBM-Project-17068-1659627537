# from crypt import methods

from __future__ import print_function

from distutils.log import debug
from email import message
from gzip import BadGzipFile
from itertools import dropwhile
# from signal import alarm
from sqlite3 import connect
import cvlib as cv
from cvlib.object_detection import draw_bbox
import cv2 
import time
import numpy as np
import requests

import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

from werkzeug.utils import secure_filename
from playsound import playsound

import os
from dotenv import load_dotenv, find_dotenv

from flask import Flask, request, render_template, redirect, url_for, make_response

from cloudant.client import Cloudant

load_dotenv(find_dotenv())


client = Cloudant.iam(os.getenv("IBM_CLOUDANT_KEY"), os.getenv("IBM_CLOUDANT_USER"), connect=True)

my_database = client.create_database("my_database")

app = Flask(__name__)

def sendMail(to_email, to_name, subject, content):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("EMAIL_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    html_content = "<html><body><h1>"+ content +"</h1></body></html>"
    sender = {"name":"Admin@VirtualEye","email":"fullstackdevme07@gmail.com"}
    to = [{"email":to_email,"name": to_name}]
    headers = {"Some-Custom-Name":"unique-id-1234"}
    params = {"parameter":"My param value","subject": subject}
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, headers=headers, html_content=html_content, sender=sender, subject=subject)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/index.html")
def home():
    return render_template("index.html")

@app.route("/prediction")
def prediction():
    if request.cookies.get("isLoggedIn") == "True":
        return render_template("prediction.html")
    else:
        return render_template("login.html", message="You must be logged in first!")

@app.route("/dashboard")
def dashboard():
    if request.cookies.get("isLoggedIn") == "True":
        return render_template("dashboard.html")
    else:
        return render_template("login.html", message="You must be logged in first!")
        

@app.route('/upload', methods = ['POST'])
def upload_file():
    if request.cookies.get("isLoggedIn") == "True":
        if request.method == 'POST':
            f = request.files['video']
            f.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads', secure_filename(f.filename)))
            return render_template("prediction.html", message="File upload success, Processing stream...", bad=False, filename=f.filename)
    else:
        return render_template("login.html", message="You must be logged in first!")

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/afterreg", methods=["POST"])
def afterreg():
    x = [x for x in request.form.values()]
    print(x)
    data = {
        "_id": x[1],
        "name": x[0],
        "psw": x[2],
        "feedback": ""
    }
    print(data)

    query = {"_id": {"$eq": data["_id"]}}

    docs = my_database.get_query_result(query)
    print(docs)

    print(len(docs.all()))

    if(len(docs.all()) == 0):
        url = my_database.create_document(data)
        content = "Hi, " + data["name"] + " You have successfully registered with us!"
        sendMail(data["_id"], data["name"], "Registration Successfull", content)
        return render_template("register.html", message="Registration Successfull, Please login using your credentials", bad=False)
    else:
        return render_template("register.html", message="You are already a member, please login using your credentials", bad=True)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/afterlogin", methods=["POST"])
def afterlogin():
   
    user = request.form["_id"]
    passw = request.form["psw"]
    print(user, passw)

    query = {"_id": {"$eq": user}}

    docs = my_database.get_query_result(query)
    print(docs)

    print(len(docs.all()))

    if(len(docs.all()) == 0):
        resp = make_response(render_template("login.html", message="The email is not found!"))  
        return resp
    else:
        if((user == docs[0][0]["_id"]) and passw == docs[0][0]["psw"]):
            resp = make_response(redirect(url_for("dashboard")))
            resp.set_cookie('isLoggedIn',"True") 
            print(docs[0][0]["_id"])
            if user == "admin@virtualeye.com":
                print("zsbdjsjbh")
                resp.set_cookie('isAdmin',"True") 
            resp.set_cookie('email', user)  
            return resp
        else:
            print("Invalid User")
            resp = make_response(render_template("login.html", message="The email is not found!"))
    

@app.route("/logout")
def logout():
    if request.cookies.get("isLoggedIn") == "True":
        resp = make_response(render_template("login.html", message="You have logged out successfully!"))
        resp.set_cookie('isLoggedIn', '', expires=0)
        resp.set_cookie('isAdmin','', expires=0) 
        resp.set_cookie('email', '', expires=0)
        return resp
    else:
        return render_template("login.html", message="You must be logged in first!")
        

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.cookies.get("isLoggedIn") == "True":
        if request.method == "GET":
            if request.cookies.get("isAdmin") == "True":
                return render_template("feedback.html", email=request.cookies.get('email'), admin=True)
            return render_template("feedback.html", email=request.cookies.get('email'))
        else:
            print(request.form)
            email = request.form["email"]
            print(email)
            feedback = request.form["feedback"]
            print(feedback)

            query = {"_id": {"$eq": email}}

            docs = my_database.get_query_result(query)

            print(docs)

            print(len(docs.all()))

            if(len(docs.all()) == 0):
                resp = make_response(render_template("feedback.html", message="Something went wrong.. Plese try again later"))
                return resp
            else:
                if((email == docs[0][0]["_id"])):

                    my_document = my_database[email]
                    my_document['feedback'] = feedback
                    my_document.save() 

                    print(my_document)

                    content = "Thank you for your feedback!"
                    sendMail(email, "Dear user", "Feedback Submitted Successfully!", content)

                    resp = make_response(render_template("feedback.html", message="Thanks! Your feedback submitted successfully!!"))
                    return resp 
                else:
                    print("Invalid User")
                    resp = make_response(render_template("feedback.html", message="Something went wrong.. Plese try again later"))
                    return resp

    else:
        return render_template("login.html", message="You must be logged in first!")

@app.route("/feedbacks", methods=["GET"])
def adminDashboard():
    if request.cookies.get("isLoggedIn") == "True" and request.cookies.get("isAdmin") == "True":

        feedbacks = []

        for document in my_database:
            feedbacks.append(document)
            print(document)

        return render_template("feedbacks.html", feedbacks=feedbacks)
    else:
        return render_template("login.html", message="You must be logged in first!")


@app.route("/result-upload", methods=["GET"])
def resUpload():
    
    if request.cookies.get("isLoggedIn") == "True":

        filename = request.args.get("filename")

        webcam = cv2.VideoCapture("static/uploads/" + filename)

        if not webcam.isOpened():
            print("Could not open webcam")
            exit()

        t0 = time.time()
        centre0 = np.zeros(2)
        isDrowning = False

        while webcam.isOpened():

            status, frame = webcam.read()
            bbox, label, conf = cv.detect_common_objects(frame)

            if(len(bbox) > 0):
                bbox0 = bbox[0]
                centre = [0,0]
                
                centre = [(bbox0[0]+bbox0[2])/2, (bbox0[1]+bbox0[3])/2]

                hmov = abs(centre[0]-centre0[0])
                vmov = abs(centre[1]-centre0[1])

                x = time.time()

                threshold = 10

                if((hmov > threshold) or (vmov > threshold)):
                    print(x-t0, "s")
                    t0 = time.time()
                    isDrowning = False
                
                else:

                    print(x-t0, "s")
                    if((time.time() - t0) > 10):
                        isDrowning = True

                print("bbox: ", bbox, "Centre: ", centre, "Centre0: ", centre0)
                print("Is he drowning: ", isDrowning)

                centre0 = centre

            
                out = draw_bbox(frame, bbox, label, conf)

                cv2.imshow("Real-time object detection: ", out)
                
                if(isDrowning == True):
            
                    webcam.release()
                    cv2.destroyAllWindows()

                    playsound("http://localhost:5000/static/sound3.mp3")

                    return render_template("prediction.html", message="Emergency!!! The Person is Drowning")

                if(cv2.waitKey(1) & 0xFF ==  ord("q")):
                    break

        webcam.release()
        cv2.destroyAllWindows()

        return render_template("prediction.html")
    else:
        return render_template("login.html", message="You must be logged in first!")


if __name__ == '__main__':
    app.run(debug=True, static_url_path="static", static_folder='static', template_folder="templates")






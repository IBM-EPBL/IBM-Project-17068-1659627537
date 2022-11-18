import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

import os
from dotenv import load_dotenv, find_dotenv

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


# mail trigger after successful registration
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
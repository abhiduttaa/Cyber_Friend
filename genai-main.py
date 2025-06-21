import os
import vt
from flask import Flask, request, render_template, redirect, url_for, jsonify
import google.generativeai as genai
import uuid
import requests
import vt
import threading
from dotenv import load_dotenv
from PyPDF2 import PdfReader as rdr
#from vtClientTest import vtclienttest as vt
#from abstractapiEmailPhoneIP import absEmailPhoneIP as ae
#import json
#from gAi import net_scan as ns

load_dotenv()
f = 0
url_result = {}


def inc():
    global f
    f += 1
    return f


def confgemini():
    global model
    model = genai.GenerativeModel('gemini-1.5-flash')
    global chat
    chat = model.start_chat(history=[])
    #return chat


def textextraction(file):
    print("starting text extraction")
    if file.filename.endswith('.pdf'):
        print("extracting .pdf file")
        file_content = ''
        reader = rdr(file)
        num_page = len(reader.pages)
        for i in range(num_page):
            page = reader.pages[i]
            file_content = file_content + " " + (page.extract_text())
            print("pdf-text extraction done")
    elif file.filename.endswith('.txt'):
        print("extracting .txt file")
        file_content = file.read().decode('utf-8')
        print("text extraction done")
    else:
        file_content = ""
    print("all extraction complete!")
    print(file_content)
    return file_content


def collect_news():
    prompt = f"""Please generate current cybersecurity news and digital world news, presented in a simple yet 
    engaging and aesthetically pleasing manner. Focus on key developments, emerging threats, and significant 
    innovations, explaining them clearly without jargon, but with a touch of elegance in the language. The output 
    should be easily digestible for a general audience while still being informative and captivating."""
    response = model.generate_content(prompt).text
    return response

def extract_summary(data: dict) -> str:
    print("reached extract_summery")
    summary = data.get("attributes", {}).get("stats", {})
    return ", ".join(f"{k}: {v}" for k, v in summary.items())

def url_scan(url,task_id):
    api_key=os.getenv("VIRUSTOTAL_API_KEY")
    print(api_key)
    client=vt.Client(api_key)
    analysis=client.scan_url(url, wait_for_completion=True)
    print(analysis)
    client.close()
    result=extract_summary(analysis.to_dict())
    url_result[task_id]=result




app = Flask(__name__)

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure your GEMINI_API_KEY is correctly set in the .env file.")
    exit(1)


@app.route('/')
def home():
    return render_template('ds3.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_message = request.json.get('message')
    if not user_message:
        return ({"error": "No message provided"}), 400
    try:
        inc()
        if f == 1:
            confgemini()
            prompt = f"""You are a helpful AI assistant for cybersecurity. Your purpose is to provide information and assistance related to cybersecurity, file analysis, and general computer security topics.Avoid unrelated queries. Answer in very formal tone and avoid explanation if not requested.Answer the following user query:"""
            prompt += f"""{user_message}"""
            print(prompt)
            inc()
        else:
            prompt = f"""{user_message}"""
            print(prompt)
        response = chat.send_message(prompt)
        gemini_response = response.text
        return {"response_text": gemini_response}
    except Exception as q:
        print(f"Error during Gemini chat API call: {q}")
        return ({"error": "An error occurred during chat processing."}), 500

@app.route('/news-page')
def get_news():
    cyber_news = collect_news()
    return render_template('news.html', result=cyber_news)

@app.route('/analyze-net',methods=['POST'])
def serve_net_page():
    print("Successfull!")
    net_error=''
    net_result=''
    up_file=request.files['file']
    if up_file.filename.endswith('.txt'):
        file_content=up_file.read().decode['utf-8']
    elif up_file.filename.endswith('.pdf'):
        file_content=textextraction(up_file)
    else:
        file_content='No result!'
    prompt=(f"I have made a log file of my home network using scanning tools, i have received the following file. I "
            f"want you to read the file and make a general summery. When answering you should consider all known "
            f"patterns and signs of suspicious network activity and problems. Give me a overview within few lines. "
            f"Use enough spacing and styling in your content to make it better looking.{file_content}")
    response=model.generate_content(prompt).text
    return render_template('ds3.html',net_result=net_result,net_error=net_error)


#Note : Doubt : return none
@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    result = None
    error = None
    task_id = ''
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            error = 'No file part'
            return render_template('ds3.html', error=error)

        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            error = 'No selected file'
            return render_template('ds3.html', error=error)
        if file:
            model = genai.GenerativeModel('gemini-1.5-flash')
            file_content=textextraction(file)
            prompt = f"""
                        Analyze the following text, which could be an email, log, or general message, for signs of phishing or social engineering.
                        Focus on:
                        - Any attempts to create urgency, fear, or excitement.
                        - Requests for sensitive information (passwords, banking details).
                        - Suspicious links or file download prompts.
                        - Impersonation attempts (e.g., pretending to be a bank, IT support, or a known company).
                        - Grammatical errors, unusual phrasing, or generic greetings.
                        Give your response within 10 to 15 lines.
                        ---
                        {file_content}
                        ---
                        """
            response = model.generate_content(prompt)
            result = response.text
    return render_template('ds3.html', result=result, error="An error occurred in file analysis")


@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    error=None
    result=None
    url = request.form.get('url', '').strip()
    if not url :
        return render_template('ds3.html',error="no url given!")
    if url:
        task_id=str(uuid.uuid4())
        threading.Thread(target=url_scan,args=(url,task_id)).start()
        return redirect(url_for('scan_result',task_id=task_id))
    return render_template('ds3.html',result=result,error="Unexpectedly broken!")


@app.route('/scan-result/<task_id>')
def scan_result(task_id):
    result=''
    error=''
    sc_result=url_result.get(task_id)
    if sc_result:
        prompt=(f"Look at the following link analysis report and give me back a easily understandable output about the link.Check for "
                f"any malicious activity or any history that flags it as unsafe.Give me the category of the "
                f"link.--->{sc_result}")
        result=model.generate_content(prompt).text
    return render_template('ds3.html',result=result,error="error")

if __name__ == '__main__':
    app.run(debug=True)  #debug=True

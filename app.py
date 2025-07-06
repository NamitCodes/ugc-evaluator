from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANSWER_KEY_PATH = os.path.join(BASE_DIR, 'answer_key.json')
# Load your master answer key (already available)
with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

def extract_user_responses(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    user_responses = {}

    for question_div in soup.find_all("div", class_="question-pnl"):
        qid = None
        chosen = None

        menu_tbl = question_div.find("table", class_="menu-tbl")
        if not menu_tbl:
            continue

        # Extract all <td> tags and pair them as (label, value)
        tds = menu_tbl.find_all("td")
        for i in range(0, len(tds) - 1, 2):
            label = tds[i].get_text(strip=True)
            value = tds[i + 1].get_text(strip=True)

            if label == "Question ID :":
                qid = value
            elif label == "Chosen Option :":
                chosen = value

        if qid and chosen:
            user_responses[qid] = chosen

    return user_responses


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/check', methods=['POST'])
def check_score():
    url = request.form.get("ugcnet_url")

    try:
        response = requests.get(url, timeout=10)
        # print("HTML length:", len(response.text))  # Add this

        # with open("responses_raw.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)

        user_responses = extract_user_responses(response.text)

        print(user_responses)

        correct = wrong = unattempted = 0
        for qid, correct_ans in answer_key.items():
            user_ans = user_responses.get(qid, "")
            if user_ans == "":
                unattempted += 1
            elif user_ans == correct_ans:
                correct += 1
            else:
                wrong += 1

        score = correct * 2
        total = len(answer_key) * 2
        percentage = round((score / total) * 100, 2)

        return render_template("result.html", correct=correct, wrong=wrong,
                               unattempted=unattempted, score=score,
                               total=total, percentage=percentage)

    except Exception as e:
        return f"❌ Error fetching or processing the URL: {str(e)}", 500

if __name__ == '__main__':
    app.run()

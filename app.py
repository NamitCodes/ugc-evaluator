from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANSWER_KEY_PATH = os.path.join(BASE_DIR, 'answer_key.json')

# Load flat answer key
with open(ANSWER_KEY_PATH, 'r') as f:
    full_answer_key = json.load(f)

# Automatically split the first 50 as Paper 1, rest as Paper 2
answer_key_p1 = dict(list(full_answer_key.items())[:50])
answer_key_p2 = dict(list(full_answer_key.items())[50:])

def extract_user_responses(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    user_responses = {}

    for question_div in soup.find_all("div", class_="question-pnl"):
        qid = None
        chosen = None

        menu_tbl = question_div.find("table", class_="menu-tbl")
        if not menu_tbl:
            continue

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
        user_responses = extract_user_responses(response.text)

        def evaluate(key_subset):
            correct = wrong = unattempted = 0
            for qid, correct_ans in key_subset.items():
                user_ans = user_responses.get(qid, "")
                if user_ans == "":
                    unattempted += 1
                elif user_ans == correct_ans:
                    correct += 1
                else:
                    wrong += 1
            total = len(key_subset) * 2
            score = correct * 2
            percentage = round((score / total) * 100, 2)
            return correct, wrong, unattempted, score, total, percentage

        c1, w1, u1, s1, t1, p1 = evaluate(answer_key_p1)
        c2, w2, u2, s2, t2, p2 = evaluate(answer_key_p2)

        return render_template("result.html",
                               p1_correct=c1, p1_wrong=w1, p1_unattempted=u1, p1_score=s1, p1_total=t1, p1_percentage=p1,
                               p2_correct=c2, p2_wrong=w2, p2_unattempted=u2, p2_score=s2, p2_total=t2, p2_percentage=p2,
                               total_score=s1 + s2,
                               total_possible=t1 + t2,
                               total_percentage=round(((s1 + s2) / (t1 + t2)) * 100, 2)
                               )

    except Exception as e:
        return f"❌ Error: {str(e)}", 500

if __name__ == '__main__':
    app.run()

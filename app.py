import random
import csv
from flask import Flask, render_template, request, redirect, url_for, session
from parser import parse_questions
from flask import jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

app = Flask(__name__)
questions = parse_questions("81be766a.docx")

# 设置密钥用于加密 session
app.secret_key = 'Aa@asdas21398snjs'

# 配置 Session 存储到服务器的文件系统中
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session/'   # 自定义目录（可省略）
app.config['SESSION_PERMANENT'] = False               # 是否永久会话
app.config['SESSION_USE_SIGNER'] = True               # 是否对 session 内容签名
app.config['SESSION_COOKIE_NAME'] = 'my_session'      # 可自定义 cookie 名

# 打乱单选题选项顺序
def shuffle_options(q):
    if q["type"] != "single":
        return q
    # 拆分题干和选项
    parts = q["question"].split("\n")
    q_text = parts[0].strip()
    opts = [p.strip() for p in parts[1:] if p.strip().startswith(tuple("ABCD"))]
    correct = q["answer"].strip().upper()
    label_to_opt = {o[0]: o for o in opts if len(o) > 2}
    correct_text = label_to_opt.get(correct, "")
    shuffled = random.sample(opts, len(opts))
    q["question_text"] = q_text
    q["shuffled_options"] = shuffled
    q["correct_text"] = correct_text
    return q

@app.route("/")
def index():
    session["score"] = 0
    session["is_correct"] = 1
    session["current"] = 0
    session["total"] = len(questions)
    session["order"] = random.sample(range(len(questions)), len(questions))
    session["history"] = []
    return render_template("index.html", total=session["total"])

@app.route("/question", methods=["GET", "POST"])
def question():
    i = session.get("current", 0)
    if i >= len(questions):
        return redirect(url_for("result"))

    q_index = session["order"][i]
    q = questions[q_index].copy()
    q = shuffle_options(q)

    if request.method == "POST":
        user_ans = request.form.get("answer", "").strip().upper()
        correct_ans = q["answer"].strip().upper()
        session["is_correct"] = 0

        if q["type"] == "single":
            selected_text = next((opt for opt in q.get("shuffled_options", []) if opt.startswith(user_ans)), "")
            correct_text = q["correct_text"]
            correct = selected_text.strip() == q["correct_text"].strip()
            user_ans = selected_text[3:]
            correct_ans = correct_text[3:]
        else:
            correct = user_ans == correct_ans

        if correct:
            session["score"] += 1
            session["is_correct"] = 1

        # 保存答题记录
        session["history"].append({
            "题目": q["question_text"] if "question_text" in q else q["question"],
            "你的答案": user_ans,
            "正确答案": correct_ans,
            "是否正确": "√" if correct else "×"
        })

        session["current"] += 1
        return redirect(url_for("question"))

    answered = session["current"]
    correct = session["score"]
    wrong = answered - correct
    error_rate = round((correct / answered) * 100, 2) if answered else 0

    if session["is_correct"] == 0:
        last_answer = session["history"][-1]
    else:
        last_answer = ""

    return render_template("question.html", q=q, idx=i+1, total=session["total"], error_rate=error_rate, correct=correct, error=wrong, last_answer=last_answer)

@app.route("/result")
def result():
    score = session.get("score", 0)
    total = session.get("total", 1)
    rate = round(score / total * 100, 2)
    passed = rate >= 70

    # 导出CSV
    with open("result.csv", "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["题目", "你的答案", "正确答案", "是否正确"])
        writer.writeheader()
        writer.writerows(session.get("history", []))


    return render_template("result.html", score=score, total=total, rate=rate, passed=passed)

@app.route("/get_result_csv")
def get_result_csv():
    import io
    import csv

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["题目", "你的答案", "正确答案", "是否正确"])
    writer.writeheader()
    writer.writerows(session.get("history", []))
    csv_data = output.getvalue()
    output.close()

    return jsonify({"csv": csv_data})

@app.before_request
def make_session_permanent():
    session.permanent = True

if __name__ == "__main__":
    Session(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.run(host="0.0.0.0", port=5001, debug=True)

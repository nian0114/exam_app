from docx import Document
import re
import random

def parse_questions(docx_path):
    document = Document(docx_path)
    questions = []
    mode = None
    buffer = []

    for para in document.paragraphs:
        text = para.text.strip()

        if not text:
            continue
        if text.startswith("一、判断题"):
            mode = "judge"
            continue
        if text.startswith("二、单选题"):
            mode = "single"
            continue

        # 判断题格式：( √ )1. ...
        if mode == "judge":
            ans = '√' in text
            content = text[5:]
            questions.append({"type": "judge", "question": content, "answer": "√" if ans else "×"})

        # 单选题（题干和答案在一段内，使用参考答案标记）
        elif mode == "single":
            if "（65）" in text or  "（66）" in text  or  "（67）" in text  or  "（68）" in text   or  "（69）" in text   or  "（70）" in text :
                text = text[4:]

            buffer.append(text)

            if "参考答案" in text:
                if len(buffer) >= 6:
                    question_text = buffer[0]
                    options = buffer[1:5]
                    answer_line = buffer[5]

                    # 匹配原始正确答案，如：参考答案：B
                    ans_match = re.search(r'参考答案[:：]\s*([A-D])', answer_line)
                    correct_label = ans_match.group(1).strip().upper()

                    if not ans_match:
                        buffer = []
                        continue

                    shuffled_options=[]
                    new_label = None
                    for i, opt in enumerate(options):
                        shuffled_options.append("{}. {}".format(str(chr(ord('A') + i)), opt))

                    formatted = question_text + "\n" + "\n".join(shuffled_options)
                    questions.append({
                        "type": "single",
                        "question": formatted.strip(),
                        "answer": correct_label
                    })
                buffer = []

    return questions

import requests
from flask import Flask, render_template, request
import openai
import os

app = Flask(__name__)


def chat_with_gpt(user_input=None, conversation_history=None):
    openai.api_key = os.environ["OPENAI_API_KEY"]
    conversation_history = conversation_history or [{"role": "system", "content": "あなたはproの記者です。"}]

    if user_input:
        conversation_history.append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=500,
            temperature=0.8
        )
        chat_gpt_response = response["choices"][0]["message"]["content"]
        conversation_history.append({"role": "assistant", "content": chat_gpt_response})
        return chat_gpt_response, conversation_history
    else:
        return None, conversation_history


def search_google_cse(query, api_key_google_cse, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key_google_cse,
        "cx": cse_id,
        "q": query,
        "tbm": "nws",
        "sort": "date"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        return None


api_key = os.environ["OPENAI_API_KEY"]
api_key_google_cse = os.environ["GOOGLE_API_KEY"]
cse_id = os.environ["GOOGLE_CSE_ID"]
conversation_history = None


@app.route("/", methods=["GET", "POST"])
def index():
    global conversation_history
    if request.method == "GET":
        chat_history = "何を検索しますか？先頭に「ニュース検索」とつけ、スペースを一つ空けて質問してください。｢終了｣と入力すると終了します。"
        return render_template("index.html", chat_history=chat_history)

    if request.method == "POST":
        user_input = request.form["user_input"]
        if user_input.lower() in ["終了"]:
            chat_history = "あなた: " + user_input + "\nChatGPT: さようなら！またお会いしましょう！"
            conversation_history = None
            return render_template("index.html", chat_history=chat_history)

        if "ニュース検索" in user_input:
            query = user_input.replace("ニュース検索", "").strip()
            search_results = search_google_cse(query, api_key_google_cse, cse_id)
            search_snippets = []
            for i, result in enumerate(search_results[:3]):
                search_snippets.append(result['title'] + ' - ' + result['link'])
            gpt_query = f"{user_input} 検索結果: {' '.join(search_snippets)}"
            chat_gpt_response, conversation_history = chat_with_gpt(gpt_query, conversation_history)
            chat_history = f"あなた: {user_input}\nChatGPT: {chat_gpt_response}"
        else:
            chat_gpt_response, conversation_history = chat_with_gpt(user_input, conversation_history)
            chat_history = f"あなた: {user_input}\nChatGPT: {chat_gpt_response}"

        return render_template("index.html", chat_history=chat_history)

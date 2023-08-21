import time
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from flask_cors import cross_origin
import os
import json
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

# NLTK's Pretrained Model import
load_dotenv()
nltk.download("vader_lexicon")
sid = SentimentIntensityAnalyzer()

import openai

# Openai Environment Setting
apikey = os.environ["API_KEY"]
openai.api_key = apikey

# Pattern Json Input
json_intents = {}
with open("pattern.json", "r") as json_file:
    json_intents = json.load(json_file)

# Flask App Setting
app = Flask(__name__)
CORS(app)

# Bot 2 Question Sentences
gretting_question = "Hi this is name from healthcare benefit. How are you today?"
medicare_question = "I'm calling because the updated plan for Medicare has been released and it may give you some better access to things like dental vision hearing and over-the-counter benefits. Now I believe you do have Medicare part a and B correct?"


# Pattern Matching Intent Analysis
def find_pattern(sentence):
    for intent_data in json_intents["intents"]:
        for pattern in intent_data["patterns"]:
            if pattern.lower() in sentence.lower():
                matches = re.findall(pattern, sentence)
                if matches:
                    return intent_data["tag"]
    return "not exist"


# NLTK's sentiment Analysis Model using
def analyze_sentiment(text):
    sentiment_score = sid.polarity_scores(text)
    return sentiment_score["compound"]


# DNC Specification
def indentify_dnc(sentence):
    if "not" in sentence and "call" in sentence:
        return True
    if "stop" in sentence and "call" in sentence:
        return True
    if "no" in sentence and "call" in sentence:
        return True
    return False
    get_intent_from_question_response


# Verify that The Language is english or not.
def is_english_string(input_string):
    english_chars = re.compile(r"^[a-zA-Z0-9\s]+$")
    return bool(english_chars.match(input_string))


# Removing Sentence Symbols
def remove_sentence_symbols(input_string):
    sentence_symbols = [".", "!", "?", ","]
    for symbol in sentence_symbols:
        input_string = input_string.replace(symbol, "")
    return input_string


# Get response from openai chatgpt
def get_chatgpt_response(prompt):
    res = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        stop=None,
        temperature=0.2,
        n=1,
        stream=False,
    )
    answer = res["choices"][0]["text"].strip()
    return answer


# Getting The client's age (openai chatgpt used because the customer's response is variety)
def get_age(response):
    prompt = f"""
      Your task is to find out the age from the following sentence. if the age is not mentioned in the following sentence, the answer is 'not mentioned'.
      "{response}
    """
    intent = get_chatgpt_response(prompt)
    return intent


#  Verify that the customer has got disability
def get_disability(response):
    prompt = f"""
      Your task is to find out the man who is speaking the following sentence have disability or not. 
      if have disbility, the answer is 'YES', if else, the answer is 'NO'.
      sentence: {response}
    """
    intent = get_chatgpt_response(prompt)
    return intent


#  Getting Last Chatgpt Part
def get_last_chatgpt_intent(question, response):
    answer = get_age(response)

    prompt = f"""
      This is a call for selling medicare insurance. which is for people over 60 year old or people who not 60 but have disability . 
      so our criteria is to qualify people who have already medicare A, Medicare B or both of them. Or people who have medicaid. 
      The question is as below.
      {question}
      The reponse to my question is below.
      {response}
      I want to know what this reponse's intent is by some categories using understanding of the reponse with question-response pair like yes or no.
      possible answers are below.
      - YES
      - NO
      - don't call (DNC)
      - call back again (CB)

      Otherwise the category is 'NO'
    
      Criteria is:

      Interested people -  YES
      need insurance - YES
      have medicare - YES
      have disability - YES
      people who is kidding bot - NO
      people who don't want to talk , abuses or want to remove from the list - DNC
      can't speak english - LB
      want to speak in other language instead of english - LB

      Not interested people - NO
      People don't have medicare - NO
      age group barrier - AG

      Please give me the category of the reponse.
      Output must be the following format.
      { {'intent': 'category'} }
      """

    intent = get_chatgpt_response(prompt)
    return intent


# Special Part
def get_intent_in_special_case(lower):
    if "hi" == lower:
        return "YES"
    if "not" in lower:
        return "NO"
    elif "no" in lower:
        return "NO"
    else:
        return "NO SPEC"


# Making Logs
def make_logs(question, response, intent):
    print(question, response)


# Caching responses
def caching_intents(question, response, intent):
    print(response, intent)


# Getting Total Intent
def get_total_intent(question, response):
    # ------------------- Response Preprocessing For Specification case --------------------------------------
    # Some times (cant == can't)
    if " cant " in response:
        response.replace(" cant ", " can not ")
    # Replave 've to have
    response.replace("'ve", " have")
    # Replace 't to not
    response = response.replace("'t", " not")

    # The customer's response is English or not
    if is_english_string(response) == False:
        return "LB"
    # lower the response
    lower = response.lower()

    # ------------------- Getting Intent  --------------------------------------
    # Maching Pattern -----------------------------
    intent = find_pattern(lower)
    if intent != "not exist":
        return intent

    # dnc indentify exact specifically ----------------------------
    dnc = indentify_dnc(response)
    if dnc == True:
        return "DNC"

    # Sentiment Analysis -----------------------------
    sentiment_score = analyze_sentiment(lower)

    # Specific Intent >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    specific_intent = get_intent_in_special_case(lower)
    if specific_intent != "NO SPEC":
        return specific_intent
    # Sentiment Analysis Part: if the score > 0.2, the sentiment is good : YES >>>>>>>>>>>>>>
    elif sentiment_score >= 0.2:
        return "YES"
    else:
        # I have used Chatgpt in the last for saving openai tokens -----------------------------------
        # Getting age > 60 or not
        answer = get_age(response)
        if answer != "not mentioned":
            age = int(answer)
            if age >= 60:
                return "YES"
        # Getting disability or not >>>>>>>>>>>>>>>>>>>>>
        if get_disability(response) == "YES":
            return "YES"

        # Getting intent from LAST chatgpt part >>>>>>>>>>>>>>>>>>>
        intent = get_last_chatgpt_intent(question, lower)

        intent = intent.replace("'", '"')
        data = json.loads(intent)
        intent_value = data["intent"]
        if intent_value != "fallback":
            return intent_value
        # If the sentiment is not Good >>>>>>>>>>>>>>>>>>>>>
        if sentiment_score <= -0.2:
            return "NO"
        return "FALLBACK"


# GUI Part
@app.route("/", methods=["GET", "POST"])
def sentiment():
    if request.method == "POST":
        question_type = request.json.get("question")
        response = request.json.get("response")
        print(response)

        response_temp = response
        # Question Exchangin
        question = ""
        if question_type == "gretting":
            question = gretting_question
        else:
            question = medicare_question
        # Remove Sentence Symbols
        response = remove_sentence_symbols(response)
        intent = get_total_intent(question, response)
        print(intent)

        # Make Log and cache
        make_logs(question, response, intent)
        caching_intents(question, response, intent)

        return jsonify({"response": response_temp, "intent": intent})
    return render_template("index.html")


# API Request Part : GET Request
@app.route("/api", methods=["GET"])
def sentiment1():
    question_type = request.args.get("question")
    response = request.args.get("response")
    if question_type != "" and response != "":
        response_temp = response
        print(response)

        # Question Exchanging
        question = ""
        if question_type == "greeting":
            question = gretting_question
        else:
            question = medicare_question
        intent = get_total_intent(question, response)

        # Make Log and cache
        make_logs(request, response, intent)
        caching_intents(request, response, intent)

        return jsonify({"response": response_temp, "intent": intent})
    else:
        return "Please input exactly."


# Running Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

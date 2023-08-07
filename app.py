import time
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from flask_cors import cross_origin
import os
import json
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# nltk.download("vader_lexicon")
nltk.data.path.append("/home/TOPTOP/nltk_data")


import openai

apikey = "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"
openai.api_key = apikey

json_intents = {
    "intents": [
        {
            "tag": "dnc",
            "patterns": [
                "fuck off",
                "stop calling",
                "stop calling me",
                "get the fuck out, I do not want you talking to me",
                "you're an idiot, who the fuck care if you live or die, go to hell",
                "scammers",
                "don't be a fool",
                "leave me alone, I do not want your calls anymore",
                "go to hell",
                "shut up",
                "take me off your list",
                "not interested",
                "no i d like for you not to call me ever again",
                "nope i ve gotten insurance",
                "take me off the list how about that",
                "fucker",
                "mother fucker",
                "fuck yourself",
                "bitch",
                "whore",
                "suck my dick",
                "dick",
            ],
            "responses": ["ok I'll put you on dnc list"],
            "context": [""],
        },
        {
            "tag": "no",
            "patterns": [
                "no",
                "now",
                "nope",
                "I dont want",
                "nah",
                "no thank you",
                "i don't think so",
                "no i dont want",
                "i do not want",
                "i dont want",
                "not interested",
                "cannot",
                "you cannot",
                "No I am not interested in whatever you're selling",
                "never",
                "satisfied with your message",
                "i have it",
                "press one",
                "press two",
                "press three",
                "press four",
                "press five",
                "press six",
                "press seven",
                "press eight",
                "press nine",
                "no i m all set",
                "if you re satisfied with the message",
                "one for more options",
                "i m busy righs now",
                "you may hang up or across the county for more options",
                "if you are satisfied with your message press one to listen to your message press two to erase and re record press three to continue recording where you left off press four",
                "damn",
                "the pound key",
                "just hang up",
                "already have a plan",
                "i m sorry",
                "i know",
                "this is a business",
                "excuse me",
                "i don't think i qualify",
                "i don't think",
                "we won t be shown",
                "i'm covered",
                "i don't need none",
                "mm no",
                "mm mm no",
                "english",
                "i don't speak english",
                "i can't talk in english",
                "no english",
                "sorry no",
                "wow",
                "i gotta find it on my own",
                "i got a plan",
                "no not at all",
                "speak to a sales associate press two",
            ],
            "responses": ["ok thanks for your time, have a great day"],
            "context": [""],
        },
        {
            "tag": "who",
            "patterns": [
                "who are you",
                "what is your name",
                "what is your company name",
                "who is this",
                "tell me about you",
                "what's your company name",
                "from where you are calling",
                "which company you are from",
                "tell me about company ",
                "what you guys do",
                "hello",
                "hi",
                "oh hi",
                "oh hello",
                "hi there",
                "i can't hear you",
                "what are you saying",
                "can you repeat",
                "sorry what",
                "what is this",
                "what",
                "mm",
                "hmm",
                "more",
                "who",
                "who are you calling",
            ],
            "responses": ["My name is Amy and I am calling from healthcare"],
            "context": [""],
        },
        {
            "tag": "why",
            "patterns": [
                "why are you calling me",
                "why",
                "what is purpose",
                "what can i do for you",
                "what a disregard",
                "what is this regarding",
                "what is this about",
            ],
            "responses": ["I am calling you about health insurance"],
            "context": [""],
        },
        {
            "tag": "yes",
            "patterns": [
                "yes",
                "yes",
                "cool",
                "cool",
                "fine",
                "good",
                "more",
                "okay",
                "sure",
                "yeah",
                "great",
                "ah yes",
                "correct",
                "oh fine",
                "ok fine",
                "you can",
                "go ahead",
                "ofcourse",
                "yes i do",
                "i want it",
                "i think so",
                "i think yes",
                "ok go ahead",
                "yeah go ahead",
                "i will love to",
                "lets go for it",
                "yes thats fine",
                "I am doing good",
                "i can do it now",
                "okay talk to me",
                "i am doing great",
                "ok transfer my call",
                "i'm good how are you",
                "i'm very well thanks",
                "ok can u transfer now",
                "i'm fine what you need",
                "not too bad how are you",
                "i'm fine what do you need",
            ],
            "responses": [
                "ok please hold while i transfer your call",
                "ok transferring your call to enrollment specialist",
                "ok wait while i connect to you for more options",
            ],
            "context": [""],
        },
        {
            "tag": "later",
            "patterns": ["later", "yes later", "some other time"],
            "responses": [
                "Sure i will schedule a callback later. thanks bye",
                "ok later we can do it. thanks bye",
                "ok some other time.thanks bye",
            ],
            "context": [""],
        },
    ]
}


app = Flask(__name__)
CORS(app)

gretting_question = "Hi this is name from healthcare benefit. How are you today?"
medicare_question = "I’m calling because the updated plan for Medicare has been released and it may give you some better access to things like dental vision hearing and over-the-counter benefits. Now I believe you do have Medicare part a and B correct?"


def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentiment_score = sid.polarity_scores(text)
    return sentiment_score["compound"]


def find_intent(sentence):
    for intent_data in json_intents["intents"]:
        for pattern in intent_data["patterns"]:
            if pattern.lower() in sentence.lower():
                matches = re.findall(pattern, sentence)
                if matches:
                    return intent_data["tag"]
    return "not exist"


def indentify_dnc(sentence):
    if "not" in sentence and "call" in sentence:
        return True
    if "stop" in sentence and "call" in sentence:
        return True
    if "no" in sentence and "call" in sentence:
        return True
    return False


def assign_intent_with_sentiment(response):
    intent = find_intent(response)

    dnc = indentify_dnc(response)
    if dnc == True:
        return "dnc"
    if intent != "not exist":
        return intent
    sentiment_score = analyze_sentiment(response)
    if sentiment_score >= 0.2:
        return "yes"
    elif sentiment_score <= -0.2:
        return "no"
    elif "why" in response:
        return "yes"
    elif "who" in response:
        return "who"
    elif "later" in response:
        return "later"
    else:
        return "fallback"


@app.route("/api/intent", methods=["GET"])
@cross_origin()
def intent():
    question = request.args.get("question")
    response = request.args.get("response")

    response_temp = response

    question1 = ""
    if question == "gretting":
        question1 = gretting_question
    else:
        question1 = medicare_question
    response = response.replace("'t", " not")
    intent = assign_intent_with_sentiment(response)

    return {"response": response, "intent": intent}


@app.route("/", methods=["GET", "POST"])
def hello():
    if request.method == "POST":
        print("Hello")
        # Get the form data from the request
        question = request.json.get("question")
        response = request.json.get("response")

        response = response.replace("'t", " not")
        intent = assign_intent_with_sentiment(response)

        return jsonify({"intent": intent})
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2000, debug=True)

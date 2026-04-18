from flask import Flask, render_template, send_file
import csv
import threading
from scraper import run_scraper

app = Flask(__name__)

def load_data():
    data = []
    try:
        with open("db.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except:
        pass
    return data

@app.route("/")
def index():
    data = load_data()
    data = sorted(data, key=lambda x: int(x["score"]), reverse=True)
    return render_template("index.html", leads=data)

@app.route("/run")
def run():
    threading.Thread(target=run_scraper).start()
    return "🚀 Scraping lancé en arrière-plan"

@app.route("/download")
def download():
    return send_file("db.csv", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

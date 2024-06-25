import os
import time
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import dotenv
from tenacity import retry, wait_fixed, stop_after_attempt
import kernel

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("PG_CONNECT") + "?connect_timeout=10"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    date_processed = db.Column(db.Date, nullable=False)

@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def process_tasks():
    with app.app_context():
        tasks = Site.query.filter_by(status='В очереди на обработку').all()
        print(len(tasks))
        for task in tasks:
            print(task.url)
            task.status = kernel.execute(task.url)
            task.date_processed = datetime.now()
            db.session.commit()
        print(f'Processed {len(tasks)} tasks at {datetime.now()}')

if __name__ == '__main__':
    while True:
        try:
            process_tasks()
        except Exception as e:
            print(f"Error processing tasks: {e}")
        time.sleep(60)

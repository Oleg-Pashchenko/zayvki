import os
import time
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import dotenv

import kernel

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("PG_CONNECT")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    date_processed = db.Column(db.Date, nullable=False)



def process_tasks():
    with app.app_context():
        tasks = Site.query.filter_by(status='В очереди на обработку').all()
        for task in tasks:
            task.status = kernel.execute(task)
            task.date_processed = datetime.now()
            db.session.commit()
        print(f'Processed {len(tasks)} tasks at {datetime.now()}')


if __name__ == '__main__':
    while True:
        process_tasks()
        time.sleep(60)

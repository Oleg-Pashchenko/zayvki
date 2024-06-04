from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io
import dotenv
import os

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

    def __init__(self, url, status, date_processed):
        self.url = url
        self.status = status
        self.date_processed = date_processed


# Инициализация базы данных
with app.app_context():
    db.create_all()


def get_status_counts():
    status_counts = {
        'В очереди на обработку': Site.query.filter_by(status='В очереди на обработку').count(),
        'Форма найдена и сообщение отправлено': Site.query.filter_by(
            status='Форма найдена и сообщение отправлено').count(),
        'Не удалось найти форму': Site.query.filter_by(status='Не удалось найти форму').count(),
        'Форма найдена, не удалось отправить сообщение': Site.query.filter_by(
            status='Форма найдена, не удалось отправить сообщение').count()
    }
    return status_counts


@app.route('/')
def index():
    per_page = 10
    current_page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('filter', '', type=str)
    search_url = request.args.get('search', '', type=str)

    query = Site.query
    if filter_status:
        query = query.filter_by(status=filter_status)
    if search_url:
        query = query.filter(Site.url.ilike(f'%{search_url}%'))

    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page
    sites = query.paginate(page=current_page, per_page=per_page, error_out=False).items
    status_counts = get_status_counts()

    return render_template('index.html',
                           sites=sites,
                           current_page=current_page,
                           total_pages=total_pages,
                           filter=filter_status,
                           status_counts=status_counts)


@app.route('/add-site', methods=['POST'])
def add_site():
    site_url = request.form.get('siteUrl')
    if site_url:
        new_site = Site(
            url=site_url,
            status='В очереди на обработку',
            date_processed=datetime.now()
        )
        db.session.add(new_site)
        db.session.commit()
        flash(f'Сайт {site_url} был успешно добавлен!', 'success')
    else:
        flash('Не удалось добавить сайт. Попробуйте снова.', 'danger')
    return redirect(url_for('index'))


@app.route('/upload-file', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename.endswith('.txt'):
        file_content = file.read().decode('utf-8')
        uploaded_sites = file_content.splitlines()
        for url in uploaded_sites:
            new_site = Site(
                url=url,
                status='В очереди на обработку',
                date_processed=datetime.now()
            )
            db.session.add(new_site)
        db.session.commit()
        flash(f'Файл загружен и {len(uploaded_sites)} сайтов было добавлено!', 'success')
    else:
        flash('Загрузите корректный файл .txt', 'danger')
    return redirect(url_for('index'))


@app.route('/download_status/<status>')
def download_status(status):
    sites = Site.query.filter_by(status=status).all()
    file_content = "\n".join(site.url for site in sites)
    return send_file(
        io.BytesIO(file_content.encode()),
        as_attachment=True,
        download_name=f'{status}.txt',
        mimetype='text/plain'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

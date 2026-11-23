import os
import json
import uuid
import hashlib
import mimetypes
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_flash_messages'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')
METADATA_FILE = os.path.join(BASE_DIR, 'metadata.json')

FORBIDDEN_EXTENSIONS = {'.exe', '.sh', '.php', '.js', '.bat', '.cmd', '.msi', '.py'}
FORBIDDEN_MIMETYPES = {
    'application/x-msdownload',
    'application/x-sh',
    'application/x-httpd-php',
    'application/javascript',
    'text/javascript'
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_metadata():
    """Загружает метаданные из JSON-файла при старте/обращении."""
    if not os.path.exists(METADATA_FILE):
        return []
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_metadata(data):
    """Сохраняет метаданные в JSON-файл."""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def calculate_md5(file_stream):
    """Вычисляет MD5-хэш файла потоково."""
    hash_md5 = hashlib.md5()
    file_stream.seek(0)
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hash_md5.update(chunk)
    file_stream.seek(0)
    return hash_md5.hexdigest()


def is_file_allowed(filename, file_stream):
    """Проверяет расширение и MIME-тип файла."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext in FORBIDDEN_EXTENSIONS:
        return False, f"Загрузка файлов с расширением '{ext}' запрещена."

    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type in FORBIDDEN_MIMETYPES or file_stream.mimetype in FORBIDDEN_MIMETYPES:
        return False, f"Запрещенный MIME-тип файла ({guessed_type or file_stream.mimetype})."

    return True, ""


@app.route('/', methods=['GET', 'POST'])
def index():
    files_data = load_metadata()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Ошибка: Файл не найден в запросе.', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Ошибка: Вы не выбрали файл для загрузки.', 'error')
            return redirect(request.url)

        original_filename = file.filename
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        allowed, reason = is_file_allowed(original_filename, file)
        if not allowed:
            flash(f'Ошибка безопасности: {reason}', 'error')
            return redirect(request.url)

        file_md5 = calculate_md5(file)
        if any(item['md5'] == file_md5 for item in files_data):
            flash('Ошибка: Такой файл уже был загружен ранее (дубликат по MD5).', 'error')
            return redirect(request.url)

        file_uuid = uuid.uuid4().hex
        sub_dir_1 = file_uuid[:2]
        sub_dir_2 = file_uuid[2:4]
        new_filename = f"{file_uuid}{ext}"

        target_dir = os.path.join(UPLOAD_FOLDER, sub_dir_1, sub_dir_2)
        os.makedirs(target_dir, exist_ok=True)

        full_save_path = os.path.join(target_dir, new_filename)
        relative_server_path = f"/upload/{sub_dir_1}/{sub_dir_2}/{new_filename}"

        file.save(full_save_path)

        file_record = {
            'uuid_name': new_filename,
            'original_name': original_filename,
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'server_path': relative_server_path,
            'extension': ext if ext else 'без расширения',
            'md5': file_md5
        }

        files_data.append(file_record)
        save_metadata(files_data)

        flash(f'Файл "{original_filename}" успешно загружен!', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', files=reversed(files_data))


if __name__ == '__main__':
    app.run(debug=True)

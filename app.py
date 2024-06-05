import sqlite3
import io
import matplotlib.pyplot as plt
import tempfile

from flask import Flask, render_template, send_file, redirect, request, url_for

app = Flask(__name__)
DATABASE = 'todo.db'


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         title TEXT NOT NULL,
                         completed BOOLEAN NOT NULL CHECK (completed IN (0, 1)),
                         deleted BOOLEAN NOT NULL CHECK (deleted IN (0, 1)),
                         date DATE NOT NULL)''')


@app.route('/')
def index():
    with sqlite3.connect(DATABASE) as conn:
        tasks = conn.execute(
            'SELECT * FROM tasks WHERE deleted = 0 ORDER BY date DESC').fetchall()
    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    date = request.form['date']
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            'INSERT INTO tasks (title, completed, deleted, date) VALUES (?, ?, ?, ?)', (title, False, False, date))
    return redirect(url_for('index'))


@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
    return redirect(url_for('index'))


@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('UPDATE tasks SET deleted = 1 WHERE id = ?', (task_id,))
    return redirect(url_for('index'))


@app.route('/completed')
def completed_tasks():
    with sqlite3.connect(DATABASE) as conn:
        tasks = conn.execute(
            'SELECT * FROM tasks WHERE completed = 1 AND deleted = 0').fetchall()
    return render_template('completed.html', tasks=tasks)


@app.route('/statistics')
def statistics():
    with sqlite3.connect(DATABASE) as conn:
        total_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE deleted = 0').fetchone()[0]
        completed_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE completed = 1 AND deleted = 0').fetchone()[0]
        current_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE completed = 0 AND deleted = 0').fetchone()[0]
        deleted_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE deleted = 1').fetchone()[0]
    return render_template('statistics.html', total_tasks=total_tasks, completed_tasks=completed_tasks,
                           current_tasks=current_tasks, deleted_tasks=deleted_tasks)


def update_image():
    with sqlite3.connect(DATABASE) as conn:
        completed_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE completed = 1 AND deleted = 0').fetchone()[0]
        current_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE completed = 0 AND deleted = 0').fetchone()[0]
        deleted_tasks = conn.execute(
            'SELECT COUNT(*) FROM tasks WHERE deleted = 1').fetchone()[0]

    labels = []
    sizes = []
    if completed_tasks > 0:
        labels.append('Completed Tasks')
        sizes.append(completed_tasks)
    if current_tasks > 0:
        labels.append('Current Tasks')
        sizes.append(current_tasks)
    if deleted_tasks > 0:
        labels.append('Deleted Tasks')
        sizes.append(deleted_tasks)

    colors = ['#4caf50', '#2196f3', '#f44336']

    plt.figure(figsize=(10, 10), dpi=100)
    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=140)
    plt.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    return img


@app.route('/filter', methods=['POST'])
def filter_tasks():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    with sqlite3.connect(DATABASE) as conn:
        tasks = conn.execute(
            'SELECT * FROM tasks WHERE date BETWEEN ? AND ? AND deleted = 0 ORDER BY date DESC', (start_date, end_date)).fetchall()
    return render_template('filtered_tasks.html', tasks=tasks)


@app.route('/generate_chart')
def generate_chart():
    img = update_image()

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(img.read())
    temp_file.close()

    return send_file(temp_file.name, mimetype='image/png')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, threaded=True)

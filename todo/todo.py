from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from todo.auth import login_required
from todo.db import get_db

bp = Blueprint('todo', __name__)

@bp.route('/')
def index():
    db = get_db()
    tasks = db.execute(
        'SELECT t.id, t.task, t.creation_time, t.expiration_date, t.user_id, u.username'
        ' FROM tasks t JOIN users u ON t.user_id = u.id'
        ' ORDER BY t.creation_time DESC'
    ).fetchall()
    return render_template('todo-app/index.html', tasks=tasks)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        task = request.form['task']
        expiration_date = request.form['expiration_date']
        error = None

        if not task:
            error = 'Task is required.'
        
        if not expiration_date:
            error = 'Expiration date is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO tasks (task, expiration_date, user_id)'
                ' VALUES (?, ?, ?)',
                (task, expiration_date, g.user['id'])
            )
            db.commit()
            return redirect(url_for('todo.index'))

    return render_template('todo-app/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    task = get_task(id)

    if request.method == 'POST':
        task = request.form['task']
        expiration_date = request.form['expiration_date']
        error = None

        if not task:
            error = 'Task is required.'
        
        if not expiration_date:
            error = 'Expiration date is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE tasks SET task = ?, expiration_date = ?'
                ' WHERE id = ?',
                (task, expiration_date, id)
            )
            db.commit()
            return redirect(url_for('todo.index'))

    return render_template('todo-app/update.html', task=task)


def get_task(id, check_author=True):
    task = get_db().execute(
        'SELECT t.id, t.task, t.creation_time, t.expiration_date, t.user_id, u.username'
        ' FROM tasks t JOIN users u ON t.user_id = u.id'
        ' WHERE t.id = ?',
        (id,)
    ).fetchone()

    if task is None:
        abort(404, f"Task id {id} doesn't exist.")

    if check_author and task['user_id'] != g.user['id']:
        abort(403)

    return task


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_task(id)
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('todo.index'))
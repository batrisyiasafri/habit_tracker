from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from datetime import datetime
from datetime import timedelta
from flask_migrate import Migrate
from flask import jsonify
from calendar import monthrange, weekday

app = Flask(__name__)
app.secret_key = 'secret-me'

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# setup database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# models
class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, default=datetime.utcnow)
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, nullable=False)
    
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade="all, delete")

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), default='done')



with app.app_context():
    db.create_all()

# to index page
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('refresh'))

    habits = Habit.query.filter_by(user_id=session['user_id']).all()
    today = date.today()
    done_today = set()
    habit_stats = {}

    for habit in habits:
        log_dates = [log.date for log in habit.logs]
        if today in log_dates:
            done_today.add(habit.id)
        total, current, longest = calculate_streaks(log_dates)
        habit_stats[habit.id] = {
            'total': total,
            'current': current,
            'longest': longest
        }

    return render_template(
        'index.html', 
        habits=habits, 
        today=today, 
        done_today=done_today,
        habit_stats=habit_stats
        )

# add habit
@app.route('/add_habit', methods=['POST'])
def add_habit():
    name = request.form.get('habit_name')
    if name:
        new_habit = Habit(name=name, user_id=session['user_id'])
        db.session.add(new_habit)
        db.session.commit()
    return redirect(url_for('index'))

# edit habit
@app.route('/edit_habit/<int:habit_id>', methods=['GET', 'POST'])
def edit_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    if request.method == 'POST':
        new_name = request.form.get('habit_name')
        if new_name:
            habit.name = new_name
            db.session.commit()
            flash('Habit updated successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Habit name cannot be empty', 'warning')
    return render_template('edit_habit.html', habit=habit)

# delete habit
@app.route('/delete_habit/<int:habit_id>')
def delete_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    if habit.user_id != session.get('user_id'):
        flash("You don't have permission to delete this habit.", "error")
        return redirect(url_for('index'))

    db.session.delete(habit)
    db.session.commit()
    flash("Habit deleted successfully.", "danger")
    return redirect(url_for('index'))

# mark done in habit
@app.route('/mark_done/<int:habit_id>')
def mark_done(habit_id):
    today = date.today()
    log = HabitLog(habit_id=habit_id, date=today)
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('index'))

# undo mark done
@app.route('/toggle_done/<int:habit_id>', methods=['POST'])
def toggle_done(habit_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    status = data.get('status')
    today = date.today()

    existing_log = HabitLog.query.filter_by(habit_id=habit_id, date=today).first()

    if status == 'done':
        if not existing_log:
            new_log = HabitLog(habit_id=habit_id, date=today, status='done')
            db.session.add(new_log)
        else:
            existing_log.status = 'done'

    elif status == 'skipped':
        if not existing_log:
            new_log = HabitLog(habit_id=habit_id, date=today, status='skipped')
            db.session.add(new_log)
        else:
            existing_log.status = 'skipped'

    elif status == 'undone':
        if existing_log:
            db.session.delete(existing_log)
        else:
            return jsonify({'success': True, 'marked': status})

    db.session.commit()
    return jsonify({'success': True, 'marked': status})

    
# habit history
@app.route('/habit_history/<int:habit_id>')
def habit_history(habit_id):
    habit = Habit.query.get_or_404(habit_id)

    # year and month but default to today
    year = request.args.get('year', default=date.today().year, type=int)
    month = request.args.get('month', default=date.today().month, type=int)

    # no. of days in a month
    num_days = monthrange(year, month)[1]

    # start and end date of the month
    start_date = date(year, month, 1)
    end_date = date(year, month, num_days)

    # query completions in that month for the habit
    completions = HabitLog.query.filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date >= start_date,
        HabitLog.date <= end_date
    ).all()

    # ambil days completed in that month as a set
    completed_days = {log.date.day for log in completions}
    
    first_weekday = (weekday(year, month, 1) + 1) % 7 # Monday=0, Sunday=6; adjust to start from Monday=0 for calendar grid

    # calculate previous month/year for navigation
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    # calculate next month/year for navigation
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    return render_template(
       'habit_history.html',
        habit=habit,
        year=year,
        month=month,
        num_days=num_days,
        completed_days=completed_days,
        first_weekday=first_weekday,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )

# calculate streak
def calculate_streaks(log_dates):
    if not log_dates:
        return 0,0,0
    
    log_dates = sorted([d for d in log_dates if isinstance(d, date)])
    
    total_completions = len(log_dates)
    longest_streak = 0
    current_streak = 0 
    streak = 1

    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # check if streak is in log
    if log_dates[-1] == today:
        current_streak = 1
    else:
        current_streak = 0

    # logs in order
    for i in range(1, len(log_dates)):
        prev = log_dates[i - 1]
        curr = log_dates[i]
        if(curr - prev).days == 1:
            streak +=1
        else:
            streak = 1

        if curr == today:
            current_streak = streak
        elif curr == yesterday and today not in log_dates:
            current_streak = streak

        longest_streak = max(longest_streak, streak)

    longest_streak = max(longest_streak, current_streak)

    return total_completions, current_streak, longest_streak




# refresh page but fake atm
@app.route('/refresh')
def refresh():
    session['user_id'] = 1 
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


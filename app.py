# -*- coding: utf8 -*-
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from random import shuffle
from wtforms import IntegerField, HiddenField, StringField, SubmitField
import data
import json


# дни недели
week = {'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница',
        'sat': 'Суббота',
        'sun': 'Воскресенье'
        }

# иконки целей
goal_icon = {"travel": "⛱",
             "study": "🏫",
             "work": "🏢",
             "relocate": "🚜"}


# запись в json-файл
def write_json(file, stroka):
    s = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            s = json.loads(f.read())
    except:
        f = open(file, 'w', encoding='utf-8')
        f.close()
    finally:
        s = list(s)
        s.extend(stroka)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(s, sort_keys=True, indent=2, ensure_ascii=False))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = '123456'
db = SQLAlchemy(app)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    goals = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)

    bron = db.relationship('Bron', back_populates='teacher')


class Bron(db.Model):
    __tablename__ = 'bron'
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    teacher = db.relationship('Teacher', back_populates='bron')
    # как реализовать teacherId, teacherDay, teacherTime


class Requestss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    goal = db.Column(db.String(100), unique=True, nullable=False)
    time = db.Column(db.String(100), unique=True, nullable=False)


class Booking(FlaskForm):
    teacher_id = HiddenField('Учитель')
    day = HiddenField('День недели')
    hour = HiddenField('Время')
    name = StringField('Имя пользователя')
    phone = StringField('Цена')
    submit = SubmitField()


# создание БД, запись data.py в нее
'''db.create_all()
for t in data.teachers:
    t = Teacher(name=t['name'],
                about=t['about'],
                rating=t['rating'],
                picture=t['picture'],
                price=t['price'],
                goals=' '.join(t['goals']),
                time=json.dumps(t['free']))
    db.session.add(t)
db.session.commit()'''

teachers = db.session.query(Teacher).all()


@app.route('/')
def main():
    # рандомный список 6 учителей
    t = teachers
    shuffle(t)
    return render_template("index.html",
                           goals=data.goals,
                           goal_icon=goal_icon,
                           teachers=t[:6])


@app.route('/all_teachers/')
def all_teachers():
    return render_template('all_teachers.html',
                           teachers=teachers)


@app.route('/profile/<id_teacher>/')
def id_teach(id_teacher):
    teacher = db.session.query(Teacher).filter(Teacher.id == id_teacher).first()
    # список времени
    lst = json.loads(teacher.time)
    return render_template("profile.html",
                           lst=lst,
                           teacher=teacher,
                           week=week)


@app.route('/goals/<goal>/')
def to_goals(goal):
    teachers = db.session.query(Teacher).filter(Teacher.goals.ilike(f"%{goal}%"))\
        .order_by(Teacher.rating.desc()).all()
    return render_template("goal.html",
                           icon=goal_icon[goal],
                           goal=goal,
                           goals=data.goals,
                           teachers=teachers)


@app.route('/booking/<id_teacher>/<day_week>/<time>/')
def booking(id_teacher, day_week, time):
    teacher = db.session.query(Teacher).filter(Teacher.id == id_teacher).first()
    form = Booking()
    return render_template("booking.html",
                           day=day_week,
                           teacher=teacher,
                           time=time,
                           week=week,
                           form=form)


@app.route('/booking_done/', methods=['POST'])
def booking_done():
    # teacherId = request.form.get('clientTeacher')
    # teacherDay = request.form.get('clientWeekday')
    # teacherTime = request.form.get('clientTime')
    # clientName = request.form.get('clientName')
    # clientPhone = request.form.get('clientPhone')

    form = Booking()
    print(form.name.data)
    print(form.phone.data)
    print(form.day.data)
    print(form.hour.data)
    print(form.teacher_id.data)
    # подготовка json-строки
    stroka = [{
        "teacher":
            {
                'ID': teacherId,
                "day": week[teacherDay],
                "time": teacherTime
            },
        "client":
            {
                "name": clientName,
                "phone": clientPhone
            }
    }]

    write_json('booking.json', stroka)

    return render_template("booking_done.html",
                           teacherDay=week[teacherDay],
                           teacherTime=teacherTime,
                           clientName=clientName,
                           clientPhone=clientPhone)


@app.route('/request/')
def t_request():
    return render_template("request.html")


@app.route('/request_done/', methods=['POST'])
def request_done():
    goal = request.form.get('goal')
    time = request.form.get('time')
    clientName = request.form.get('clientName')
    clientPhone = request.form.get('clientPhone')

    goal = data.goals[goal]
    stroka = [{
        'goal': goal,
        'time': time,
        'clientName': clientName,
        'clientPhone': clientPhone
    }]

    write_json('request.json', stroka)

    return render_template("request_done.html",
                           goal=goal,
                           time=time,
                           clientName=clientName,
                           clientPhone=clientPhone)


@app.errorhandler(404)
@app.errorhandler(500)
def not_found(e):
    return "Такой страницы нет"


if __name__ == "__main__":
    app.run('0.0.0.0', 8000)

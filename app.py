# -*- coding: utf8 -*-
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from random import sample
from wtforms import RadioField, HiddenField, StringField, SubmitField
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


# бронирование времемни у учителя
class Bron(db.Model):
    __tablename__ = 'bron'
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(50), nullable=False, unique=False)
    hour = db.Column(db.String(50), nullable=False, unique=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    teacher = db.relationship('Teacher', back_populates='bron')


# запрос на поиск учителя
class Requestss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    goal = db.Column(db.String(100), unique=True, nullable=False)
    time = db.Column(db.String(100), unique=True, nullable=False)


# форма для заполнения
class Booking(FlaskForm):
    # для бронирования времени
    teacher_id = HiddenField('Учитель')
    day = HiddenField('День недели')
    hour = HiddenField('Время')
    name = StringField('Имя пользователя')
    phone = StringField('Номер телефона')
    submit = SubmitField()
    # для подбора учителя
    radio_goal = RadioField("Цель занятий", choices=[('travel', 'Для путешествий'),
                                                     ('study', 'Для учебы'),
                                                     ('work', 'Для работы'),
                                                     ('relocate', 'Для переезда')])
    radio_time = RadioField("Время в неделю", choices=[(1, '1-2 часа в неделю'),
                                                       (2, '3-5 часов в неделю'),
                                                       (3, '5-7 часов в неделю'),
                                                       (4, '7-10 часов в неделю')])


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
db.session.commit()
'''

teachers = db.session.query(Teacher).all()


@app.route('/')
def main():
    return render_template("index.html",
                           goals=data.goals,
                           goal_icon=goal_icon,
                           teachers=sample(teachers, 6))


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
    form = Booking()
    # запись в БД
    user = Bron(client_name=form.name.data,
                client_phone=form.phone.data,
                teacher_id=form.teacher_id.data,
                day=form.day.data,
                hour=form.hour.data)
    db.session.add(user)
    db.session.commit()
    return render_template("booking_done.html",
                           form=form,
                           week=week)


@app.route('/request/')
def t_request():
    form = Booking()
    return render_template("request.html", form=form)


@app.route('/request_done/', methods=['POST'])
def request_done():
    form = Booking()
    user = Requestss(client_name=form.name.data,
                     client_phone=form.phone.data,
                     goal=form.radio_goal.data,
                     time=form.radio_time.data)
    db.session.add(user)
    db.session.commit()
    return render_template("request_done.html", form=form, goals=data.goals)


@app.errorhandler(404)
@app.errorhandler(500)
def not_found(e):
    return "Такой страницы нет"


if __name__ == "__main__":
    app.run('0.0.0.0', 8000)

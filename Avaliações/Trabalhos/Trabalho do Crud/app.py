from flask import Flask, render_template, request, redirect, session, url_for, flash # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime
import os
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = b'\x9a\xf1\xd3\xe4\x1f\xf8\xbd!\x12\xa2\x8a\xec\x0b\xdbJ\x8c\x90'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definição das tabelas
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    consultations = db.relationship('Consultation', backref='user', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    crm = db.Column(db.Integer, unique=True, nullable=False)
    consultations = db.relationship('Consultation', backref='doctor', lazy=True)

class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nome_paciente = db.Column(db.String(100), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    nome_doctor = db.Column(db.String(100), nullable=False)
    crm = db.Column(db.Integer, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/areamedico', methods=['GET'])
def areamedico():
    crm = request.args.get('crm')
    crm = int(crm) if crm else None  # Converte para inteiro se não for None
    
    if crm:
        # Filtra consultas com base no CRM fornecido
        consultations = Consultation.query.filter_by(crm=crm).all()
    else:
        consultations = []

    # Verifica se o CRM foi passado corretamente e imprime para depuração
    print(f"CRM recebido: {crm}")
    print(f"Consultas encontradas: {consultations}")

    return render_template('areamedico.html', consultations=consultations, crm=crm)

@app.route('/editar_consulta/<int:id>', methods=['GET', 'POST'])
def edit_consultation(id):
    consultation = Consultation.query.get_or_404(id)
    
    if request.method == 'POST':
        consultation.date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash('Consulta atualizada com sucesso!')
        return redirect(url_for('areamedico', crm=consultation.crm))
    
    return render_template('editar_consulta.html', consultation=consultation)

@app.route('/delete_consultation/<int:id>', methods=['POST'])
def delete_consultation(id):
    consultation = Consultation.query.get_or_404(id)
    db.session.delete(consultation)
    db.session.commit()
    flash('Consulta excluída com sucesso!')
    return redirect(url_for('areamedico', crm=consultation.crm))



@app.route("/logindomedico", methods=['GET',"POST"])
def logindomedico():
    return render_template('logindomedico.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            return redirect(url_for('agendamento'))
        else:
            flash('Usuário Inválido')
            return redirect('/login')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('e-mail')
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            flash('Cadastro inválido')
            return redirect('/register')
    return render_template('register.html')


@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form.get('name')
        specialty = request.form.get('specialty')
        crm= request.form.get('crm')
        if name and specialty:
            new_doctor = Doctor(name=name, specialty=specialty, crm=crm)
            db.session.add(new_doctor)
            db.session.commit()
            return redirect(url_for('logindomedico'))
        else:
            flash('Preencha todos os campos')
            return redirect('/register_doctor')
    return render_template('register_doctor.html')


@app.route('/agendamento', methods=['GET', 'POST'])
def agendamento():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)
    specialty = db.session.query(Doctor.specialty).distinct().all()
    specialty = [specialty[0] for specialty in specialty]
    doctors = Doctor.query.all()

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        date_time_str = request.form.get('date_time')

        doctor = Doctor.query.get(doctor_id)

        if date_time_str and doctor and user:
            date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
            new_consultation = Consultation(
                user_id=user.id,
                nome_paciente=user.username,
                doctor_id=doctor.id,  # Use doctor.id
                nome_doctor=doctor.name,
                crm=doctor.crm,  # Use doctor.crm
                date_time=date_time
            )
            db.session.add(new_consultation)
            db.session.commit()
            return redirect(url_for('agendamento'))
        else:
            return "Erro ao capturar os dados para o agendamento.", 400

    consultations = Consultation.query.all()
    return render_template('agendamento.html', doctors=doctors, specialties=specialty, consultations=consultations)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

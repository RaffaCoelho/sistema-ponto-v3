from flask_sqlalchemy import SQLAlchemy
from datetime import date

# Instância global do banco (será inicializada no app)
db = SQLAlchemy()


class Schedule(db.Model):
    __tablename__ = "schedule"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)

    entrada_manha = db.Column(db.String(5), default="08:00")
    saida_manha = db.Column(db.String(5), default="12:00")
    entrada_tarde = db.Column(db.String(5), default="14:00")
    saida_tarde = db.Column(db.String(5), default="18:00")

    # relação inversa: lista de funcionários com esse horário
    funcionarios = db.relationship("Funcionario", back_populates="schedule")

    def __repr__(self):
        return f"<Schedule {self.nome} ({self.entrada_manha}-{self.saida_manha}, {self.entrada_tarde}-{self.saida_tarde})>"


class Funcionario(db.Model):
    __tablename__ = "funcionario"

    id = db.Column(db.String, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    setor = db.Column(db.String(120))
    lotacao = db.Column(db.String(120))
    admissao = db.Column(db.Date, nullable=True)
    demissao = db.Column(db.Date, nullable=True)

    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=True)
    schedule = db.relationship("Schedule", back_populates="funcionarios")

    def __repr__(self):
        return f"<Funcionario {self.nome} ({self.id})>"


class Feriado(db.Model):
    __tablename__ = "feriado"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    descricao = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Feriado {self.data} - {self.descricao}>"

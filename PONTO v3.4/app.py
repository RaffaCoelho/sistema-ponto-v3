from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from datetime import date, datetime, timedelta
import io, zipfile, os
from PyPDF2 import PdfMerger
from flask import request
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from utils.pdf import gerar_pdf
from backup import export_sqlite, import_sqlite
from export_excel import export_to_excel

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ponto.db"
app.config["SECRET_KEY"] = "v3-1-upgrade"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    def set_password(self, pwd): self.password_hash = bcrypt.generate_password_hash(pwd).decode("utf-8")
    def check_password(self, pwd): return bcrypt.check_password_hash(self.password_hash, pwd)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    entrada_manha = db.Column(db.String(5), default="08:00")
    saida_manha = db.Column(db.String(5), default="12:00")
    entrada_tarde = db.Column(db.String(5), default="14:00")
    saida_tarde = db.Column(db.String(5), default="18:00")

class Funcionario(db.Model):
    id = db.Column(db.String, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    setor = db.Column(db.String(120))
    lotacao = db.Column(db.String(120))
    funcao = db.Column(db.String(120))
    admissao = db.Column(db.Date, nullable=True)
    demissao = db.Column(db.Date, nullable=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=True)
    schedule = db.relationship("Schedule", backref="funcionarios")

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    
    nome = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.before_request
def make_session_non_permanent():
    session.permanent = False

@app.route("/auth/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        u = User.query.filter_by(username=username).first()
        if u and u.check_password(password):
            login_user(u); return redirect(url_for("dashboard"))
        flash("Usuário ou senha inválidos", "danger")
    return render_template("login.html")

@app.route("/auth/logout")
@login_required
def logout():
    logout_user(); return redirect(url_for("login"))

@app.route("/auth/register", methods=["GET","POST"])
@login_required
def register():
    if not current_user.is_admin:
        flash("Apenas administradores podem criar usuários.", "danger"); return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form["username"].strip(); password = request.form["password"].strip()
        is_admin = True if request.form.get("is_admin")=="on" else False
        if User.query.filter_by(username=username).first(): flash("Usuário já existe.", "danger")
        else:
            u = User(username=username, is_admin=is_admin); u.set_password(password); db.session.add(u); db.session.commit()
            flash("Usuário criado!", "success"); return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/auth/seed-admin")
def seed_admin():
    if User.query.filter_by(username="admin").first(): return "Admin já existe: admin / admin", 200
    u = User(username="admin", is_admin=True); u.set_password("admin"); db.session.add(u)
    if not Schedule.query.first():
        s = Schedule(nome="Padrão", entrada_manha="08:00", saida_manha="12:00", entrada_tarde="14:00", saida_tarde="18:00"); db.session.add(s)
    db.session.commit(); return "Admin criado: admin / admin", 201

@app.route("/")
@login_required
def dashboard():
    total = Funcionario.query.count(); ativos = Funcionario.query.filter(Funcionario.demissao == None).count(); demitidos = total-ativos
    return render_template("dashboard.html", total=total, ativos=ativos, demitidos=demitidos)

@app.route("/funcionarios")
@login_required
def funcionarios():
    busca = request.args.get("busca","").strip(); setor = request.args.get("setor","").strip(); lotacao = request.args.get("lotacao","").strip(); funcao = request.args.get("funcao","").strip()
    situacao = request.args.get("situacao","Ativos")
    q = Funcionario.query
    if busca:
        like = f"%{busca}%"; q = q.filter((Funcionario.nome.ilike(like)) | (Funcionario.id.ilike(like)))
    if funcao: q = q.filter(Funcionario.funcao == funcao)    
    if setor: q = q.filter(Funcionario.setor == setor)
    if lotacao: q = q.filter(Funcionario.lotacao == lotacao)
    if situacao=="Ativos": q = q.filter(Funcionario.demissao == None)
    elif situacao=="Demitidos": q = q.filter(Funcionario.demissao != None)
    funcionarios = q.order_by(Funcionario.nome.asc()).all()
    setores = sorted({f.setor for f in Funcionario.query.all() if f.setor});
    lotacoes = sorted({f.lotacao for f in Funcionario.query.all() if f.lotacao});
    funcoes = sorted({f.funcao for f in Funcionario.query.all() if f.funcao})
    return render_template("funcionarios.html", funcionarios=funcionarios, filtros=dict(busca=busca,setor=setor,lotacao=lotacao, funcao=funcao, situacao=situacao), setores=setores, lotacoes=lotacoes, funcoes=funcoes)

@app.route("/funcionarios/novo", methods=["GET","POST"])
@login_required
def funcionario_novo():
    schedules = Schedule.query.all()
    if request.method == "POST":
        try:
            admissao = request.form.get("admissao") or None; demissao = request.form.get("demissao") or None
            f = Funcionario(
                id=request.form["matricula"].strip(), nome=request.form["nome"].strip(),
                setor=request.form.get("setor","").strip(), lotacao=request.form.get("lotacao","").strip(),
                funcao = request.form["funcao"].strip(),admissao=datetime.strptime(admissao, "%Y-%m-%d").date() if admissao else None,
                demissao=datetime.strptime(demissao, "%Y-%m-%d").date() if demissao else None,
                schedule_id=int(request.form.get("schedule_id")) if request.form.get("schedule_id") else None
            )
            db.session.add(f); db.session.commit(); flash("Funcionário cadastrado!", "success"); return redirect(url_for("funcionarios"))
        except Exception as e:
            db.session.rollback(); flash(f"Erro ao cadastrar: {e}", "danger")
    return render_template("funcionario_form.html", schedules=schedules, f=None)

@app.route("/funcionarios/<matricula>/editar", methods=["GET","POST"])
@login_required
def funcionario_editar(matricula):
    f = Funcionario.query.get_or_404(matricula); schedules = Schedule.query.all()
    if request.method == "POST":
        try:
            f.nome = request.form["nome"].strip(); f.setor = request.form.get("setor","").strip(); f.lotacao = request.form.get("lotacao","").strip()
            admissao = request.form.get("admissao") or None; demissao = request.form.get("demissao") or None
            f.admissao = datetime.strptime(admissao, "%Y-%m-%d").date() if admissao else None
            f.demissao = datetime.strptime(demissao, "%Y-%m-%d").date() if demissao else None
            f.schedule_id = int(request.form.get("schedule_id")) if request.form.get("schedule_id") else None
            db.session.commit(); flash("Funcionário atualizado!", "success"); return redirect(url_for("funcionarios"))
        except Exception as e:
            db.session.rollback(); flash(f"Erro ao salvar: {e}", "danger")
    return render_template("funcionario_form.html", schedules=schedules, f=f)

@app.route("/funcionarios/<matricula>/excluir", methods=["POST"])
@login_required
def funcionario_excluir(matricula):
    f = Funcionario.query.get_or_404(matricula); db.session.delete(f); db.session.commit(); flash("Funcionário excluído.", "info")
    return redirect(url_for("funcionarios"))

@app.route("/horarios")
@login_required
def horarios():
    hs = Schedule.query.order_by(Schedule.nome.asc()).all(); return render_template("horarios.html", horarios=hs)

@app.route("/horarios/novo", methods=["GET","POST"])
@login_required
def horario_novo():
    if request.method == "POST":
        s = Schedule(
            nome=request.form["nome"],
            entrada_manha=request.form.get("entrada_manha","08:00"), saida_manha=request.form.get("saida_manha","12:00"),
            entrada_tarde=request.form.get("entrada_tarde","14:00"), saida_tarde=request.form.get("saida_tarde","18:00"),
        ); db.session.add(s); db.session.commit(); return redirect(url_for("horarios"))
    return render_template("horario_form.html", s=None)

@app.route("/horarios/<int:sid>/editar", methods=["GET","POST"])
@login_required
def horario_editar(sid):
    s = Schedule.query.get_or_404(sid)
    if request.method == "POST":
        s.nome = request.form["nome"]; s.entrada_manha = request.form.get("entrada_manha","08:00"); s.saida_manha = request.form.get("saida_manha","12:00")
        s.entrada_tarde = request.form.get("entrada_tarde","14:00"); s.saida_tarde = request.form.get("saida_tarde","18:00"); db.session.commit(); return redirect(url_for("horarios"))
    return render_template("horario_form.html", s=s)

@app.route("/horarios/<int:sid>/excluir", methods=["POST"])
@login_required
def horario_excluir(sid):
    s = Schedule.query.get_or_404(sid); db.session.delete(s); db.session.commit(); return redirect(url_for("horarios"))

@app.route("/feriados", methods=["GET","POST"])
@login_required
def feriados():
    if request.method == "POST":
        data = datetime.strptime(request.form["data"], "%Y-%m-%d").date(); nome = request.form["nome"].strip()
        if not Holiday.query.filter_by(data=data).first():
            db.session.add(Holiday(data=data, nome=nome)); db.session.commit()
    hs = Holiday.query.order_by(Holiday.data.asc()).all(); return render_template("feriados.html", feriados=hs)

@app.route("/feriados/<int:hid>/excluir", methods=["POST"])
@login_required
def feriado_excluir(hid):
    h = Holiday.query.get_or_404(hid); db.session.delete(h); db.session.commit(); return redirect(url_for("feriados"))

@app.route("/relatorios")
@login_required
def relatorios(): return render_template("relatorios.html")

@app.route("/relatorios/pdf/<matricula>")
@login_required
def relatorio_individual(matricula):
    f = Funcionario.query.get_or_404(matricula)
    ano = int(request.args.get("ano", date.today().year))
    mes = int(request.args.get("mes", date.today().month))
    buf = io.BytesIO()
    gerar_pdf(
        f, buf, ano, mes,
        {h.data: h.nome for h in Holiday.query.all() if h.data.year == ano},
        logo_esq=os.path.join('static', 'img', 'logo_funad.png'),
        logo_dir=os.path.join('static', 'img', 'logo_crh.png')
    )
    buf.seek(0)
    fname = f"folha_{f.id}_{mes:02d}-{ano}.pdf"
    return send_file(
        buf,
        as_attachment=False,
        download_name=fname,
        mimetype="application/pdf"
    )

@app.route("/relatorios/pdf-lote")
@login_required
def relatorio_lote():
    busca = request.args.get("busca","").strip()
    setor = request.args.get("setor","").strip()
    lotacao = request.args.get("lotacao","").strip()
    funcao = request.args.get("funcao","").strip()
    situacao = request.args.get("situacao","Ativos")
    ano = int(request.args.get("ano", date.today().year))
    mes = int(request.args.get("mes", date.today().month))
    q = Funcionario.query
    if busca:
        like = f"%{busca}%"
        q = q.filter((Funcionario.nome.ilike(like)) | (Funcionario.id.ilike(like)))
    if setor:
        q = q.filter(Funcionario.setor == setor)
    if lotacao:
        q = q.filter(Funcionario.lotacao == lotacao)
    if funcao:
        q = q.filter(Funcionario.funcao == funcao)
    if situacao == "Ativos":
        q = q.filter(Funcionario.demissao == None)
    elif situacao == "Demitidos":
        q = q.filter(Funcionario.demissao != None)
    funcionarios = q.order_by(Funcionario.nome.asc()).all()
    feriados_db = {h.data: h.nome for h in Holiday.query.all() if h.data.year == ano}

    merger = PdfMerger()
    for f in funcionarios:
        buf = io.BytesIO()
        gerar_pdf(
            f, buf, ano, mes, feriados_db,
            logo_esq=os.path.join('static','img','logo_funad.png'),
            logo_dir=os.path.join('static','img','logo_crh.png')
        )
        buf.seek(0)
        merger.append(buf)
    out = io.BytesIO()
    merger.write(out)
    out.seek(0)
    # Para abrir em nova aba, basta garantir as_attachment=False e definir o mimetype corretamente
    return send_file(
        out,
        as_attachment=False,
        download_name=f"folhas_{mes:02d}-{ano}.pdf",
        mimetype="application/pdf"
    )


@app.route("/backup")
@login_required
def backup_page():
    if not current_user.is_admin:
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("backup.html")


@app.route("/backup/export")
@login_required
def backup_export():
    if not current_user.is_admin:
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))
    db_path = os.path.join(app.root_path, "instance", "ponto.db")
    out = export_sqlite(db_path, os.path.join(app.root_path, "instance"))
    return send_file(out, as_attachment=True, download_name=os.path.basename(out))


@app.route("/backup/import", methods=["POST"])
@login_required
def backup_import():
    if not current_user.is_admin:
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))
    file = request.files.get("arquivo")
    if not file or not file.filename:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for("backup_page"))
    tmp_path = os.path.join(app.root_path, "instance", "_upload.sqlite")
    file.save(tmp_path)
    db_path = os.path.join(app.root_path, "instance", "ponto.db")
    import_sqlite(tmp_path, db_path)
    os.remove(tmp_path)
    flash("Backup restaurado com sucesso.", "success")
    return redirect(url_for("backup_page"))


@app.route("/relatorios/excel")
@login_required
def relatorio_excel():
    # Same filters as lote
    from io import BytesIO


    busca = request.args.get("busca","").strip()
    setor = request.args.get("setor","").strip()
    lotacao = request.args.get("lotacao","").strip()
    situacao = request.args.get("situacao","Ativos")
    q = Funcionario.query
    if busca:
        like = f"%{busca}%"
        q = q.filter((Funcionario.nome.ilike(like)) | (Funcionario.id.ilike(like)))
    if setor: q = q.filter(Funcionario.setor == setor)
    if lotacao: q = q.filter(Funcionario.lotacao == lotacao)
    if situacao=="Ativos": q = q.filter(Funcionario.demissao == None)
    elif situacao=="Demitidos": q = q.filter(Funcionario.demissao != None)
    funcionarios = q.order_by(Funcionario.nome.asc()).all()
    rows = []
    for f in funcionarios:
        rows.append({
            "matricula": getattr(f, "id", None),
            "nome": getattr(f, "nome", ""),
            "setor": getattr(f, "setor", ""),
            "lotacao": getattr(f, "lotacao", ""),
            "admissao": getattr(f, "admissao", ""),
            "demissao": getattr(f, "demissao", ""),
        })
    buf = BytesIO()
    export_to_excel(rows, buf)  # pandas writer also accepts buffer
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="relatorio_funcionarios.xlsx")



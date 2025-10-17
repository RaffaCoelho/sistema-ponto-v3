from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from datetime import date
import calendar, os
from holidays import is_holiday
from theme import WEEKEND_ROW_COLOR, HOLIDAY_ROW_COLOR, ACCENT_COLOR
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

def _hex_to_rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

def _rgb255(r,g,b):
    return (r/255.0, g/255.0, b/255.0)

WEEKEND = _rgb255(*_hex_to_rgb(WEEKEND_ROW_COLOR))
HOLIDAY = _rgb255(*_hex_to_rgb(HOLIDAY_ROW_COLOR))
ACCENT = _rgb255(*_hex_to_rgb(ACCENT_COLOR))

def celula_dividida(manha, tarde):
    sub_data = [
        [manha],
        [tarde]
    ]
    sub_table = Table(sub_data, colWidths=[80], rowHeights=[15, 15])
    sub_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return sub_table


def gerar_pdf(funcionario, buffer, ano=None, mes=None, feriados_map=None, logo_esq=None, logo_dir=None):
    if ano is None or mes is None:
        hoje = date.today(); ano, mes = hoje.year, hoje.month
    feriados_map = feriados_map or {}
    logo_esq = logo_esq or os.path.join('static','img','logo_funad.png')
    logo_dir = logo_dir or os.path.join('static','img','logo_crh.png')

    
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=30*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Center", parent=styles['Normal'], alignment=1))

   

    def draw_header(canvas, doc):
        y = A4[1] - 20*mm
        try:
            canvas.drawImage(logo_esq, 18*mm, y-10*mm, width=30*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
        except Exception: pass
        try:
            canvas.drawImage(logo_dir, A4[0]-58*mm, y-20*mm, width=40*mm, height=40*mm, preserveAspectRatio=True, mask='auto')
        except Exception: pass
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawCentredString(A4[0]/2, y-2*mm, f"Folha de Ponto • {mes:02d}/{ano}")
        canvas.setLineWidth(0.5); canvas.line(18*mm, y-12*mm, A4[0]-18*mm, y-12*mm)

        # footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(18*mm, 12*mm, "Instituição • FUNAD")
        canvas.drawRightString(A4[0]-18*mm, 12*mm, f"Gerado em {date.today().strftime('%d/%m/%Y')}")

    story = []
    story.append(Paragraph(f"Servidor: <b>{getattr(funcionario,'nome','')}</b>  — Função:<b> {getattr(funcionario,'funcao','')}</b>")) 
    story.append(Paragraph(f"Lotação: <b>{getattr(funcionario,'lotacao','')}</b> — Setor: <b>{getattr(funcionario,'setor','')}</b> — Matrícula: <b>{getattr(funcionario,'id','')}</b>"))

    story.append(Spacer(1, 6))

    # Build days table
    first_weekday, days_in_month = calendar.monthrange(ano, mes)
    header = ["Data", "Dia", "Entrada Manhã", "Saída Manhã", "Entrada Tarde", "Saída Tarde", "Observações"]
    data = [header]
    row_styles = [("GRID",(0,0),(-1,-1),0.5,colors.black),
                  ("BACKGROUND",(0,0),(-1,0), colors.Color(*ACCENT)),
                  ("ALIGN",(0,0),(-1,0),"CENTER")]
    for d in range(1, days_in_month+1):
        dt = date(ano, mes, d)
        weekday_name = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"][dt.weekday()]
        obs = ""
        if dt in feriados_map:
            obs = feriados_map[dt]
            is_hol = True
        else:
            is_hol, hol_name = is_holiday(dt)
            if is_hol:
              obs = hol_name or "Feriado"
        obs_style=ParagraphStyle('obs', fontsize=8, leading=10)
        row = [f"{d:02d}/{mes:02d}", weekday_name, "", "", "", "", Paragraph(obs, obs_style) if obs else ""]
        data.append(row)
        row_index = len(data)-1
        if dt.weekday() >= 5:  # weekend
            row_styles.append(("BACKGROUND",(0,row_index),(-1,row_index), colors.Color(*WEEKEND)))
        if is_hol:
            row_styles.append(("BACKGROUND",(0,row_index),(-1,row_index), colors.Color(*HOLIDAY)))

    t = Table(data, colWidths=[40, 28, 75, 75, 75, 75, 200])
    t.setStyle(TableStyle(row_styles))
    story.append(t)
    story.append(Spacer(1, 10))

    # Schedule table centered text
    
    story.append(Paragraph("Horário de Trabalho", styles['Center']))
    schedule = funcionario.schedule  # pega o horário vinculado
    th = Table([["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA"],
          [
        celula_dividida(
            f"{getattr(schedule, 'entrada_manha', '')} - {getattr(schedule, 'saida_manha', '')}",
            f"{getattr(schedule, 'entrada_tarde', '')} - {getattr(schedule, 'saida_tarde', '')}"
        ),
        celula_dividida(
            f"{getattr(schedule, 'entrada_manha', '')} - {getattr(schedule, 'saida_manha', '')}",
            f"{getattr(schedule, 'entrada_tarde', '')} - {getattr(schedule, 'saida_tarde', '')}"
        ),
        celula_dividida(
            f"{getattr(schedule, 'entrada_manha', '')} - {getattr(schedule, 'saida_manha', '')}",
            f"{getattr(schedule, 'entrada_tarde', '')} - {getattr(schedule, 'saida_tarde', '')}"
        ),
        celula_dividida(
            f"{getattr(schedule, 'entrada_manha', '')} - {getattr(schedule, 'saida_manha', '')}",
            f"{getattr(schedule, 'entrada_tarde', '')} - {getattr(schedule, 'saida_tarde', '')}"
        ),
        celula_dividida(
            f"{getattr(schedule, 'entrada_manha', '')} - {getattr(schedule, 'saida_manha', '')}",
            f"{getattr(schedule, 'entrada_tarde', '')} - {getattr(schedule, 'saida_tarde', '')}"
        ),
    ],
                
            ],
               colWidths=[ 90, 90, 90, 90, 90] )
    
    
    th.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1.5,colors.black),
                            ("BACKGROUND",(0,0),(-1,0), colors.Color(*ACCENT)),
                            ("ALIGN",(0,0),(-1,0),"CENTER"),
                            ("ALIGN",(0,1),(-1,1),"CENTER")]))
    story.append(th)

    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)

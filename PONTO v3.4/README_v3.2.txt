PONTO v3.2 - Resumo das melhorias
=================================
- Interface: paleta #0328f8 (primária), #ffffff (fundo), #ffc200 (acentos).
- Relatórios: exportação Excel (.xlsx) adicionada (openpyxl/pandas).
- Filtros: por nome, setor, lotação e período (filters.py).
- Controle de usuários: auth.py (admin e user), com tabela users (SQLite).
- PDF aprimorado: helpers em pdf_helpers.py para cabeçalho/rodapé e destaque de finais de semana e feriados.
- Backup: exportar e importar banco (backup.py).

COMO INTEGRAR NO CÓDIGO EXISTENTE
---------------------------------
- Interface (Tkinter/TTK): utilize theme.py para aplicar cores nos widgets.
- Relatório Excel: chame export_to_excel(rows, 'saida.xlsx').
- Filtros: use ReportFilter + apply_filters(rows, filtro).
- Auth: use auth.ensure_schema(db), auth.login(...), auth.is_admin(session).
- Backup: export_sqlite(db, 'backups/') e import_sqlite('backup.sqlite', db).
- PDF: utilize pdf_helpers.weekend_or_holiday(data) para colorir linhas e opcionalmente exibir nome do feriado.

Observações
-----------
- Caso seu gerador de PDF use FPDF e não reportlab, adapte as cores (RGB 0-255) e o fill para cada linha.
- As funções on_export_excel / on_backup_export / on_backup_import foram adicionadas nos arquivos de UI detectados para facilitar a ligação com botões/menus.

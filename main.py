import sqlite3
from datetime import datetime
import flet as ft
import csv

DB_NAME = "pocketledger_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            importo REAL NOT NULL,
            tipo TEXT NOT NULL,
            conto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descrizione TEXT,
            fisco INTEGER DEFAULT 0,
            isee INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM conti")
    if cursor.fetchone()[0] == 0:
        conti_iniziali = [('Conto Corrente',), ('Hype',), ('PostPay / Carta',), ('Contanti',)]
        cursor.executemany("INSERT INTO conti (nome) VALUES (?)", conti_iniziali)
        
    cursor.execute("SELECT COUNT(*) FROM categorie")
    if cursor.fetchone()[0] == 0:
        cat_iniziali = [
            ('Stipendio / Salario', 'Entrata'),
            ('Rimborso / Extra', 'Entrata'),
            ('Alimentari e Supermercato', 'Uscita'),
            ('Affitto / Mutuo', 'Uscita'),
            ('Bollette (Luce, Gas, Acqua, Internet)', 'Uscita'),
            ('Condominio e Spese Casa', 'Uscita'),
            ('Carburante e Trasporti', 'Uscita'),
            ('Assicurazione e Bollo Auto', 'Uscita'),
            ('Salute, Farmacia e Medico', 'Uscita'),
            ('Istruzione e Università', 'Uscita'),
            ('Mantenimento / Assegni', 'Uscita'),
            ('Svago, Ristoranti e Hobby', 'Uscita'),
            ('Abbonamenti (Streaming, Servizi)', 'Uscita'),
            ('Shopping e Abbigliamento', 'Uscita'),
            ('Tasse e Contributi', 'Uscita'),
            ('Spese Varie / Generico', 'Uscita')
        ]
        cursor.executemany("INSERT INTO categorie (nome, tipo) VALUES (?, ?)", cat_iniziali)
        
    conn.commit()
    conn.close()

def get_db_data(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data

def main(page: ft.Page):
    page.title = "PocketLedger Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 15
    
    init_db()
    
    conti_db = [c[0] for c in get_db_data("SELECT nome FROM conti")]
    cat_db = [c[0] for c in get_db_data("SELECT nome FROM categorie")]
    
    anno_corrente = str(datetime.now().year)
    
    selettore_anno = ft.Dropdown(
        label="Anno",
        options=[ft.dropdown.Option(str(y)) for y in range(2024, 2031)],
        value=anno_corrente,
        width=110, text_size=12,
        on_change=lambda e: aggiorna_interfaccia()
    )
    
    cards_container = ft.Row([], spacing=10, scroll=ft.ScrollMode.AUTO)
    status_text = ft.Text("", size=12, color="green")
    movimenti_list = ft.ListView(expand=1, spacing=6, padding=5, height=280)

    filtro_conto = ft.Dropdown(
        label="Filtra Conto",
        options=[ft.dropdown.Option("Tutti")] + [ft.dropdown.Option(c) for c in conti_db],
        value="Tutti", width=150, text_size=11,
        on_change=lambda e: aggiorna_interfaccia()
    )
    filtro_cat = ft.Dropdown(
        label="Filtra Categoria",
        options=[ft.dropdown.Option("Tutte")] + [ft.dropdown.Option(c) for c in cat_db],
        value="Tutte", width=170, text_size=11,
        on_change=lambda e: aggiorna_interfaccia()
    )

    form_conto = ft.Dropdown(label="Conto", options=[ft.dropdown.Option(c) for c in conti_db], expand=2, text_size=12)
    form_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Uscita"), ft.dropdown.Option("Entrata")], value="Uscita", expand=1, text_size=12)
    form_importo = ft.TextField(label="Importo (€)", keyboard_type=ft.KeyboardType.NUMBER, expand=1, text_size=12)
    form_cat = ft.Dropdown(label="Categoria", options=[ft.dropdown.Option(c) for c in cat_db], expand=2, text_size=12)
    form_desc = ft.TextField(label="Descrizione", expand=3, text_size=12)
    form_data = ft.TextField(label="Data (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"), expand=1, text_size=12)
    
    chk_fisco = ft.Checkbox(label="Interesse Fiscale / Detraibile", value=False)
    chk_isee = ft.Checkbox(label="Rilevante per ISEE", value=False)

    edit_id = ft.Text(visible=False)
    edit_conto = ft.Dropdown(label="Conto", options=[ft.dropdown.Option(c) for c in conti_db], width=180, text_size=12)
    edit_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Uscita"), ft.dropdown.Option("Entrata")], width=120, text_size=12)
    edit_importo = ft.TextField(label="Importo", width=120, text_size=12)
    edit_cat = ft.Dropdown(label="Categoria", options=[ft.dropdown.Option(c) for c in cat_db], width=180, text_size=12)
    edit_desc = ft.TextField(label="Descrizione", width=250, text_size=12)
    edit_data = ft.TextField(label="Data", width=130, text_size=12)
    edit_fisco = ft.Checkbox(label="Fisco")
    edit_isee = ft.Checkbox(label="ISEE")

    def aggiorna_interfaccia():
        anno_selezionato = selettore_anno.value
        cards_container.controls.clear()
        totale_generale = 0.0
        
        for conto in conti_db:
            movs = get_db_data("SELECT tipo, importo FROM movimenti WHERE conto = ? AND data LIKE ?", (conto, f"{anno_selezionato}%"))
            saldo_conto = sum(imp if t == "Entrata" else -imp for t, imp in movs)
            totale_generale += saldo_conto
            
            cards_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(conto, size=13, color="cyan", weight=ft.FontWeight.BOLD),
                        ft.Text(f"€ {saldo_conto:,.2f}", size=18, weight=ft.FontWeight.BOLD, color="green" if saldo_conto >= 0 else "red"),
                        ft.Text(f"Anno {anno_selezionato}", size=10, color="grey")
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor="#1e293b", padding=12, border_radius=8, width=160, height=100
                )
            )
            
        cards_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("TOTALE GENERALE", size=13, color="amber", weight=ft.FontWeight.BOLD),
                    ft.Text(f"€ {totale_generale:,.2f}", size=18, weight=ft.FontWeight.BOLD, color="green" if totale_generale >= 0 else "red"),
                    ft.Text(f"Anno {anno_selezionato}", size=10, color="grey")
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#1e293b", padding=12, border_radius=8, width=160, height=100
            )
        )

        query = "SELECT id, data, importo, tipo, conto, categoria, descrizione, fisco, isee FROM movimenti WHERE data LIKE ?"
        params = [f"{anno_selezionato}%"]
        
        if filtro_conto.value != "Tutti":
            query += " AND conto = ?"
            params.append(filtro_conto.value)
        if filtro_cat.value != "Tutte":
            query += " AND categoria = ?"
            params.append(filtro_cat.value)
            
        query += " ORDER BY data DESC, id DESC"
        
        movimenti_list.controls.clear()
        righe = get_db_data(query, tuple(params))
        
        if not righe:
            movimenti_list.controls.append(ft.Text("Nessun movimento trovato per i filtri selezionati.", size=12, color="grey"))
        else:
            for r in righe:
                m_id, data, importo, tipo, conto, cat, desc, fisco, isee = r
                segno = "+" if tipo == "Entrata" else "-"
                colore = "green" if tipo == "Entrata" else "red"
                
                badges = []
                if fisco:
                    badges.append(ft.Container(content=ft.Text("FISCO", size=9, color="white", weight=ft.FontWeight.BOLD), bgcolor="purple", border_radius=3, padding=3))
                if isee:
                    badges.append(ft.Container(content=ft.Text("ISEE", size=9, color="white", weight=ft.FontWeight.BOLD), bgcolor="teal", border_radius=3, padding=3))

                def apri_modifica(e, rd=r):
                    edit_id.value = str(rd[0])
                    edit_data.value = rd[1]
                    edit_importo.value = str(rd[2])
                    edit_tipo.value = rd[3]
                    edit_conto.value = rd[4]
                    edit_cat.value = rd[5]
                    edit_desc.value = rd[6] if rd[6] else ""
                    edit_fisco.value = bool(rd[7])
                    edit_isee.value = bool(rd[8])
                    page.dialog = edit_dialog
                    edit_dialog.open = True
                    page.update()

                def elimina(e, idm=m_id):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM movimenti WHERE id = ?", (idm,))
                    conn.commit()
                    conn.close()
                    aggiorna_interfaccia()

                movimenti_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Text(data, size=11, color="grey", width=75),
                                ft.VerticalDivider(width=1, color="transparent"),
                                ft.Text(f"{conto} • {cat}", size=12, weight=ft.FontWeight.W_500, color="white", width=200),
                                ft.Row(badges, spacing=4),
                                ft.Text(f"({desc})" if desc else "", size=11, color="grey", italic=True, width=130, overflow=ft.TextOverflow.ELLIPSIS),
                            ], spacing=4),
                            ft.Row([
                                ft.Text(f"{segno}€{importo:,.2f}", size=12, weight=ft.FontWeight.BOLD, color=colore, width=85),
                                ft.TextButton("Modifica", on_click=apri_modifica),
                                ft.TextButton("Elimina", on_click=elimina)
                            ], spacing=2)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bgcolor="#1e293b", padding=6, border_radius=5
                    )
                )
        page.update()

    def salva_nuovo(e):
        try:
            if not form_conto.value or not form_cat.value or not form_importo.value:
                status_text.value = "Compila Conto, Categoria e Importo!"
                status_text.color = "red"
                page.update()
                return

            importo = float(form_importo.value.replace(",", "."))
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO movimenti (data, importo, tipo, conto, categoria, descrizione, fisco, isee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (form_data.value, importo, form_tipo.value, form_conto.value, form_cat.value, form_desc.value, int(chk_fisco.value), int(chk_isee.value)))
            conn.commit()
            conn.close()

            status_text.value = "Movimento salvato con successo!"
            status_text.color = "green"
            form_importo.value = ""
            form_desc.value = ""
            chk_fisco.value = False
            chk_isee.value = False
            aggiorna_interfaccia()
        except ValueError:
            status_text.value = "Errore nel formato dell'importo."
            status_text.color = "red"
            page.update()

    def salva_modifica(e):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE movimenti SET data = ?, importo = ?, tipo = ?, conto = ?, categoria = ?, descrizione = ?, fisco = ?, isee = ?
                WHERE id = ?
            """, (edit_data.value, float(edit_importo.value.replace(",", ".")), edit_tipo.value, edit_conto.value, edit_cat.value, edit_desc.value, int(edit_fisco.value), int(edit_isee.value), int(edit_id.value)))
            conn.commit()
            conn.close()
            edit_dialog.open = False
            aggiorna_interfaccia()
        except ValueError:
            pass

    edit_dialog = ft.AlertDialog(
        title=ft.Text("Modifica Movimento", size=14),
        content=ft.Column([
            edit_id,
            ft.Row([edit_conto, edit_tipo], spacing=8),
            ft.Row([edit_importo, edit_cat], spacing=8),
            ft.Row([edit_desc, edit_data], spacing=8),
            ft.Row([edit_fisco, edit_isee], spacing=15)
        ], tight=True, spacing=8),
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: setattr(edit_dialog, 'open', False) or page.update()),
            ft.ElevatedButton("Salva", on_click=salva_modifica, bgcolor="blue", color="white")
        ]
    )

    def esporta_csv(e):
        try:
            righe_exp = get_db_data("SELECT id, data, importo, tipo, conto, categoria, descrizione, fisco, isee FROM movimenti ORDER BY data DESC")
            filename = f"pocketledger_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Data", "Importo", "Tipo", "Conto", "Categoria", "Descrizione", "Fisco", "ISEE"])
                writer.writerows(righe_exp)
            status_text.value = f"Esportato in {filename}"
            status_text.color = "green"
            page.update()
        except Exception as ex:
            status_text.value = f"Errore export: {ex}"
            status_text.color = "red"
            page.update()

    form_section = ft.Container(
        content=ft.Column([
            ft.Text("Nuovo Movimento", size=13, weight=ft.FontWeight.BOLD, color="amber"),
            ft.Row([form_conto, form_tipo, form_importo, form_cat], spacing=8),
            ft.Row([form_desc, form_data], spacing=8),
            ft.Row([chk_fisco, chk_isee], spacing=15),
            ft.Row([ft.ElevatedButton("Salva Movimento", on_click=salva_nuovo, bgcolor="blue", color="white"), status_text], spacing=10)
        ], spacing=8),
        bgcolor="#1e293b", padding=12, border_radius=8
    )

    storico_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Storico Movimenti", size=13, weight=ft.FontWeight.BOLD, color="amber"),
                ft.Row([filtro_conto, filtro_cat, ft.ElevatedButton("CSV", on_click=esporta_csv, bgcolor="green", color="white", height=30)], spacing=6)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            movimenti_list
        ], spacing=6),
        bgcolor="#1e293b", padding=10, border_radius=8
    )

    page.add(
        ft.Column([
            ft.Row([
                ft.Text("PocketLedger Pro", size=16, weight=ft.FontWeight.BOLD),
                selettore_anno
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            cards_container,
            form_section,
            storico_section
        ], spacing=10)
    )

    aggiorna_interfaccia()

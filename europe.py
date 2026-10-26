"""Cadastro inicial idempotente; alterações posteriores pertencem ao administrador."""
YEAR = 2026
SOURCES = {
    'Roma':'https://www.turismoroma.it/it/itinerari/roma-72-ore',
    'Paris':'https://parisjetaime.com/decouvrir-paris/paris-en-1-2-ou-3-jours-i126',
    'Londres':'https://www.visitlondon.com/things-to-do/visiting-london-for-the-first-time/firsttime-visitors-itinerary',
    'Madrid':'https://www.esmadrid.com/madrid-en-un-dia',
}

def _seed_base(c):
    if not c.execute("SELECT 1 FROM migrations WHERE name='multi-trip-europe-v1'").fetchone():
        notes=('Viagem de 27/10/2026 a 12/11/2026. '
               '01/11: saída de Roma às 18h e chegada a Paris às 23h. '
               'Chegadas a Londres e Madrid ainda sem horário informado. '
               'Passeios são sugestões editáveis; horários de visita são propostas, não reservas. '
               'Confirmar funcionamento, ingressos e deslocamentos para o ano da viagem.')
        c.execute('INSERT INTO trips(name,start,end,places,notes) VALUES(?,?,?,?,?)',('Europa',f'{YEAR}-10-27',f'{YEAR}-11-12','Roma → Paris → Londres → Madrid',notes))
        if c.execute('SELECT 1 FROM entries WHERE trip_id IS NULL').fetchone():
            legacy=c.execute('INSERT INTO trips(name,start,end,places,notes) VALUES(?,?,?,?,?)',('Minha viagem anterior','2026-01-01','2026-12-31','','Conteúdo anterior preservado durante a atualização. Ajuste o período da viagem.')).lastrowid
            c.execute('UPDATE entries SET trip_id=? WHERE trip_id IS NULL',(legacy,))
            c.execute('INSERT INTO trip_members SELECT ?,id FROM users',(legacy,))
        c.execute("INSERT INTO migrations VALUES('multi-trip-europe-v1')")
    if c.execute("SELECT 1 FROM migrations WHERE name='europe-itinerary-v1'").fetchone():return
    admin=c.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if not admin:return
    tid=c.execute("SELECT id FROM trips WHERE name='Europa' ORDER BY id LIMIT 1").fetchone()[0]
    c.execute('INSERT OR IGNORE INTO trip_members VALUES(?,?)',(tid,admin[0]))
    def add(kind,title,city,day,hour,end='',description='',category='Passeio'):
        start=f'{YEAR}-{day}'+(f'T{hour}' if hour else '')
        finish=f'{YEAR}-{day}T{end}' if end else ''
        if kind=='tour':description='SUGESTÃO — horário proposto, sujeito a confirmação de funcionamento e ingressos. '+description+'\nReferência turística: '+SOURCES[city]
        c.execute('INSERT INTO entries(kind,title,place,start,end,description,category,user_id,trip_id) VALUES(?,?,?,?,?,?,?,?,?)',(kind,title,city,start,finish,description,category,admin[0],tid))
    transport=[
        ('Início da viagem Europa','Roma','10-27','','Início em 27/10; origem e horário de embarque ainda não informados.'),
        ('Chegada a Roma','Roma','10-28','06:00','Chegada informada às 06h. Reservar tempo para imigração, bagagem, traslado e descanso.'),
        ('Saída de Roma para Paris','Roma','11-01','18:00','Saída corrigida pelo administrador para 18h. Aeroporto e voo a informar. Manter a tarde livre para traslado e embarque.'),
        ('Chegada a Paris','Paris','11-01','23:00','Chegada informada às 23h. Planejar traslado e entrada tardia no hotel. Aeroporto e voo a informar.'),
        ('Saída de Paris para Londres','Paris','11-08','23:00','Saída informada às 23h. Modal, estação/aeroporto e chegada a Londres a confirmar; não pressupor trem noturno.'),
        ('Chegada a Londres — data e horário a confirmar','Londres','11-09','','Após saída de Paris em 08/11 às 23h. Data e horário exatos dependem do transporte.'),
        ('Saída de Londres para Madrid','Londres','11-12','06:00','Saída informada às 06h. Aeroporto, voo e horário de chegada a Madrid não informados.'),
        ('Chegada a Madrid — horário a confirmar','Madrid','11-12','','Chegada prevista em 12/11, após saída de Londres às 06h. Ajustar passeios conforme pouso, bagagens e traslados.'),
        ('Retorno a partir de Madrid','Madrid','11-12','22:00','Partida informada às 22h. Aeroporto, destino final e voo ainda não informados. Planejar chegada ao aeroporto com antecedência adequada.'),
    ]
    for title,city,day,hour,desc in transport:add('logistics',title,city,day,hour,description=desc,category='Voo' if hour else 'Outro')
    tours=[
        ('Roma','10-28','14:00','17:00','Primeiro passeio: centro histórico','Caminhada leve pela Fontana di Trevi, Piazza di Spagna e arredores. Opcional conforme cansaço da chegada.'),
        ('Roma','10-29','09:00','13:00','Coliseu, Fórum Romano e Palatino','Separar a manhã para a Roma antiga. Confirmar ingresso e janela de entrada no site oficial.'),
        ('Roma','10-29','15:00','17:30','Campidoglio e Piazza Venezia','Caminhada pelos mirantes e praças, com pausas para descanso.'),
        ('Roma','10-30','09:00','13:00','Museus Vaticanos e Capela Sistina','Verificar funcionamento na data escolhida e reservar ingresso; ajustar a ordem dos dias se necessário.'),
        ('Roma','10-30','14:30','17:00','Praça e Basílica de São Pedro','Prever filas e controles de entrada. Visita interna condicionada ao funcionamento.'),
        ('Roma','10-31','10:00','13:00','Pantheon, Piazza Navona e Campo de’ Fiori','Percurso a pé pelo centro. Confirmar ingresso para o Pantheon, se houver visita interna.'),
        ('Roma','10-31','17:00','20:00','Trastevere ao entardecer','Explorar as ruas e escolher um restaurante para jantar em grupo.'),
        ('Roma','11-01','09:00','12:00','Villa Borghese e Pincio','Passeio ao ar livre. Dia de deslocamento: manter a tarde livre para malas e traslado. 01/11 pode afetar a programação local.'),
        ('Paris','11-02','10:00','13:00','Trocadéro, Torre Eiffel e Champ de Mars','Primeiro contato com Paris. Subida à torre somente com ingresso e horário confirmados.'),
        ('Paris','11-02','16:00','18:00','Caminhada às margens do Sena','Passeio leve; cruzeiro opcional sujeito à disponibilidade.'),
        ('Paris','11-04','09:30','13:00','Museu do Louvre','Quarta-feira: evitar terça-feira, dia habitual de fechamento. Escolher alas prioritárias e confirmar ingresso. https://www.louvre.fr/en/visit/hours-admission'),
        ('Paris','11-04','14:30','17:00','Tuileries e Palais Royal','Caminhada com pausa para café após o museu.'),
        ('Paris','11-03','10:00','13:00','Île de la Cité e Quartier Latin','Caminhar pela ilha e arredores de Notre-Dame; visitas internas dependem da disponibilidade na data.'),
        ('Paris','11-03','14:30','17:00','Jardim de Luxemburgo e Saint-Germain','Tarde em jardins, livrarias e cafés.'),
        ('Paris','11-05','09:00','17:00','Versalhes — passeio opcional','Bate-volta com tempo para deslocamentos. Confirmar funcionamento, transporte e ingresso; alternativa: dia livre em Paris.'),
        ('Paris','11-06','10:00','13:00','Montmartre e Sacré-Cœur','Caminhada pelo bairro, mirantes e praça dos artistas.'),
        ('Paris','11-06','15:00','18:00','Opéra e arredores','Explorar o bairro; visita interna à ópera depende da programação.'),
        ('Paris','11-07','10:00','13:00','Musée d’Orsay — visita opcional','Confirmar dia de abertura e ingresso para o ano informado. Alternativa: caminhada pelo Sena.'),
        ('Paris','11-07','15:00','18:00','Champs-Élysées e Arco do Triunfo','Passeio pela avenida; subida ao arco opcional com ingresso.'),
        ('Paris','11-08','10:00','14:00','Le Marais e Place des Vosges','Último passeio em Paris, mantendo o restante do dia para bagagens e deslocamento a Londres.'),
        ('Londres','11-09','11:00','14:00','Westminster, Big Ben e St James’s Park','Provisório: ajustar ao horário de chegada a Londres. Priorizar caminhada externa e descanso.'),
        ('Londres','11-09','16:00','18:00','South Bank às margens do Tâmisa','Passeio pelo rio; atrações pagas são opcionais.'),
        ('Londres','11-10','09:30','13:00','Tower of London e Tower Bridge','Confirmar funcionamento e ingresso; reservar tempo para deslocamento e almoço.'),
        ('Londres','11-10','14:30','17:30','City e arredores de St Paul’s','Caminhada pela City. Visita interna à catedral opcional e sujeita ao funcionamento.'),
        ('Londres','11-11','10:00','13:00','British Museum','Selecionar as coleções de interesse e verificar acesso na data da viagem.'),
        ('Londres','11-11','14:30','18:00','Covent Garden, Soho e despedida de Londres','Passeio e jantar cedo. Preparar malas e traslado para saída às 06h do dia seguinte.'),
        ('Madrid','11-12','12:00','15:00','Puerta del Sol, Plaza Mayor e centro','Somente se houver tempo após pouso e deslocamento. Confirmar guarda de bagagens e duração real da conexão.'),
        ('Madrid','11-12','15:30','17:00','Retiro ou arredores do Palácio Real — opcional','Escolher apenas uma região conforme tempo disponível. Cancelar se a chegada atrasar; priorizar retorno ao aeroporto para a partida às 22h.'),
    ]
    for city,day,hour,end,title,desc in tours:add('tour',title,city,day,hour,end,desc)
    c.execute("INSERT INTO migrations VALUES('europe-itinerary-v1')")

ETAPAS = [
    # título novo, local, início, término, categoria, descrição, títulos antigos convertíveis
    ('Voo Fortaleza → Madrid','Fortaleza',f'{YEAR}-10-27','','Voo','Anexe aqui passagem, cartão de embarque e comprovantes. Horário e voo a informar.',['Início da viagem Europa']),
    ('Voo Madrid → Roma','Madrid',f'{YEAR}-10-28',f'{YEAR}-10-28T06:00','Voo','Chegada a Roma informada às 06h. Anexe passagem e comprovantes. Reservar tempo para imigração, bagagem, traslado e descanso.',['Chegada a Roma']),
    ('Hotel Roma','Roma',f'{YEAR}-10-28',f'{YEAR}-11-01','Hotel','Anexe voucher da reserva e comprovantes. Endereço e horários de check-in/check-out a informar.',[]),
    ('Viagem Roma → Paris','Roma',f'{YEAR}-11-01T18:00',f'{YEAR}-11-01T23:00','Voo','Saída às 18h e chegada às 23h. Anexe passagens e comprovantes. Aeroporto e voo a informar; planejar traslado e entrada tardia no hotel.',['Saída de Roma para Paris']),
    ('Hotel Paris','Paris',f'{YEAR}-11-01',f'{YEAR}-11-08','Hotel','Anexe voucher da reserva e comprovantes. Endereço e horários de check-in/check-out a informar.',[]),
    ('Viagem Paris → Londres','Paris',f'{YEAR}-11-08T23:00','','Outro','Saída às 23h. Modal, estação/aeroporto e chegada a Londres a confirmar; não pressupor trem noturno. Anexe passagens e comprovantes.',['Saída de Paris para Londres']),
    ('Hotel Londres','Londres',f'{YEAR}-11-09',f'{YEAR}-11-12','Hotel','Anexe voucher da reserva e comprovantes. Data e horário exatos de chegada dependem do transporte.',[]),
    ('Viagem Londres → Madrid','Londres',f'{YEAR}-11-12T06:00','','Voo','Saída às 06h. Aeroporto, voo e horário de chegada a Madrid a informar. Anexe passagens e comprovantes.',['Saída de Londres para Madrid']),
    ('Hotel Madrid','Madrid',f'{YEAR}-11-12','','Hotel','Anexe voucher, se houver reserva (ou guarda de bagagens). Chegada em 12/11 e partida às 22h.',[]),
    ('Viagem Madrid → Fortaleza','Madrid',f'{YEAR}-11-12T22:00','','Voo','Partida às 22h. Anexe passagem, cartão de embarque e comprovantes. Planejar chegada ao aeroporto com antecedência adequada.',['Retorno a partir de Madrid']),
]
# Chegadas que passam a fazer parte da etapa de viagem correspondente.
OBSOLETAS = ['Chegada a Paris','Chegada a Londres — data e horário a confirmar','Chegada a Madrid — horário a confirmar']

def _backup(c):
    import sqlite3,time
    from pathlib import Path
    row=next((r for r in c.execute('PRAGMA database_list').fetchall() if r[1]=='main'),None)
    if not row or not row[2]:return
    dest=Path(row[2]).with_name('backup-before-logistica-'+time.strftime('%Y%m%d-%H%M%S')+'.db')
    out=sqlite3.connect(dest)
    try:c.backup(out)
    finally:out.close()

def _livre(c,eid):
    """Etapa sem arquivos nem comentários pode ser convertida/removida sem perder conteúdo."""
    return not c.execute('SELECT 1 FROM files WHERE entry_id=? UNION SELECT 1 FROM comments WHERE entry_id=?',(eid,eid)).fetchone()

def logistica_docs(c):
    """Uma etapa de logística por voo/viagem e hotel, para anexar passagens e vouchers."""
    if c.execute("SELECT 1 FROM migrations WHERE name='europe-logistica-docs-v1'").fetchone():return
    if not c.execute("SELECT 1 FROM migrations WHERE name='europe-itinerary-v1'").fetchone():return
    admin=c.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    trip=c.execute("SELECT id FROM trips WHERE name='Europa' ORDER BY id LIMIT 1").fetchone()
    if not admin or not trip:return
    tid=trip[0]
    def find(title):return c.execute("SELECT id FROM entries WHERE trip_id=? AND kind='logistics' AND title=? ORDER BY id LIMIT 1",(tid,title)).fetchone()
    for title,place,start,end,category,description,olds in ETAPAS:
        if find(title):continue
        old=next((r for r in map(find,olds) if r and _livre(c,r[0])),None)
        if old:c.execute('UPDATE entries SET title=?,place=?,start=?,end=?,description=?,category=? WHERE id=?',(title,place,start,end,description,category,old[0]))
        else:c.execute('INSERT INTO entries(kind,title,place,start,end,description,category,user_id,trip_id) VALUES(?,?,?,?,?,?,?,?,?)',('logistics',title,place,start,end,description,category,admin[0],tid))
    for title in OBSOLETAS:
        row=find(title)
        if row and _livre(c,row[0]):c.execute('DELETE FROM entries WHERE id=?',(row[0],))
    c.execute("INSERT INTO migrations VALUES('europe-logistica-docs-v1')")

def seed(c):
    if c.execute("SELECT 1 FROM migrations WHERE name='europe-itinerary-v1'").fetchone() and not c.execute("SELECT 1 FROM migrations WHERE name='europe-logistica-docs-v1'").fetchone():
        try:_backup(c)
        except Exception:pass
    _seed_base(c)
    logistica_docs(c)
    from roma2026 import apply
    apply(c)
    from roma2026 import apply_file
    apply_file(c,'paris2026.json','europa-paris-champagne-202611-v1','paris')
    apply_file(c,'roma_four_days.json','europa-roma-four-days-202610-v1','roma-four-days')
    apply_file(c,'london_two_days.json','europa-london-two-days-202611-v1','london-two-days')
    apply_file(c,'london_without_museums.json','europa-london-no-museums-v1','london-no-museums')
    apply_file(c,'paris_five_days.json','europa-paris-five-days-202611-v1','paris-five-days')

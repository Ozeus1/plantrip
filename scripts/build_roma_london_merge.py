"""Roma (Sant'Ignazio) e Londres (mescla dos roteiros de referência a pé).

Atualiza guides.json e gera roma_sant_ignazio.json e london_merged.json.
Fotos: scripts/fetch_merge_photos.py. Executar uma única vez sobre o guides.json anterior (git checkout guides.json para refazer).
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'guides.json';guides=json.loads(P.read_text(encoding='utf-8'))
TFL=('TfL — transporte acessível','https://tfl.gov.uk/transport-accessibility/')
REVIEWED='2026-11-14'
patches={}   # key -> [[texto antigo, texto novo]] para descrições já gravadas no banco

def patch(key,field,new):
 g=guides[key];old=g[field]
 if old!=new:patches.setdefault(key,[]).append([old,new]);g[field]=new

def retime(key,start,end):
 """Atualiza a faixa de horário no início de 'duration' preservando o estilo (09:00 ou 9h00)."""
 g=guides[key];m=re.match(r'(\d{1,2})([:h])(\d{2})–(\d{1,2})[:h](\d{2})',g['duration'])
 if not m:raise ValueError(key)
 sep=m.group(2);a,b=start[-5:],end[-5:];rng=f'{a[:2]}{sep}{a[3:]}–{b[:2]}{sep}{b[3:]}'
 g['duration']=rng+g['duration'][m.end():]

# ------------------------------------------------------------------ ROMA
ROME_DAY1=[('roma-centro','14:00','14:35'),('roma-adriano','14:50','15:15'),('roma-santignazio','15:25','15:50'),('roma-pantheon','16:00','16:45'),('roma-sanluigi','17:00','17:30'),('roma-navona','17:40','18:15'),('roma-campo','18:30','19:00')]
ROME_DATE='2026-10-29'
SANT='Igreja de Santo Inácio de Loyola (Sant’Ignazio)'
rome_old=guides['roma-sanluigi']
rome_new=dict(key='roma-santignazio',title=SANT,city='Roma',kicker='Dia 1 · Centro histórico · Parada 3',
 history=['A Igreja de Santo Inácio de Loyola, conhecida como Sant’Ignazio, foi erguida pelos jesuítas no século XVII, no Campo Marzio, e dedicada ao fundador da Companhia de Jesus. A fachada barroca abre para uma pequena praça desenhada no século XVIII, de aspecto quase teatral, que contrasta com o movimento do Pantheon e da Via del Corso, a poucos minutos dali.',
  'O interior é famoso pelos afrescos de Andrea Pozzo, que usam a perspectiva para criar a impressão de uma arquitetura que não existe. Sobre a nave, a glória de Santo Inácio parece abrir o teto em direção ao céu; no cruzamento, uma cúpula que parece real é uma pintura sobre tela plana. Um disco no piso da nave indica o ponto de observação em que a ilusão é mais convincente.',
  'A visita guiada de cerca de uma hora indicada pelo grupo explora esses truques de ótica. Mesmo sem guia, 20 a 30 minutos de observação já permitem compreender o efeito e seguir ao Pantheon, na mesma região do centro.'],
 stops=[dict(title='Praça de Sant’Ignazio',text='Observe a fachada e o desenho da pequena praça antes de entrar; o piso de pedra pede atenção a desníveis.'),
  dict(title='Disco no piso e teto de Pozzo',text='Procure o ponto de observação na nave e olhe o teto a partir dele, sem bloquear o fluxo de visitantes.'),
  dict(title='Falsa cúpula e saída ao Pantheon',text='Compare a cúpula pintada com a arquitetura real e siga em seguida ao Pantheon, a poucos passos.')],
 tips=rome_old['tips'],
 arrival='Piazza di Sant’Ignazio, 00186 Roma. Horários locais de Roma. O mapa indica o local, não garante uma rota acessível. Confirmar a entrada sem degraus.',
 duration='15:25–15:50 no roteiro, incluindo observação e pausas',
 booking='Visita ordinária à igreja geralmente gratuita; é local de culto, com horários e missas próprios. Confirmar a abertura em 29/10 (quinta-feira) e evitar entrar durante celebração. A visita guiada de cerca de 1 hora indicada pelo grupo é um produto de terceiros: conferir preço, idioma, ponto de encontro e acessibilidade antes de reservar; não é necessária para a visita livre.',
 accessibility='Confirmar com a igreja a entrada sem degraus e o piso interno. A praça tem pavimento irregular. Em dias concorridos, escolher um ponto lateral na nave para ver o teto sem bloquear a passagem.',
 photo_tip='Observe uma vista geral e um detalhe. Fotografe sem bloquear o percurso e respeite as regras do local; as fotos do guia são referências, não registros da viagem.',
 sources=[dict(title='Turismo Roma — igreja de Santo Inácio',url='https://www.turismoroma.it/en/places/church-st-ignatius-loyola'),dict(title='Sant’Ignazio — referência histórica',url='https://en.wikipedia.org/wiki/Sant%27Ignazio,_Rome')],
 reviewed=REVIEWED,photo_query='intitle:"Sant\'Ignazio" Roma',rome_day=1,rome_sequence=3,day_name=rome_old['day_name'],day_note=rome_old['day_note'],photos=guides.get('roma-santignazio',{}).get('photos',[]),food=rome_old['food'],route_summary=json.loads(json.dumps(rome_old['route_summary'])))
rome_new['intro']=rome_new['history'][0]
guides['roma-santignazio']=rome_new
places=['Fontana di Trevi','Templo de Adriano e Piazza di Pietra',SANT,'Pantheon','San Luigi dei Francesi','Piazza Navona','Campo de’ Fiori']
for seq,(key,a,b) in enumerate(ROME_DAY1,1):
 g=guides[key];g['rome_sequence']=seq;g['kicker']=re.sub(r'Parada \d+',f'Parada {seq}',g['kicker'])
 if key!='roma-santignazio':retime(key,ROME_DATE+'T'+a,ROME_DATE+'T'+b)
for g in guides.values():
 if g.get('rome_day'):g['route_summary'][0]['places']=places
guides['roma-adriano']['stops'][-1]['text']='Somente se a programação e o acesso estiverem confirmados; seguir depois à Igreja de Santo Inácio, a poucos passos.'
VITT_EXTRA='Dados consultados pelo grupo no Google Maps: telefone +39 06 6999 4211; o horário exibido na consulta indicava abertura até 19h30 — confirmar no dia.'
if VITT_EXTRA not in guides['roma-vittoriano']['booking']:guides['roma-vittoriano']['booking']=guides['roma-vittoriano']['booking'].rstrip()+' '+VITT_EXTRA
def rome_stage(key,a,b,seq):
 g=guides[key];d=dict(key=key,old_title=g['title'],title=g['title'],place='Roma',start=ROME_DATE+'T'+a,end=ROME_DATE+'T'+b,parada=seq)
 if key=='roma-santignazio':d['description']=f'DIA 1 — CENTRO HISTÓRICO | Parada {seq}: {SANT}.\n\n'+g['booking']+'\n\nMobilidade: '+g['accessibility']
 if key=='roma-vittoriano':d['append']=VITT_EXTRA
 elif key in patches:d['replace']=patches[key]
 return d
rome_stages=[rome_stage(k,a,b,i) for i,(k,a,b) in enumerate(ROME_DAY1,1)]
rome_stages.append(rome_stage('roma-vittoriano','09:30','10:05',2))
rome_stages[-1].update(start='2026-10-30T09:30',end='2026-10-30T10:05');del rome_stages[-1]['parada']
(ROOT/'roma_sant_ignazio.json').write_text(json.dumps(dict(common='Ajuste do roteiro de Roma: Igreja de Santo Inácio de Loyola incluída no dia 1 (29/10), entre a Piazza di Pietra e o Pantheon; as paradas seguintes foram deslocadas em 30 minutos. O Altar da Pátria e Vittoriano já consta em 30/10. Horários sugeridos, sujeitos a confirmação.',stages=rome_stages),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

# ------------------------------------------------------------------ LONDRES
DAY={1:('2026-11-09','Buckingham, Westminster e South Bank'),2:('2026-11-10','Torre de Londres, pontes e Bankside')}
PLAN={1:[('londres-buckingham','10:00','10:35'),('londres-stjames','10:45','11:20'),('londres-mall','11:30','11:45'),('londres-trafalgar','11:50','12:50'),('londres-horseguards','13:00','13:10'),('londres-downing','13:15','13:25'),('londres-westminster','13:35','14:50'),('londres-cabines','15:00','15:10'),('londres-bigben','15:10','15:25'),('londres-parlamento','15:25','15:40'),('londres-westminsterbridge','15:45','16:00'),('londres-southbank','16:10','17:30')],
 2:[('londres-potters','09:00','09:10'),('londres-towerbridge','09:15','09:40'),('londres-stkatharine','09:45','09:55'),('londres-tower','10:10','12:30'),('londres-londonbridge','12:45','13:00'),('londres-southwark','13:05','13:20'),('londres-borough','13:25','14:10'),('londres-clink','14:15','14:25'),('londres-globe','14:30','14:40'),('londres-millennium','14:45','15:05'),('londres-city','15:15','16:15'),('londres-onenewchange','16:20','16:40')]}
base=guides['londres-city']
COMMON=base['route_footnote'].split(' Roteiro mesclado')[0]+' Roteiro mesclado com os roteiros de referência a pé indicados pelo grupo (Whitehall e South Bank no dia 9; Potters Fields, Bankside e St Paul’s no dia 10); a visita ao museu do segundo roteiro de referência não foi incluída porque museus foram retirados do roteiro.'
FOOD={1:'Almoço rápido proposto de 11h50 a 12h50 na região de Trafalgar Square/Strand, antes de Whitehall e da Abadia. Conferir acesso nivelado, mesa e sanitário. Reservar cerca de uma hora e prever £20–35 por pessoa como orçamento inicial, não cotação. Jantar próximo ao hotel, evitando novo deslocamento longo depois do pôr do sol.',
 2:'Almoço proposto de 13h25 a 14h10 no Borough Market ou em restaurante vizinho (Borough High Street/Southwark Street). 10/11 é terça-feira: o mercado pode ter menos bancas, então conferir o calendário e manter um restaurante com mesa e banheiro acessível como alternativa. Orçamento inicial £20–35 por pessoa, sujeito ao cardápio. O Fifteen citado no vídeo fechou e não é opção de reserva.'}
TIPS=base['tips']
def L(key,title,day,start,end,history,stops,booking,access,address,query,sources,tips=None,arrival=None):
 date,label=DAY[day];guides[key]=dict(guides.get(key,{}),key=key,title=title,city='Londres',history=history,intro=history[0],
  stops=[dict(title=t,text=x) for t,x in stops],tips=(tips or [])+TIPS,
  arrival=(arrival or address)+'. Horários locais. O mapa aponta a atração, não uma rota acessível garantida.',duration=start+'–'+end+' no roteiro; ajustar ao ritmo e às reservas.',booking=booking,accessibility=access,
  photo_tip=base['photo_tip'],photos=guides.get(key,{}).get('photos',[]),photo_query=query,map_query=address+', London',sources=[dict(title=t,url=u) for t,u in sources]+[dict(title=TFL[0],url=TFL[1])],
  reviewed=REVIEWED,route_title=base['route_title'],london_day=day,route_day=day,alternatives=base['alternatives'],alternatives_intro=base['alternatives_intro'])
NEW={}
T={k:(a,b) for d in PLAN for k,a,b in PLAN[d]}
def N(key,title,day,*args,**kw):
 NEW[key]=1;L(key,title,day,T[key][0],T[key][1],*args,**kw)

N('londres-mall','The Mall e Admiralty Arch',1,
 ['The Mall é a avenida processional que liga o Palácio de Buckingham a Trafalgar Square. O traçado atual, com o pavimento avermelhado e o Victoria Memorial em uma das extremidades, foi concebido no início do século XX como memorial à rainha Vitória e como cenário de cortejos oficiais. Caminhar por ela ajuda a entender a geografia cerimonial de Londres, entre palácio, parques e praça.',
  'Na outra extremidade fica o Admiralty Arch, edifício edwardiano de Aston Webb concluído em 1912, cujo grande arco central marca a passagem entre The Mall e Trafalgar Square. Para o grupo, a proposta é um trecho curto e fotográfico, observando a perspectiva do arco a partir do nível da rua, sem atravessar vias de tráfego fora das travessias sinalizadas. Em dias de cerimônia, ensaios ou eventos, trechos podem ser fechados.'],
 [('Saída do parque','Deixar St James’s Park pela ligação em nível até The Mall, observando a avenida e o Victoria Memorial ao fundo.'),('Perspectiva da avenida','Fotografar o alinhamento de árvores, bandeiras e pavimento sem ocupar a pista nem as calçadas estreitas.'),('Admiralty Arch','Ver o arco a partir da calçada; a travessia para Trafalgar Square deve usar somente passagens sinalizadas.')],
 'Percurso externo em via pública, sem ingresso e sem horário de abertura. A visita interna ao Admiralty Arch não faz parte do roteiro. Em dias de cerimônia, ensaio ou evento, trechos da avenida podem ser fechados; confirmar avisos locais antes de sair.',
 'Calçadas largas na avenida, mas com cruzamentos movimentados e meios-fios; escolher travessias com rebaixamento. Em caso de chuva ou cansaço, encurtar o trecho e seguir de táxi adaptado até Trafalgar Square.',
 'The Mall / Admiralty Arch','intitle:"Admiralty Arch" London',[('The Mall — referência histórica','https://en.wikipedia.org/wiki/The_Mall,_London'),('Admiralty Arch — referência histórica','https://en.wikipedia.org/wiki/Admiralty_Arch')])

N('londres-trafalgar','Trafalgar Square e National Gallery — exterior',1,
 ['Trafalgar Square é uma das grandes praças cívicas de Londres, projetada no século XIX para lembrar a vitória naval de 1805. A Coluna de Nelson, as fontes e os quatro leões de bronze organizam o espaço, e o quarto pedestal, no canto noroeste, recebe obras de arte contemporânea temporárias. É ponto de encontro e de manifestações, de modo que o ambiente muda muito conforme o dia.',
  'No lado norte fica a National Gallery, museu de entrada gratuita no acervo permanente. Como o grupo retirou museus do roteiro, a proposta é olhar a fachada e a praça pelo exterior, fazer um almoço rápido na região e seguir para Whitehall. A igreja de St Martin-in-the-Fields, no canto leste, é uma pausa possível para banheiro e café, conforme o funcionamento do dia.'],
 [('Coluna de Nelson e leões','Reconhecer o eixo da praça e escolher um ponto de fotografia sem escadas.'),('Fachada da National Gallery','Observar o exterior; a entrada no museu fica fora do roteiro a pedido do grupo.'),('Almoço rápido','Escolher restaurante da região com mesa, acesso nivelado e banheiro; reservar cerca de uma hora.')],
 'Praça pública sem ingresso. A National Gallery tem acervo permanente gratuito, mas museus foram retirados do roteiro: só o exterior está previsto. Manifestações, eventos e montagens podem fechar partes da praça. Almoço sem reserva: orçamento inicial £20–35 por pessoa, não cotação.',
 'A praça tem desníveis e escadarias, com rampas e travessias em nível em partes; confirmar o caminho mais plano no local. Verificar acesso, largura da mesa e sanitário do restaurante antes de sentar; evitar fila longa em pé.',
 'Trafalgar Square','intitle:"Trafalgar Square" London',[('Trafalgar Square — referência histórica','https://en.wikipedia.org/wiki/Trafalgar_Square'),('National Gallery','https://www.nationalgallery.org.uk/')])

N('londres-horseguards','Horse Guards (Whitehall)',1,
 ['Horse Guards é o edifício do século XVIII que serviu de portão cerimonial entre Whitehall e os palácios e parques reais. Em sua frente, sentinelas montadas da Household Cavalry ficam em guarita, uma cena clássica de Londres que não exige ingresso. A tradição está ligada à guarda do soberano e a cerimônias oficiais.',
  'A parada é rápida e feita na rua: observar os soldados e os cavalos à distância, respeitando as instruções de segurança e sem tocar nos animais nem nas guaritas. Os horários de troca e de cerimônias seguem calendário próprio e não foram garantidos; o roteiro apenas passa por ali no caminho entre Trafalgar Square e Downing Street. Atrás do edifício fica Horse Guards Parade, espaço usado em eventos oficiais.'],
 [('Guaritas em Whitehall','Observar as sentinelas montadas à distância segura e sem bloquear a calçada.'),('Arco e pátio','Olhar o arco de passagem e o pátio sem atravessar áreas restritas.'),('Seguir a Downing Street','Continuar por Whitehall em calçada nivelada, poucos passos adiante.')],
 'Exterior gratuito, sem ingresso. Cerimônias, trocas de guarda e ensaios têm calendário próprio e não estão garantidos para 09/11; conferir antes. Não tocar nos cavalos nem entrar em áreas militares; seguir as orientações dos soldados e da polícia.',
 'Calçada plana em Whitehall, mas com aglomeração perto das guaritas e cavalos próximos; manter distância e espaço para a cadeira. Preferir travessias com semáforo e rebaixamento; evitar a pista.',
 'Horse Guards, Whitehall','intitle:"Horse Guards" Whitehall London',[('Horse Guards — referência histórica','https://en.wikipedia.org/wiki/Horse_Guards_(building)')])

N('londres-downing','Downing Street — vista de Whitehall',1,
 ['Downing Street é a rua da residência oficial do primeiro-ministro britânico, no número 10, e do gabinete do Tesouro, no número 11. A casa nº 10 é um símbolo do poder político britânico, mas a rua não é uma atração aberta: o acesso é fechado por portões e policiamento, e a visita se resume a olhar da calçada de Whitehall.',
  'Como a vista pública é limitada, a parada deve ser curta e sem expectativa de entrar ou de ver a porta de perto. A segurança pode alterar a circulação, e os policiais orientam o público a manter distância; fotografar com respeito às instruções. Depois, o trajeto segue a pé por Whitehall até Parliament Square, onde ficam a Abadia de Westminster e o Parlamento.'],
 [('Portão em Whitehall','Ver a rua do lado de fora, atrás dos portões; não é possível entrar.'),('Fotos com respeito','Seguir as orientações da polícia e não bloquear a calçada.'),('Rumo a Parliament Square','Seguir por Whitehall em calçada nivelada até a Abadia.')],
 'Sem ingresso e sem visita: a rua é fechada ao público e o acesso depende de decisão de segurança. A vista limita-se ao portão em Whitehall e pode ser restrita em dias de evento. Não é necessário reservar nada.',
 'Calçadas planas em Whitehall, mas com tráfego intenso e policiamento; usar somente travessias sinalizadas. A parada é curta e pode ser cortada se a calçada estiver lotada.',
 '10 Downing Street, Whitehall','intitle:"Downing Street" London',[('GOV.UK — 10 Downing Street','https://www.gov.uk/government/history/10-downing-street')])

N('londres-westminsterbridge','Westminster Bridge',1,
 ['A Westminster Bridge liga a margem do Parlamento à South Bank e oferece uma das vistas mais conhecidas da Elizabeth Tower e do Palácio de Westminster. A ponte atual, de ferro e com acabamento gótico, foi inaugurada em 1862 e é pintada de verde, cor associada aos assentos da Câmara dos Comuns; a Lambeth Bridge, mais adiante, é vermelha como a Câmara dos Lordes.',
  'Atravessá-la é a ligação natural entre o dia político, em Whitehall e Westminster, e a margem sul, onde estão o London Eye e o passeio ribeirinho. A calçada é frequentada por muitos turistas e por vendedores, e o piso pode ficar escorregadio em dias de chuva. Perto da cabeceira do lado de Westminster fica a estátua de Boudica e suas filhas, obra de Thomas Thornycroft, outro ponto fotográfico.'],
 [('Estátua de Boudica','Observar o monumento perto do início da ponte e seguir pela calçada em nível.'),('Vista central','Parar em ponto da calçada com espaço para fotografar o relógio sem bloquear o fluxo.'),('Margem sul','Descer da ponte por rampa ou passagem nivelada até o London Eye, sem usar escadas de acesso à margem.')],
 'Ponte pública sem ingresso, aberta a pedestres. Travessia curta, de cerca de 250 m, sem horário. Obras, eventos e filas de visitantes podem estreitar a calçada; conferir avisos locais e reservar tempo extra em horários de pico.',
 'A calçada é plana, mas pode ser estreita e movimentada; há travessias de rua com semáforo nas duas pontas. Conferir a rampa até a margem sul e evitar as escadas laterais; táxi adaptado é alternativa se o trecho estiver lotado.',
 'Westminster Bridge','intitle:"Westminster Bridge" London',[('Westminster Bridge — referência histórica','https://en.wikipedia.org/wiki/Westminster_Bridge'),('Parlamento — visitas','https://www.parliament.uk/visiting/')])

N('londres-potters','Potters Fields Park',2,
 ['Potters Fields Park é um parque ribeirinho na margem sul do Tâmisa, entre a Tower Bridge e a City Hall, com um dos melhores pontos de vista para a ponte e para a Torre de Londres na outra margem. O espaço ocupa uma antiga área portuária transformada em parque e funciona como ponto de partida tranquilo para o roteiro do segundo dia.',
  'A parada inicial é breve: olhar o rio, a ponte e o horizonte da City antes das multidões e seguir a pé em direção à Tower Bridge pela margem. O gramado e os caminhos podem estar úmidos em novembro, e o vento perto da água pede agasalho. Não há ingresso nem horário de funcionamento fixo, mas o parque pode ter eventos e áreas fechadas temporariamente.'],
 [('Vista da ponte','Escolher ponto do caminho pavimentado com vista da Tower Bridge e do rio.'),('Torre ao longe','Reconhecer a Torre de Londres e a City na margem oposta.'),('Seguir à Tower Bridge','Caminhar pela margem, em piso nivelado, por cerca de cinco minutos.')],
 'Parque público sem ingresso. Eventos, obras ou manutenção podem fechar áreas; conferir a sinalização local. Cafés e banheiros próximos têm funcionamento próprio — confirmar antes de depender deles.',
 'Caminhos pavimentados, mas a grama pode estar úmida em novembro; ficar nos trechos de calçada. Confirmar banheiro acessível próximo antes de seguir; a saída é pela margem para a Tower Bridge, em piso plano.',
 'Potters Fields Park','intitle:"Potters Fields" London',[('Potters Fields Park — referência','https://en.wikipedia.org/wiki/Potters_Fields_Park')],
 tips=['Roteiro de referência indicado pelo grupo: saída às 8h45, a pé, da hospedagem em Bermondsey até Potters Fields (cerca de 15 min, 1,1 km). Ajustar se a hospedagem for outra.'])

N('londres-stkatharine','St Katharine Docks',2,
 ['St Katharine Docks é uma marina e área de lazer ao lado da Tower Bridge, na margem norte, em antigas docas projetadas por Thomas Telford e inauguradas em 1828. Perderam o uso comercial no século XX e foram reaproveitadas como porto de lazer, com barcos, restaurantes e edifícios restaurados.',
  'A parada é curta: uma volta pela água para ver os barcos e a mistura de armazéns antigos com prédios modernos. É um respiro entre a Tower Bridge e a Torre de Londres, com pausa possível para café ou banheiro. Algumas passarelas e pontes giratórias exigem atenção; escolher caminhos largos e evitar os desníveis das docas.'],
 [('Entrada pela Tower Bridge','Descer em direção às docas por caminho nivelado e conferir o acesso mais plano.'),('Barcos e armazéns','Olhar a água e os edifícios restaurados sem se aproximar das bordas.'),('Rumo à Torre','Seguir por pavimento plano até a Torre de Londres, poucos minutos a pé.')],
 'Área pública de acesso livre, sem ingresso. Restaurantes, cafés e banheiros têm horários próprios; eventos e feiras podem alterar a circulação. Não é necessário reservar para o passeio breve.',
 'Caminhos pavimentados em torno das docas, mas com pequenos desníveis, pontes e bordas de água; usar apenas trechos largos e planos e manter distância da água. Conferir sanitário acessível próximo antes de seguir.',
 'St Katharine Docks','intitle:"St Katharine Docks" London',[('St Katharine Docks — referência histórica','https://en.wikipedia.org/wiki/St_Katharine_Docks')])

N('londres-southwark','Catedral de Southwark',2,
 ['A Catedral de Southwark é uma igreja gótica ao lado da London Bridge, cuja origem remonta ao priorado medieval de St Mary Overie e que só recebeu o título de catedral em 1905. O edifício, com partes do século XIII, é um dos mais antigos de Londres e fica no meio do movimento do Borough Market.',
  'Entre as lembranças do interior está um memorial a William Shakespeare, que viveu e trabalhou na região de Bankside, com um vitral e uma escultura em alabastro. A visita é curta, de 15 a 20 minutos, e deve respeitar o culto e o silêncio. Confirmar abertura, eventuais serviços religiosos e a entrada sem degraus antes de seguir.'],
 [('Fachada e entrada','Observar a catedral da calçada e confirmar a entrada sem degraus.'),('Nave e memorial a Shakespeare','Procurar o memorial e o vitral, em silêncio e sem bloquear a circulação.'),('Rumo ao Borough Market','Sair para o mercado, a poucos passos, por calçada plana.')],
 'Visita geralmente gratuita, com doação sugerida; a catedral é local de culto e pode fechar para serviços ou eventos. Confirmar o horário de 10/11 no site oficial e evitar entrar durante celebração. Fotografar sem flash e conforme as regras do local.',
 'Confirmar com a catedral a entrada sem degraus e o percurso interno no dia. Evitar cruzar a nave durante cerimônias. As calçadas externas ficam movimentadas na hora do almoço.',
 'Southwark Cathedral','intitle:"Southwark Cathedral" London',[('Catedral de Southwark','https://cathedral.southwark.anglican.org/'),('Southwark Cathedral — referência histórica','https://en.wikipedia.org/wiki/Southwark_Cathedral')])

N('londres-borough','Borough Market — almoço',2,
 ['O Borough Market é um dos mercados de alimentos mais tradicionais de Londres, com raízes que remontam à Idade Média, e ocupa, em sua forma atual, edifícios do século XIX junto à London Bridge. Reúne bancas de produtores, pães, queijos, carnes, doces e comida pronta, além de restaurantes no entorno.',
  'No roteiro, é a pausa de almoço e lanche, de cerca de 45 minutos. 10/11 é terça-feira: nos primeiros dias da semana o mercado pode operar com menos bancas e horário reduzido, por isso é importante conferir o calendário antes e manter um restaurante vizinho como alternativa. Em horários de pico, os corredores ficam estreitos e cheios, exigindo paciência para a cadeira motorizada.'],
 [('Escolha da refeição','Definir bancas ou restaurante antes de entrar, para evitar circular na multidão.'),('Corredores e mesas','Procurar mesa com espaço para a cadeira e banheiro acessível; evitar comer em pé.'),('Saída para Bankside','Seguir por Southwark Street ou Clink Street em piso nivelado depois da pausa.')],
 'Entrada livre, sem ingresso; preços e funcionamento das bancas variam. 10/11 é terça-feira, quando o mercado pode ter menos bancas ou horário reduzido: confirmar no site oficial. Orçamento inicial £20–35 por pessoa, não cotação; considerar reserva em restaurante vizinho se o grupo quiser sentar.',
 'O piso é nivelado em boa parte, mas os corredores podem ser estreitos e lotados; escolher horário ou bancas com espaço. Confirmar banheiro acessível e mesa adequada antes de sentar. Se o mercado estiver cheio, usar restaurante vizinho com acesso nivelado.',
 'Borough Market','intitle:"Borough Market" London',[('Borough Market','https://boroughmarket.org.uk/'),('Borough Market — referência histórica','https://en.wikipedia.org/wiki/Borough_Market')])

N('londres-clink','Golden Hinde e Clink Street',2,
 ['A Clink Street é uma rua estreita de Bankside, junto à margem sul do Tâmisa, que preserva ruínas do Palácio dos Bispos de Winchester, incluindo parte de uma grande janela medieval. O nome está associado à antiga prisão da região, hoje lembrada em um museu que não faz parte do roteiro. A rua mostra uma Londres anterior à reurbanização do rio.',
  'Na mesma área, no cais de St Mary Overie, está a Golden Hinde, réplica em tamanho real do galeão em que Francis Drake circunavegou o globo no século XVI. A parada é de passagem, de cerca de 10 minutos, olhando a réplica e as ruínas do lado de fora; subir a bordo exigiria bilhete e tempo, e não está previsto. A rua é estreita e pode ficar cheia no horário do almoço.'],
 [('Ruínas de Winchester Palace','Olhar a janela medieval do lado de fora, em calçada estreita e sem bloquear a passagem.'),('Golden Hinde','Ver a réplica do galeão no cais, sem embarque no roteiro.'),('Seguir ao Globe','Continuar pela margem até o teatro, em piso plano e rota acessível confirmada no local.')],
 'Parada externa gratuita. A visita a bordo da Golden Hinde e o museu da prisão têm ingressos próprios e não fazem parte do roteiro. Conferir se a rua está aberta em 10/11 e se há eventos que alterem o fluxo.',
 'Clink Street é estreita, com calçadas curtas e fluxo de pedestres; escolher o lado mais livre e avaliar se a passagem é confortável com a cadeira. Evitar desníveis no cais; se a rua estiver cheia, seguir pela orla até o Globe.',
 'Clink Street / St Mary Overie Dock','intitle:"Golden Hinde"',[('Golden Hinde','https://www.goldenhinde.com/'),('Winchester Palace — referência histórica','https://en.wikipedia.org/wiki/Winchester_Palace')])

N('londres-globe','Shakespeare’s Globe',2,
 ['O Shakespeare’s Globe é uma reconstrução do teatro elisabetano em que Shakespeare trabalhou, erguida em Bankside, perto do local original, e inaugurada em 1997. A obra nasceu de uma campanha liderada pelo ator e diretor americano Sam Wanamaker e usa técnicas e materiais inspirados nos do século XVI, incluindo um teto de palha.',
  'A parada é externa: observar a fachada de madeira e o teto de palha do outro lado da rua ou da orla, tirar fotos e seguir a pé pela margem até o Millennium Bridge. Visitas internas e espetáculos têm ingresso e horário próprios e não fazem parte do roteiro de dois dias; ao planejar uma peça, é preciso consultar a programação e o acesso para cadeira de rodas.'],
 [('Fachada e teto de palha','Olhar o conjunto do lado de fora, em calçada nivelada.'),('Bankside','Aproveitar a margem do Tâmisa para fotografar o rio e a Catedral de St Paul ao fundo.'),('Rumo ao Millennium Bridge','Seguir pela orla em piso plano, por cerca de 10 minutos.')],
 'Exterior gratuito. Visitas guiadas e espetáculos têm ingresso, calendário e política de acessibilidade próprios; não estão incluídos. Para assistir a uma peça, consultar a programação oficial e a reserva de espaço para cadeira de rodas.',
 'A orla de Bankside é plana, mas tem movimento de pedestres; usar o trecho mais largo. Se houver interesse em visita ou espetáculo, confirmar com o teatro as condições de acesso e de lugares para cadeiras motorizadas.',
 'Shakespeare’s Globe, Bankside','intitle:"Shakespeare\'s Globe" London',[('Shakespeare’s Globe','https://www.shakespearesglobe.com/'),('Shakespeare’s Globe — referência histórica','https://en.wikipedia.org/wiki/Shakespeare%27s_Globe')])

N('londres-onenewchange','One New Change — terraço',2,
 ['One New Change é um centro comercial projetado pelo arquiteto Jean Nouvel, a poucos passos da Catedral de St Paul, cuja cobertura funciona como terraço panorâmico de acesso livre. De lá é possível ver a cúpula da catedral de um ponto de vista mais alto e a cidade ao redor, uma boa forma de encerrar o passeio.',
  'A parada, de cerca de 20 minutos, depende da abertura do terraço e do funcionamento do elevador em 10/11, que devem ser confirmados antes. Em novembro o fim da tarde escurece cedo: o horário previsto, depois da visita a St Paul’s, pega o anoitecer e as luzes da cidade. Se o terraço estiver fechado, ver a catedral pela praça é suficiente.'],
 [('Elevador ao terraço','Confirmar com o centro comercial o acesso por elevador e o horário do terraço.'),('Vista da cúpula','Escolher um ponto com espaço para a cadeira e fotografar a cúpula e a City sem bloquear a passagem.'),('Retorno','Voltar ao hotel de táxi adaptado ou de transporte com rampa; não presumir acesso sem degraus nas estações próximas.')],
 'Terraço público de acesso livre, sem ingresso, mas com horário e acesso sujeitos à administração do centro comercial. Confirmar a abertura em 10/11 e o funcionamento do elevador. Lojas e restaurantes têm horários próprios; o terraço pode fechar por vento ou evento.',
 'O acesso ao terraço é feito por elevador ou escada; confirmar, antes de subir, que o elevador está em serviço e comporta a cadeira. Os corredores do centro comercial são amplos, mas o terraço pode ter piso úmido e ventoso em novembro.',
 'One New Change, Cheapside','intitle:"One New Change" London',[('One New Change','https://www.onenewchange.com/'),('One New Change — referência','https://en.wikipedia.org/wiki/One_New_Change')])

# Ajustes de texto nos guias existentes (horários e fluxo mudaram).
patch('londres-westminster','booking',guides['londres-westminster']['booking'].replace('11h45 é proposta','13h35 é proposta').split(' A última entrada turística')[0]+' A última entrada turística costuma ocorrer no meio da tarde; confirmar para 09/11 e reduzir a visita ao exterior, como no roteiro de referência, se o dia atrasar.')
guides['londres-westminster']['stops'][2]=dict(title='Depois da Abadia',text='O almoço já foi feito em Trafalgar; seguir às cabines e ao relógio, mantendo pausa e banheiro acessível.')
guides['londres-southbank']['stops'][0]['text']=guides['londres-southbank']['stops'][0]['text'].replace('15h30','16h10')
guides['londres-southbank']['stops'][2]=dict(title='Waterloo Bridge ao escurecer',text='Seguir pela orla, sem descer escadas até a Thames Path inferior, até a Waterloo Bridge para ver a cidade iluminada.')
if len(guides['londres-southbank']['history'])<3:guides['londres-southbank']['history'].append('Ao fim da tarde, a caminhada segue pela margem sul até a Waterloo Bridge, de onde se vê o rio com a cidade acesa. Em novembro o sol se põe por volta de 16h15, então esta parte acontece ao anoitecer: preferir calçadas bem iluminadas e conferir o caminho nivelado.')
if not any('Jubilee' in t for t in guides['londres-southbank']['tips']):guides['londres-southbank']['tips'].append('Retorno indicado no roteiro de referência: Jubilee line de Waterloo até Bermondsey (duas paradas depois de London Bridge), se a hospedagem for naquela região; ônibus de Londres têm rampa. Conferir elevadores em serviço.')
guides['londres-tower']['stops'][0]['text']=guides['londres-tower']['stops'][0]['text'].replace('09h','10h10')
guides['londres-tower']['stops'][2]=dict(title='Saída para London Bridge',text='A caminhada até London Bridge leva cerca de 14 minutos (1,1 km); usar o banheiro antes de sair e seguir por rota nivelada, com transporte adaptado se necessário.')
guides['londres-towerbridge']['stops'][2]=dict(title='Seguir a St Katharine Docks',text='A marina fica a poucos minutos, em piso plano; de lá segue-se à Torre de Londres.')
guides['londres-londonbridge']['stops'][1]=dict(title='Catedral e mercado',text='Southwark Cathedral e Borough Market ficam a poucos passos; o almoço está previsto para 13h25–14h10.')
guides['londres-londonbridge']['stops'][2]=dict(title='Ligação a Bankside',text='Seguir por Clink Street e pela orla até a Golden Hinde e o Globe, em rota nivelada e sem escadas da margem.')
for day,items in PLAN.items():
 date,label=DAY[day];titles=[]
 for seq,(key,a,b) in enumerate(items,1):
  g=guides[key];g['route_day']=day;g['london_day']=day;g['route_sequence']=seq;g['route_title']=base['route_title'];g['route_footnote']=COMMON;g['food']=FOOD[day]
  g['kicker']=f'Dia {day} · Londres · Parada {seq}'
  if key not in NEW:retime(key,date+'T'+a,date+'T'+b)
  titles.append(g['title'])
 DAY[day]=(date,label,titles)
summary=[dict(day=d,date=DAY[d][0],title=('Buckingham, Westminster e South Bank' if d==1 else 'Torre de Londres, pontes e St Paul’s'),places=DAY[d][2]) for d in (1,2)]
for key in [k for items in PLAN.values() for k,_,_ in items]:guides[key]['route_summary']=summary

def london_stage(day,seq,key,a,b):
 date,label=DAY[day][:2];g=guides[key];d=dict(key=key,old_title=g['title'],title=g['title'],place='Londres',start=date+'T'+a,end=date+'T'+b,parada=seq)
 if key in NEW:d['description']=f'DIA {day} — {label.upper()} | Parada {seq}: {g["title"]}.\n\n'+g['booking']+'\n\nMobilidade: '+g['accessibility']
 if key in patches:d['replace']=patches[key]
 return d
stages=[london_stage(d,i,k,a,b) for d,items in PLAN.items() for i,(k,a,b) in enumerate(items,1)]
(ROOT/'london_merged.json').write_text(json.dumps(dict(common=COMMON,stages=stages),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
P.write_text(json.dumps(guides,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('guias',len(guides),'novos Londres',len(NEW),'etapas Roma',len(rome_stages),'etapas Londres',len(stages))

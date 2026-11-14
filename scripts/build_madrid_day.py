"""Madri em 12/11/2026: Puerta del Sol, Plaza Mayor, San Miguel, Palácio Real e Primark.

Atualiza guides.json e gera madrid_day.json. Fotos: scripts/fetch_merge_photos.py madrid.
Executar uma única vez sobre o guides.json anterior (git checkout guides.json para refazer).
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'guides.json';guides=json.loads(P.read_text(encoding='utf-8'))
DATE='2026-11-12';LABEL='Centro de Madri';REVIEWED='2026-11-14'
PLAN=[('madrid-centro','10:00','10:40'),('madrid-mayor','10:40','11:20'),('madrid-sanmiguel','11:20','12:30'),('madrid-palacio','12:30','14:00'),('madrid-primark','14:30','16:00')]
TIMES={k:(a,b) for k,a,b in PLAN}
TIPS=['Horários propostos a partir da tabela do grupo (10h00 Puerta del Sol, 10h40 Plaza Mayor, 11h20 Mercado de San Miguel, 12h30 Palácio Real); a Primark fica à tarde. Reservar apenas depois de confirmar a chegada a Madri.',
 'Voo de retorno às 22h: calcular a ida ao aeroporto com a rota atualizada e cortar as últimas paradas, em vez de reduzir a margem de embarque, se o dia atrasar.',
 'Guardar as malas em serviço identificado, se ainda não estiverem no hotel; não há guarda-volume incluído.',
 'Conferir elevadores do metrô e rotas sem degraus; o centro tem pisos de pedra, ladeiras e muita gente. Cuidado com bolsas e mochilas em áreas turísticas.']
COMMON='Madri em 12/11/2026. Horários locais e propostas, não reservas: 10h00 Puerta del Sol, 10h40 Plaza Mayor, 11h20 Mercado de San Miguel com tapas, 12h30 Palácio Real e Plaza de Oriente, e Primark à tarde. Chegada de Londres sem horário confirmado e retorno com partida às 22h: se houver atraso, cortar a partir do fim. Grupo com cadeira motorizada: manter pausas, rotas sem escadas e banheiro acessível. Retiro permanece como alternativa sem data.'
TFL=None
patches={}

def G(key,title,history,stops,booking,access,address,query,sources,duration=None):
 a,b=TIMES[key];old=guides.get(key,{})
 guides[key]=dict(old,key=key,title=title,city='Madrid',history=history,intro=history[0],stops=[dict(title=t,text=x) for t,x in stops],tips=TIPS,
  arrival=address+'. Horários locais de Madri. O mapa aponta a atração, não uma rota acessível garantida.',duration=duration or f'{a}–{b} no roteiro; ajustar ao horário real de chegada',booking=booking,accessibility=access,
  photo_tip='Combinar uma vista geral e um detalhe. Respeitar culto, segurança e regras do local. As imagens do guia não são registros da viagem.',
  photos=old.get('photos',[]),photo_query=query,map_query=address+', Madrid',sources=[dict(title=t,url=u) for t,u in sources],reviewed=REVIEWED)

G('madrid-centro','Puerta del Sol',
 ['Puerta del Sol é um dos grandes espaços de encontro de Madri, no centro geográfico e simbólico da cidade. A placa do quilômetro zero, de onde se contam as estradas radiais da Espanha, o relógio da Casa de Correos, a estátua do urso e do medronheiro e o letreiro de Tío Pepe são as referências que concentram fotos e encontros.',
  'No fim do ano a praça é o cenário da tradição das doze uvas, ao som do relógio da Casa de Correos. Em um dia comum o movimento é intenso, com ruas de pedestres, comércio e estação de metrô ao redor. A parada é curta, de cerca de 40 minutos, serve de ponto de partida do circuito a pé e pede atenção a multidões e a pequenos furtos.'],
 [('Quilômetro zero e Casa de Correos','Localizar a placa no piso, diante do prédio do relógio, e combinar um ponto de encontro para o grupo.'),('Urso e medronheiro','Fotografar a estátua sem bloquear a calçada e com cuidado com bolsas e mochilas.'),('Rumo à Plaza Mayor','Seguir pela Calle Mayor, a poucos minutos, em piso de pedestres.')],
 'Praça pública sem ingresso. Eventos e manifestações podem fechar partes da praça. Alimentação e guarda de bagagens são contratadas separadamente.',
 'Praça ampla e em grande parte plana, mas com multidão e pisos variados; confirmar os elevadores da estação Sol e usar apenas travessias sinalizadas. Evitar circuitos longos com malas.',
 'Puerta del Sol, estação Sol (metrô)','intitle:"Puerta del Sol" Madrid',
 [('Puerta del Sol — turismo oficial','https://www.esmadrid.com/informacion-turistica/puerta-del-sol'),('Puerta del Sol — referência histórica','https://en.wikipedia.org/wiki/Puerta_del_Sol')])
guides['madrid-centro']['kicker']='Madri em um dia · Parada 1'

G('madrid-mayor','Plaza Mayor',
 ['A Plaza Mayor é uma praça regular, fechada por edifícios de três andares com arcadas, projetada no início do século XVII, no reinado de Filipe III. No centro fica a estátua equestre do rei, e a Casa de la Panadería, com a fachada decorada, ocupa o lado norte e é o edifício mais reconhecível do conjunto.',
  'Ao longo dos séculos a praça serviu a mercados, festas, touradas e cerimônias públicas; hoje é lugar de passeio, cafés e comércio turístico. O piso é de pedra e as arcadas ajudam a circular a pé, mas os terraços dos restaurantes e a multidão reduzem o espaço. A visita é curta, de cerca de 40 minutos, entre a Puerta del Sol e o Mercado de San Miguel, que fica a poucos passos.'],
 [('Estátua de Filipe III','Usar a estátua como referência no centro da praça e observar o conjunto de ângulos diferentes.'),('Arcadas e Casa de la Panadería','Percorrer as arcadas e olhar a fachada decorada, mantendo a passagem livre.'),('Saída ao mercado','Sair por um dos arcos em direção ao Mercado de San Miguel, a poucos metros.')],
 'Praça pública sem ingresso. Os terraços de restaurantes ocupam parte do espaço e têm preços próprios; conferir o cardápio antes de sentar. Eventos e feiras sazonais podem alterar a circulação.',
 'Piso de pedra com pequenas irregularidades, mas praticamente plano; as arcadas oferecem trajeto coberto. Alguns arcos de saída têm degraus: escolher a saída em nível e confirmar a rota até o Mercado de San Miguel.',
 'Plaza Mayor','intitle:"Plaza Mayor" Madrid',
 [('Plaza Mayor — turismo oficial','https://www.esmadrid.com/informacion-turistica/plaza-mayor'),('Plaza Mayor — referência histórica','https://en.wikipedia.org/wiki/Plaza_Mayor,_Madrid')])
guides['madrid-mayor']['photos']=[p for p in guides['madrid-centro']['photos'] if 'Plaza_Mayor' in p['source']]
guides['madrid-centro']['photos']=[p for p in guides['madrid-centro']['photos'] if 'Plaza_Mayor' not in p['source']]
guides['madrid-mayor']['kicker']='Madri em um dia · Parada 2'

G('madrid-sanmiguel','Mercado de San Miguel — tapas',
 ['O Mercado de San Miguel é um mercado coberto de ferro e vidro, inaugurado em 1916 junto à Plaza Mayor, e hoje funciona como mercado gastronômico, com bancas de tapas, frutos do mar, queijos, embutidos, doces e vinhos. O edifício preserva a estrutura metálica do início do século XX, que o distingue dos prédios de pedra do entorno.',
  'A parada, de cerca de uma hora e dez minutos, funciona como pausa de almoço com tapas. Os corredores são estreitos e o mercado costuma encher, principalmente nas horas de refeição; o consumo é feito em pé ou em mesas disputadas. Para o grupo, vale chegar cedo, escolher poucas bancas, conferir o espaço para a cadeira e ter um restaurante vizinho como alternativa. Os preços são de mercado turístico.'],
 [('Escolha das bancas','Percorrer a entrada e escolher poucas bancas antes de circular pelos corredores.'),('Tapas e mesa','Procurar mesa com espaço para a cadeira ou levar a refeição a um ponto mais amplo.'),('Rumo ao Palácio Real','Seguir pela região da Calle Mayor até a Plaza de Oriente, de 10 a 15 minutos, com trechos inclinados.')],
 'Entrada livre, sem ingresso; cada banca tem preço e funcionamento próprios. Orçamento inicial de €20–35 por pessoa para tapas e bebida, não cotação. Horário e lotação do mercado variam: confirmar no site oficial e manter um restaurante vizinho como alternativa.',
 'Corredores estreitos e muito movimentados, com pouco espaço para cadeira motorizada em horários de pico; confirmar portas e banheiro acessível antes de entrar. Se estiver cheio, usar restaurante vizinho com mesa e acesso nivelado.',
 'Plaza de San Miguel','intitle:"Mercado de San Miguel" Madrid',
 [('Mercado de San Miguel — referência histórica','https://en.wikipedia.org/wiki/Mercado_de_San_Miguel'),('Madri — turismo oficial','https://www.esmadrid.com/')])
guides['madrid-sanmiguel']['kicker']='Madri em um dia · Parada 3';guides['madrid-sanmiguel']['photos']=[]

G('madrid-palacio','Palácio Real e Plaza de Oriente',
 ['O Palácio Real de Madri foi construído em meados do século XVIII onde ficava o antigo Alcázar, destruído por um incêndio em 1734. É a residência oficial do monarca espanhol, hoje usada sobretudo em cerimônias de Estado, e recebe visitas aos salões, à Armería e a coleções. A fachada de pedra clara domina a Plaza de la Armería.',
  'A Plaza de Oriente, do outro lado, é um jardim formal com estátuas de reis e a estátua equestre de Filipe IV, em frente ao Teatro Real. Nesta proposta o foco é a Plaza de Oriente e o exterior do palácio, com visita interna apenas se o grupo confirmar ingresso, horário e acesso. Perto fica a Catedral da Almudena. A parada é de cerca de 1h30, com pausa e banheiro; a subida desde o mercado tem trechos inclinados.'],
 [('Plaza de Oriente','Caminhar pelos jardins e pela estátua de Filipe IV, com o Teatro Real de um lado e o palácio do outro.'),('Fachada e Plaza de la Armería','Observar o palácio do lado de fora e conferir se há fila ou fechamento por cerimônia.'),('Interior (opcional)','Somente com ingresso, horário e acesso confirmados; a visita pode exigir 1h30 ou mais.')],
 'Exterior e Plaza de Oriente gratuitos. O interior tem ingresso e calendário próprios, com fechamento em dias de cerimônia oficial; confirmar tarifa, horário de 12/11 e gratuidades no site do Patrimonio Nacional. Não comprar antes de confirmar o horário de chegada a Madri.',
 'A região tem trechos inclinados e pisos de pedra; confirmar entrada acessível, elevadores e o roteiro adaptado do palácio. Se o interior não couber no horário, manter só a Plaza de Oriente.',
 'Plaza de Oriente / Palacio Real','intitle:"Plaza de Oriente" Madrid',
 [('Palácio Real — Patrimonio Nacional','https://www.patrimonionacional.es/visita/palacio-real-de-madrid'),('Palácio Real — turismo oficial','https://www.esmadrid.com/informacion-turistica/palacio-real'),('Plaza de Oriente — referência','https://en.wikipedia.org/wiki/Plaza_de_Oriente')])
guides['madrid-palacio']['kicker']='Madri em um dia · Parada 4'
guides['madrid-palacio']['photos']=[p for p in guides['madrid-retiro']['photos'] if 'Palacio_Real' in p['source']]

G('madrid-primark','Primark Gran Vía — compras',
 ['A Primark é uma rede irlandesa de moda e artigos para casa conhecida pelos preços baixos, com várias lojas em Madri. A proposta usa a loja da Gran Vía, no centro, como parada de compras livre depois do Palácio Real, sem exigir deslocamento ao outro lado da cidade. É uma parada de consumo, não uma atração turística.',
  'A Gran Vía é uma das avenidas mais conhecidas de Madri, aberta a partir de 1910, com edifícios de estilos variados, teatros e cinemas, e a caminhada até a loja já funciona como passeio. A loja costuma ficar cheia, com filas de provadores e de caixa. Como o voo de volta sai às 22h, vale decidir antes o orçamento, o peso e o volume das compras, considerando o limite de bagagem da companhia aérea, e reservar margem para recolher as malas e seguir ao aeroporto.'],
 [('Caminhada pela Gran Vía','Seguir da região do Palácio Real à Gran Vía observando a arquitetura, por calçadas largas.'),('Compras','Definir lista e orçamento antes de entrar e combinar um ponto de encontro do grupo dentro da loja.'),('Bagagem e retorno','Verificar peso e volume das compras antes do voo das 22h e planejar o trajeto ao aeroporto.')],
 'Entrada livre, sem ingresso. Horário, promoções e política de devolução são da loja: conferir no site oficial da Primark Espanha. Pagamento em euros; o orçamento de compras é do grupo e não faz parte da estimativa do roteiro. A Primark tem várias lojas em Madri; confirmar endereço e horário da unidade escolhida.',
 'A loja tem vários andares e corredores movimentados: confirmar elevadores, largura dos corredores e provadores acessíveis. Em horários de pico, combinar onde o grupo se encontra, especialmente para quem usa cadeira motorizada.',
 'Gran Vía (loja Primark Gran Vía)','intitle:"Gran Vía" Madrid',
 [('Primark Espanha','https://www.primark.com/es-es'),('Gran Vía — referência histórica','https://en.wikipedia.org/wiki/Gran_V%C3%ADa_(Madrid)')],
 duration='14:30–16:00 no roteiro, a confirmar')
guides['madrid-primark']['kicker']='Madri em um dia · Parada 5';guides['madrid-primark']['photos']=[]

# Retiro vira alternativa sem data; o Palácio Real tem etapa própria.
r=guides['madrid-retiro']
r.update(title='Parque do Retiro — alternativa sem data',kicker='Alternativa sem data',intro='Alternativa para outro momento em Madri: os jardins do Retiro. O Palácio Real agora tem guia e horário próprios no roteiro de 12/11, e o Retiro fica sem data.',
 duration='1 a 1h30, apenas se houver folga e sem data definida',arrival='Retiro: região de Retiro/Estación del Arte.')
r['stops'][1]=dict(title='Palácio Real',text='Já consta no roteiro de 12/11, com guia e horário próprios na Plaza de Oriente.')
r['tips'][0]='O Palácio Real já está no roteiro; esta etapa fica como alternativa sem data para o Retiro.'
r['photos']=[p for p in r['photos'] if 'Palacio_Real' not in p['source']]

titles=[guides[k]['title'] for k,_,_ in PLAN]
summary=[dict(day=1,date=DATE,title=LABEL,places=titles)]
for seq,(key,a,b) in enumerate(PLAN,1):
 g=guides[key];g.update(route_day=1,route_sequence=seq,route_title='Madri em um dia',route_summary=summary,route_footnote=COMMON)

stages=[]
CENTRO_OLD='Somente se houver tempo após pouso e deslocamento. Confirmar guarda de bagagens e duração real da conexão.'
RETIRO_OLD='Escolher apenas uma região conforme tempo disponível. Cancelar se a chegada atrasar; priorizar retorno ao aeroporto para a partida às 22h.'
for seq,(key,a,b) in enumerate(PLAN,1):
 g=guides[key];d=dict(key=key,title=g['title'],place='Madrid',start=f'{DATE}T{a}',end=f'{DATE}T{b}')
 if key=='madrid-centro':
  d['old_title']='Puerta del Sol, Plaza Mayor e centro';d['new_title']=g['title'];d['replace']=[[CENTRO_OLD,'Horário proposto a partir da tabela do grupo; confirmar a chegada a Madri e o retorno ao aeroporto.']]
 else:d['description']=f'DIA 1 — {LABEL.upper()} | Parada {seq}: {g["title"]}.\n\n'+g['booking']+'\n\nMobilidade: '+g['accessibility']
 stages.append(d)
stages.append(dict(key='madrid-retiro',old_title='Retiro ou arredores do Palácio Real — opcional',title=r['title'],new_title=r['title'],place='Madrid',start='',end='',replace=[[RETIRO_OLD,'Fora do roteiro de 12/11 (alternativa sem data): o Palácio Real passou a ter etapa própria.']]))
(ROOT/'madrid_day.json').write_text(json.dumps(dict(common=COMMON,stages=stages),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
P.write_text(json.dumps(guides,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('guias',len(guides),'etapas',len(stages))

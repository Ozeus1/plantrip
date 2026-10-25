"""Informações práticas conferidas e ajustes de apresentação editorial."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
food={1:'Refeição antes de sair e jantar após Campo de’ Fiori. Opções já sugeridas pelo grupo no centro: Armando al Pantheon e Da Gino al Parlamento. Orçamento inicial €25–40 por pessoa, sem cotação atual nem reserva; confirmar cardápio, degraus, largura e banheiro.',2:'Pausa de almoço proposta entre 13h30 e 14h30, depois de Fórum/Palatino e antes do Coliseu. Opções do grupo na região: La Taverna dei Fori Imperiali, Taverna Romana e La Carbonara. Faixa inicial de planejamento €20–40 por pessoa, não preço confirmado; reservar somente após definir o ingresso e validar o acesso.',3:'Almoço e descanso entre Museus e castelo. Opções do grupo em Prati: Osteria Ragno d’Oro, La Locanda di Pietro e Taverna Bacchus. Previsão inicial €25–40 por pessoa, sujeita ao cardápio e sem acessibilidade garantida; não atravessar Roma para comer.',4:'Almoçar por volta de 13h, no setor escolhido entre Popolo e Borghese, deixando margem até a entrada da Galleria. Escolher restaurante após confirmar o acesso do museu e a rota real; prever €20–40 por pessoa como orçamento inicial, não cotação. Mesas externas não garantem banheiro acessível.'}
addresses={'roma-centro':'Piazza di Trevi','roma-adriano':'Piazza di Pietra','roma-pantheon':'Piazza della Rotonda','roma-sanluigi':'Piazza di San Luigi de’ Francesi, 5','roma-navona':'Piazza Navona','roma-campo':'Campo de’ Fiori','roma-campidoglio':'Piazza Venezia','roma-vittoriano':'Piazza Venezia — confirmar acesso Aracoeli','roma-capitolino':'Piazza del Campidoglio','roma-forum':'Área do Fórum Romano — portão conforme percurso acessível e ingresso','roma-palatino':'Área do Palatino — acesso pelo complexo Fórum/Palatino','roma-coliseu':'Piazza del Colosseo — portão no ingresso','vaticano-saopedro':'Piazza San Pietro, Vaticano','vaticano-museus':'Viale Vaticano — entrada dos Museus','roma-castel':'Lungotevere Castello','roma-spagna':'Piazza di Spagna','roma-popolo':'Piazza del Popolo','roma-borghese':'Villa Borghese — definir entrada e setor do parque','roma-galleria':'Piazzale Scipione Borghese, 5'}
for key,v in g.items():
 if not v.get('rome_day'):continue
 v['arrival']=addresses[key]+'. Horários locais de Roma. '+v['arrival']
 v['food']=food[v['rome_day']]
 v['tips']=[t.replace('Nos quatro dias, todas as gratuidades dependem de regras vigentes e documentação; não repetir automaticamente os rótulos das imagens.','Gratuidades dependem de regras e documentação de cada instituição. O primeiro domingo é 01/11, fora das quatro datas principais.') for t in v['tips']]
 v['booking']=v['booking'].replace('Não anunciar tudo como gratuito.','O ingresso do perímetro interno não equivale à observação pela praça.').replace('Não anunciar “Villa Borghese paga” como regra geral.','A visita ao parque tem regras diferentes das do museu.')
g['roma-centro']['photos'].reverse()
g['roma-vittoriano']['booking']='O Vittoriano e áreas públicas indicadas pelo VIVE têm entrada gratuita; terraço panorâmico e outros espaços do circuito têm bilhete próprio, com integral anunciado a €18. Conferir áreas incluídas, tarifa vigente e isenções. O primeiro domingo não se aplica a 29/10. Pessoa com deficiência e acompanhante elegível podem ter gratuidade, mediante documentação.'
g['roma-vittoriano']['duration']='09h30–10h05; visita breve, terraço apenas se couber no restante do roteiro'
g['roma-galleria']['booking']='Ingresso integral publicado a €16, mais taxa de reserva de €2 quando aplicável; exposições e condições especiais podem alterar o preço. Reserva obrigatória inclusive para categorias gratuitas; há isenção da taxa para categorias específicas de deficiência/acompanhante, a validar. 31/10 é sábado, não primeiro domingo. Confirmar os seis bilhetes, documentos e acesso antes do pagamento.'
g['vaticano-museus']['booking']+=' Referência oficial: integral €20 e reduzido €10; reserva online usual acrescenta €5 ao bilhete pago. Verificar procedimento específico das gratuidades; o horário das 10h30 ainda não foi reservado.'
g['vaticano-museus']['sources'].append({'title':'Museus — tarifas oficiais','url':'https://www.museivaticani.va/content/museivaticani/en/organizza-visita/tariffe-e-biglietti.html'})
g['roma-coliseu']['tips'].append('Na operação de inverno, conferir fechamento às 16h30 e última entrada às 15h30. A proposta às 15h exige pontualidade e reserva; se não houver sessão compatível, antecipar o ingresso e reduzir as etapas anteriores.')
g['roma-coliseu']['sources'].append({'title':'Parco — calendário e tarifas atualizados','url':'https://colosseo.it/orari-e-biglietti/'})
for key,v in g.items():
 if not v.get('rome_day'):continue
 for n,photo in enumerate(v['photos']):
  label='Capela Sistina' if key=='vaticano-museus' and n>=2 else 'Santa Maria del Popolo' if key=='roma-popolo' and n>=2 else v['title']
  photo['alt']=label+' — '+('vista geral' if n%2==0 else 'detalhe e perspectiva')
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
q=ROOT/'roma_four_days.json';data=json.loads(q.read_text(encoding='utf-8'))
for stage in data['stages']:
 if stage['key']=='roma-vittoriano':stage['start']='2026-10-29T09:30'
 stage['description']=stage['description'].replace('Não anunciar tudo como gratuito.','O acesso ao perímetro interno tem regra própria.').replace('Não anunciar “Villa Borghese paga” como regra geral.','Parque e museu possuem regras de acesso distintas.')
q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

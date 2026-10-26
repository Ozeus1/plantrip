"""Retira museus do roteiro de Londres e redistribui a tarde, sem apagar conteúdo."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
source=json.loads((ROOT/'london_two_days.json').read_text(encoding='utf-8'))
stages=[]
for key,title in [('londres-tate','Tate Modern — fora do roteiro, sem data'),('londres-british','British Museum — fora do roteiro, sem data')]:
 stages.append(dict(key=key,title=title,old_title=g[key]['title'],place='Londres',start='',end='',description='FORA DO ROTEIRO — museus retirados a pedido do grupo. Sem data ou visita programada. Guia e memórias existentes preservados.'))
g['londres-tate'].pop('london_day',None)
g['londres-tate'].pop('route_summary',None)
g['londres-tate']['intro']='Museu retirado do roteiro de Londres a pedido do grupo. Guia preservado apenas para consulta e memórias.'
g['londres-city']['title']='St Paul’s Cathedral — exterior e visita interna opcional'
g['londres-city']['history'][1]='O interior inclui nave, áreas de memória e cripta, enquanto a subida à cúpula possui condições diferentes. Com a retirada da Tate, a tarde permite chegar mais cedo: a proposta é 15h15–16h15. A visita interna continua opcional, paga e condicionada à reserva e ao acesso; quem preferir pode apreciar a fachada e descansar. Confirmar a operação do dia antes de comprar.'
g['londres-city']['booking']='Exterior gratuito. Interior opcional, com proposta de 15h15–16h15 e ingresso/acesso a confirmar. Última entrada turística habitual às 16h e término cerca de 16h30; antecipar a chegada para segurança e bilheteria. Referência publicada: £27 adulto e £10,50 criança, com concessões e categorias gratuitas a validar. Culto não equivale a visita turística.'
g['londres-city']['stops']=[dict(title='Fachada e cúpula',text='Observar a arquitetura após a travessia do Millennium Bridge.'),dict(title='Interior opcional',text='Proposta de 15h15–16h15; confirmar ingresso, porta acessível e percurso da cadeira. Sem reserva, manter exterior e pausa.'),dict(title='Retorno e descanso',text='Tempo livre depois da catedral, sem novo museu ou deslocamento obrigatório.')]
g['londres-city']['duration']='15h15–16h15; interior opcional conforme reserva e acessibilidade'
g['londres-millennium']['duration']='14h45–15h05, com margem para o acesso sem escadas'
g['londres-millennium']['stops'][0]=dict(title='Ligação por Bankside',text='Depois do almoço, seguir por rota acessível ao Millennium Bridge, sem entrar na Tate.')
for key,start,end in [('londres-millennium','14:45','15:05'),('londres-city','15:15','16:15')]:
 stages.append(dict(key=key,title=g[key]['title'],old_title=next(s['title'] for s in source['stages'] if s['key']==key),place='Londres',start='2026-11-10T'+start,end='2026-11-10T'+end,description='Tarde reorganizada sem museus. Após London Bridge e almoço, seguir por Bankside ao Millennium Bridge e à Catedral de St Paul’s. Interior da catedral opcional, sujeito a ingresso e acesso confirmados. Reservar tempo para segurança, pausas e trajeto sem escadas; não é reserva efetuada.'))
active=[s for s in source['stages'] if s['day'] and s['key']!='londres-tate']
for s in active:
 if s['key']=='londres-city':s['title']=g['londres-city']['title']
summary=[dict(day=d,date='2026-11-'+('09' if d==1 else '10'),title=('Buckingham, Westminster e South Bank' if d==1 else 'Torre de Londres, pontes e St Paul’s'),places=[s['title'] for s in active if s['day']==d]) for d in (1,2)]
for key,v in g.items():
 if not v.get('london_day'):continue
 v['route_summary']=summary
 v['route_sequence']=next(i+1 for i,s in enumerate([s for s in active if s['day']==v['london_day']]) if s['key']==key)
 v['kicker']=f"Dia {v['london_day']} · Londres · Parada {v['route_sequence']}"
 v['alternatives']=[a for a in v.get('alternatives',[]) if not any(x in a['name'] for x in ('British Museum','Sherlock','Madame Tussauds'))]
 v['alternatives_intro']='Museus retirados do roteiro. O segundo dia termina em St Paul’s com tempo para visita interna opcional ou descanso.'
 v['route_footnote']=source['common']+' Museus retirados a pedido do grupo; tarde do dia 10 antecipada para St Paul’s. Guias antigos mantidos apenas como acervo.'
 v['food']=v['food']
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'london_without_museums.json').write_text(json.dumps(dict(common='Ajuste solicitado: Londres sem museus. Preservar arquivos, comentários e vínculos; sem alterações em transportes ou nas outras cidades.',stages=stages),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

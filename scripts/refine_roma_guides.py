"""Sincroniza o conteúdo editorial com o roteiro do grupo."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'guides.json'
g=json.loads(p.read_text(encoding='utf-8'))
data=json.loads((root/'roma2026.json').read_text(encoding='utf-8'))
for item in data['stages']:
    guide=g[item['key']]
    guide['tips']=[item['description']]+[t for t in guide['tips'][1:] if '?' not in t]
    if item['key'] in ('roma-castel','toscana-rural'):
        guide.update(title=item['title'],city=item['place'],kicker='Roma e Toscana — outubro de 2026',intro=item['title'],arrival=item['place'],duration='Conforme roteiro do grupo',booking='Reservas, tarifas e disponibilidade a confirmar.',accessibility='Confirmar percurso, rampas e banheiro para cadeira motorizada.',photo_tip='Registre as paisagens e os momentos compartilhados.')
        guide['tips'] += ['Confirmar acesso da cadeira motorizada antes de contratar serviços.','Horários propostos: ajustar ao descanso e aos deslocamentos.']
g['roma-castel']['history']=['Construído no século II como mausoléu de Adriano, o edifício foi transformado em fortaleza, residência papal e prisão. Sua posição perto do Vaticano marcou os sucessivos usos do monumento ao longo dos séculos.','A antiga Mole Adriana tornou-se Museu Nacional em 1925. A visita permite observar a sobreposição de funções militares, religiosas e residenciais; o percurso interno exige confirmação das áreas acessíveis antes da reserva.']
g['roma-castel']['stops']=[{'title':t,'text':s} for t,s in [('Via della Conciliazione','Prosseguir da Praça de São Pedro com pausas.'),('Exterior e ponte','Observar o monumento e o entorno sem pressupor acesso interno.'),('Museu — opcional','Entrar somente com acessibilidade e ingresso confirmados.')]]
g['roma-castel']['sources']=[{'title':'Museu Nacional de Castel Sant’Angelo','url':'https://direzionemuseiroma.cultura.gov.it/museo-nazionale-di-castel-santangelo/'},{'title':'Ingressos oficiais','url':'https://portale.museiitaliani.it/'}]
g['toscana-rural']['history']=['A paisagem do sul da Toscana reúne agricultura, cidades históricas e tradições vinícolas. O passeio proposto concentra-se em Montepulciano e no Val d’Orcia, com tempo para gastronomia e paisagens, sem acrescentar Florença e Siena ao mesmo dia.','Montepulciano combina um centro de origem medieval com arquitetura renascentista. Pienza está associada ao projeto urbano renascentista de Pio II. Em ambas, o roteiro deve ser escolhido conforme o relevo e as condições reais de circulação da cadeira motorizada.']
g['toscana-rural']['stops']=[{'title':t,'text':s} for t,s in [('Montepulciano','Visita curta, respeitando ladeiras e acessos confirmados.'),('Vinícola familiar a escolher','Degustação com almoço; reserva e acessibilidade pendentes.'),('Pienza e Val d’Orcia','Paisagens e passeio opcional conforme tempo e mobilidade.')]]
g['toscana-rural']['sources']=[{'title':'Turismo oficial da Toscana','url':'https://www.visittuscany.com/en/areas/val-dorcia/'},{'title':'Turismo de Montepulciano','url':'https://www.visittuscany.com/en/towns-and-villages/montepulciano/'}]
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

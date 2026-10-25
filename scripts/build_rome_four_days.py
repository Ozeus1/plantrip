"""Guia dos quatro dias de Roma, com atrações individuais e referências oficiais."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'guides.json'
guides=json.loads(path.read_text(encoding='utf-8'))
stages=[]
COMMON=('Roteiro de Roma em quatro dias, conforme a sequência das imagens: 28/10 centro histórico; 29/10 Roma Antiga; 30/10 Vaticano; 31/10 região norte. '
        'Horários sugeridos, não reservas. Grupo de seis, com cadeira motorizada: prever pausas, pavimento irregular, rampas, sanitários e transporte acessível. '
        'O primeiro domingo será 01/11, fora desses quatro dias; não aplicar sua gratuidade a 28–31/10. '
        'Museus Vaticanos seguem regra própria de último domingo, não primeiro domingo. Audiência papal depende de calendário e bilhete próprio. '
        'Toscana foi retirada de 30/10 e permanece como alternativa sem data, sem perda dos guias e memórias. Saída de Roma mantida em 01/11 às 18h.')
DAYS={1:('28','Centro histórico','Chegada às 06h: deixar malas, almoçar e descansar. Começar apenas se houver disposição; reduzir o roteiro se necessário.'),2:('29','Roma Antiga','Dia exigente. O Coliseu depende de horário marcado: ajustar as etapas anteriores a esse ingresso e à operação de outono.'),3:('30','Vaticano e arredores','Começar cedo por São Pedro. Planejar saída e trajeto externo até os Museus, com margem para filas e almoço.'),4:('31','Região norte','Priorizar deslocamento sem escadarias. Villa é parque público; Galleria é museu com reserva e condições próprias.')}
def add(key,title,day,hour,end,old,history,observations,booking,access,query,sources,duration=None):
    date,label,note=DAYS[day]
    seq=sum(1 for s in stages if s['day']==day)+1
    description=f'DIA {day} — {label.upper()} | Parada {seq}: {title}.\n{note}\n\n'+booking+'\n\nMobilidade: '+access
    stages.append(dict(key=key,old_title=old or title,title=title,place='Roma',start=f'2026-10-{date}T{hour}',end=f'2026-10-{date}T{end}',description=description,day=day,sequence=seq))
    previous=guides.get(key,{})
    g=dict(previous)
    g.update(key=key,title=title,city='Roma',kicker=f'Dia {day} · {label} · Parada {seq}',intro=history[0],history=history,
      stops=[{'title':t,'text':x} for t,x in observations],
      tips=[note,'Horário do roteiro é proposta. Confirme abertura, ingresso e entrada acessível no site oficial.','Combine ponto de encontro fora das passagens, leve água e reserve pausas e margem para a bateria da cadeira.'],
      arrival='O mapa indica o local, não garante uma rota acessível. '+access,duration=duration or f'{hour}–{end} no roteiro, incluindo observação e pausas',booking=booking,accessibility=access,
      photo_tip='Observe uma vista geral e um detalhe. Fotografe sem bloquear o percurso e respeite as regras do local; as fotos do guia são referências, não registros da viagem.',
      sources=[{'title':t,'url':u} for t,u in sources],reviewed='2026-10-25',photo_query=query,rome_day=day,rome_sequence=seq,
      day_name=label,day_note=note,photos=previous.get('photos',[]))
    guides[key]=g

add('roma-centro','Fontana di Trevi',1,'14:00','14:35','Centro histórico: Trevi, Spagna, Condotti e Colonna',
 ['A Fontana di Trevi é uma composição barroca em que água, escultura e arquitetura formam um grande cenário urbano. Projetada por Nicola Salvi e concluída no século XVIII, ocupa a fachada do Palazzo Poli. A figura central representa Oceano, acompanhado por cavalos marinhos e tritões: não se trata apenas de uma fonte isolada, mas de um teatro de pedra integrado à cidade.',
  'A presença da água remete ao antigo abastecimento romano ligado à Aqua Virgo. Na praça, compare a monumentalidade da fachada com a escala das ruas que chegam ao local. A tradição de lançar uma moeda é parte da cultura turística, enquanto a leitura das figuras revela o programa artístico. Na tarde da chegada, uma observação tranquila pela parte superior pode ser mais adequada que descer ao perímetro interno.'],
 [('Vista da praça','Reconheça a fachada do Palazzo Poli antes de se aproximar da borda.'),('Oceano e figuras marinhas','Compare os cavalos e a movimentação dos tritões com as rochas e a água.'),('Rumo à Piazza di Pietra','Siga para o Templo de Adriano, com tempo para piso de pedra e multidões.')],
 'Visão a partir do espaço público e acesso ao perímetro interno são diferentes. Desde 02/02/2026, o perímetro interno tem ingresso de €2 para visitantes sujeitos à tarifa; verificar isenções de deficiência/acompanhante e procedimento oficial. Não anunciar tudo como gratuito.',
 'Evitar degraus até a borda; solicitar indicação do percurso permitido à cadeira motorizada. O piso pode estar molhado e a praça fica congestionada. A observação externa é alternativa válida.',
 'intitle:"Trevi" fountain', [('Trevi — visita e tarifas','https://www.fontanaditrevi.roma.it/en'),('Turismo Roma — novo acesso','https://www.turismoroma.it/en/news/trevi-fountain-new-entry-fee-one-romes-symbols')])

add('roma-adriano','Templo de Adriano e Piazza di Pietra',1,'14:50','15:15',None,
 ['As colunas do antigo templo dedicado a Adriano sobrevivem incorporadas a uma construção posterior na Piazza di Pietra. O monumento foi concluído sob Antonino Pio, sucessor do imperador, e mostra como Roma reutilizou estruturas antigas em edifícios de outras épocas. A escala das colunas ajuda a imaginar a presença do santuário no Campo de Marte.',
  'O local também é apresentado como Templo de Víbia Sabina e Adriano, recuperando a memória do casal imperial. Hoje o edifício está associado à Câmara de Comércio de Roma e recebe programação própria. Distinguir a leitura exterior das colunas de uma eventual exposição ou experiência interna evita comprar ingresso desnecessário ou assumir que o espaço esteja sempre aberto.'],
 [('Colunata','Observe altura, capitéis e o contraste entre a pedra antiga e a fachada posterior.'),('Piazza di Pietra','Use a praça para compreender a dimensão do edifício sem bloquear as passagens.'),('Interior, se disponível','Somente se a programação e o acesso estiverem confirmados; seguir depois ao Pantheon.')],
 'Observar as colunas pelo exterior não exige ingresso de atração. A indicação de “pago” da imagem não vale automaticamente para a praça: exposições, eventos ou visitas internas têm regras próprias a consultar.',
 'Há piso irregular e diferenças de nível entre rua e ruínas. Para uma visita interna, confirmar soleira, rampa, circulação e banheiro; não inferir acessibilidade a partir da vista externa.',
 'intitle:"Temple of Hadrian"', [('Turismo Roma — Víbia Sabina e Adriano','https://www.turismoroma.it/it/luoghi/tempio-di-vibia-sabina-e-adriano'),('Câmara de Comércio — sala do templo','https://www.rm.camcom.it/pagina81_sala-del-tempio-di-adriano.html')])

add('roma-pantheon','Pantheon',1,'15:30','16:15','Pantheon e Piazza Navona',
 ['O Pantheon conserva uma das experiências espaciais mais impressionantes da Roma antiga: uma sala circular coberta por uma cúpula monumental, iluminada pelo óculo central. O edifício atual pertence à época de Adriano, embora a inscrição da fachada recorde Agripa. Observe como o pórtico de colunas anuncia uma arquitetura muito diferente do espaço que se revela no interior.',
  'Transformado em igreja no século VII, o monumento ganhou continuidade de uso que contribuiu para sua preservação. A luz muda ao longo do dia, marcando a superfície da cúpula e o pavimento. O local também guarda sepulturas, entre elas a de Rafael. A visita deve respeitar tanto o patrimônio arqueológico quanto a função religiosa: celebrações podem alterar os horários turísticos.'],
 [('Pórtico','Leia a inscrição de Agripa e compare colunas e frontão com a rotunda.'),('Cúpula e óculo','Observe a organização dos caixotões e a luz; não é necessário circular depressa para compreender o espaço.'),('Memória e culto','Identifique os túmulos de interesse e mantenha silêncio antes de seguir a San Luigi.')],
 'Tarifa integral oficial de €7 desde julho/2026; menores de 18 anos e outras categorias têm isenções conforme regras. O benefício etário reduzido não decorre apenas de estudar no Brasil. Primeiro domingo: consultar condições; a visita proposta é quarta-feira, 28/10. Gratuidades de Orlei/Elma dependem de documentação aceita.',
 'Solicitar à equipe a entrada acessível e confirmar o percurso; não usar a fila comum como garantia de acesso sem desnível. Prever piso molhado em chuva, multidões e tempo de segurança.',
 'intitle:"Pantheon" Rome', [('Pantheon — horários e tarifas oficiais','https://direzionemuseiroma.cultura.gov.it/pantheon/'),('Ingressos oficiais Musei Italiani','https://portale.museiitaliani.it/')])

add('roma-sanluigi','San Luigi dei Francesi',1,'16:30','17:00',None,
 ['A igreja da comunidade francesa em Roma reúne arquitetura religiosa e uma visita decisiva para conhecer Caravaggio. Na Capela Contarelli, o pintor representou episódios da vida de São Mateus, aproximando o tema sagrado da experiência humana por meio da luz, dos gestos e das figuras. As telas foram realizadas na passagem do século XVI para o XVII.',
  'A visita ganha profundidade quando se observa o conjunto, em vez de buscar uma única fotografia. Na Vocação de São Mateus, acompanhe a direção da luz e das mãos; nas demais obras, compare a tensão das cenas e a presença dos personagens. O espaço continua sendo uma igreja, com culto e possibilidade de interrupções. A entrada não substitui o respeito ao silêncio e à circulação dos fiéis.'],
 [('Nave','Reconheça o ambiente e procure a Capela Contarelli sem atravessar áreas reservadas.'),('Ciclo de São Mateus','Compare luz, gestos e narrativas das três pinturas de Caravaggio.'),('Saída para Navona','Faça uma pausa curta; o próximo destino está no mesmo setor do centro.')],
 'Visita ordinária à igreja geralmente gratuita. Confirmar horários do dia, celebrações e acesso à capela; não programar entrada durante culto. Eventual iluminação ou serviço não equivale a bilhete geral.',
 'Confirmar com a igreja a solução de entrada sem degraus e a posição para ver as pinturas sentado. A capela pode ficar cheia; evitar apertar o grupo entre visitantes.',
 'intitle:"San Luigi dei Francesi"', [('Turismo Roma — igreja e Caravaggio','https://www.turismoroma.it/it/luoghi/san-luigi-dei-francesi'),('Turismo Roma — referências de visita','https://www.turismoroma.it/')])

add('roma-navona','Piazza Navona',1,'17:10','17:45',None,
 ['A forma alongada da Piazza Navona conserva a memória do estádio de Domiciano, espaço de competições da Roma antiga. Sobre essa base, a cidade criou uma praça barroca de fontes, fachadas e vida cotidiana. A presença do passado não está apenas em uma ruína visível: ela organiza o desenho do lugar e a forma como se circula por ele.',
  'A Fonte dos Quatro Rios, de Bernini, dialoga com a igreja de Sant’Agnese in Agone e com outras fontes da praça. Compare esculturas, obelisco e perspectiva das fachadas. O melhor ritmo para o grupo é atravessar sem pressa, escolhendo pontos de observação e descanso. Áreas arqueológicas e interiores próximos são visitas independentes, não incluídas automaticamente em um passeio gratuito pela praça.'],
 [('Forma do estádio','Observe o eixo comprido da praça e relacione-o ao antigo espaço de jogos.'),('Fontes e fachadas','Compare o conjunto central com as fontes nas extremidades.'),('Pausa e continuação','Escolha uma lateral menos movimentada antes de seguir ao Campo de’ Fiori.')],
 'Praça pública sem ingresso geral. Estádio subterrâneo, exposições e serviços privados são cobrados separadamente, se escolhidos. Não há necessidade de comprá-los para conhecer a praça.',
 'Pavimentação de pedra, concentração de visitantes e obstáculos temporários. Preferir percurso nivelado pelo entorno das fontes e confirmar sanitário em local próximo.',
 'intitle:"Piazza Navona"', [('Turismo Roma — Piazza Navona','https://www.turismoroma.it/it/luoghi/piazza-navona'),('Turismo oficial de Roma','https://www.turismoroma.it/')])

add('roma-campo','Campo de’ Fiori',1,'18:00','18:30',None,
 ['Campo de’ Fiori oferece uma Roma de usos cotidianos, comércio e encontro, com um caráter diferente das praças dominadas por igrejas e palácios monumentais. Seu nome evoca uma paisagem anterior à urbanização consolidada. O mercado e o uso noturno fazem o mesmo espaço mudar de aparência conforme o horário.',
  'A estátua de Giordano Bruno recorda sua execução no local em 1600 e introduz uma reflexão sobre pensamento, poder e memória pública. Na visita proposta, já no fim da tarde, a experiência será de praça e entorno, não de mercado matinal em plena operação. Vale observar fachadas e ruas de ligação, sem acrescentar travessias longas no dia da chegada.'],
 [('Praça e ruas','Reconheça a escala comercial e a ligação com o centro histórico.'),('Giordano Bruno','Observe o monumento e seu papel na memória do lugar.'),('Fim do dia','Jantar na região ou retorno ao hotel; descansar tem prioridade sobre novos desvios.')],
 'Praça pública sem ingresso. O mercado é atividade de horário próprio; não prometer bancas abertas às 18h. Restaurantes ainda a escolher, com preço e acesso confirmados antes de reservar.',
 'Pedras, resíduos após o mercado, mesas e mudanças de circulação podem dificultar a cadeira. Escolher rota lateral confortável e restaurante com banheiro efetivamente acessível.',
 'intitle:"Campo de" Fiori', [('Turismo Roma — Campo de’ Fiori','https://www.turismoroma.it/it/node/1514'),('Turismo oficial de Roma','https://www.turismoroma.it/')])

add('roma-campidoglio','Piazza Venezia',2,'09:00','09:20','Fori Imperiali, Piazza Venezia, Campidoglio e Monti',
 ['Piazza Venezia é um ponto de encontro entre eixos urbanos de épocas diferentes. A presença do Palazzo Venezia e do Vittoriano coloca lado a lado uma Roma de palácios e a representação monumental da Itália unificada. Em vez de tratá-la apenas como passagem, observe como avenidas, fachadas e circulação organizam a chegada ao centro arqueológico.',
  'O nome da praça se relaciona ao palácio associado historicamente a Veneza. O conjunto pode ser lido por fora sem transformar a manhã em uma sequência de museus. A proposta começa aqui e segue para o Altar da Pátria e o Capitólio, avançando depois para Fórum, Palatino e Coliseu. Obras e travessias podem exigir uma ligação diferente daquela sugerida por mapas comuns.'],
 [('Vista geral','Identifique Palazzo Venezia e Vittoriano e a ligação com a Via del Corso.'),('Travessia segura','Use passagens sinalizadas e confirme desvios em vigor.'),('Rumo ao Vittoriano','Não atravesse o trânsito pelo trajeto mais curto se ele não for acessível.')],
 'Observar a praça é gratuito. Palazzo Venezia, museus e terraços têm acesso próprio; escolher apenas o que cabe no horário do Coliseu.',
 'Trânsito intenso e possíveis obras. Confirmar rebaixamentos de calçada e travessia; guardar margem para desvios e não se reunir em ilhas apertadas.',
 'intitle:"Piazza Venezia"', [('Turismo Roma — Piazza Venezia','https://www.turismoroma.it/it/luoghi/piazza-venezia'),('VIVE — visita','https://vive.cultura.gov.it/en/visit')])

add('roma-vittoriano','Altar da Pátria e Vittoriano',2,'09:25','10:05',None,
 ['O Vittoriano foi concebido como monumento a Vittorio Emanuele II e à unidade italiana. Sua escala e o uso do mármore branco criam uma presença muito diferente das ruínas antigas que serão visitadas mais tarde. A composição organiza escadarias, colunas, esculturas e grandes perspectivas sobre a cidade.',
  'O Altar da Pátria e o túmulo do Soldado Desconhecido agregam ao monumento uma dimensão cívica e de memória coletiva. O complexo também possui museu e terraço panorâmico, mas não é necessário visitar todas as áreas para compreender seu papel. Neste roteiro, a observação principal é breve; escolher o mirante exigirá mais tempo e possível redução de outras etapas, sem perder o horário reservado no Coliseu.'],
 [('Fachada e composição','Compare a linguagem monumental com os edifícios ao redor.'),('Memória nacional','Observe o altar com respeito a áreas cerimoniais e restrições locais.'),('Terraço opcional','Somente se ingresso, elevador e tempo estiverem confirmados; não pressupor inclusão.')],
 'Distinguir áreas externas/cerimoniais do ingresso para os espaços e terraços do VIVE. Consultar tarifa vigente e isenções; o primeiro domingo não se aplica à quinta-feira, 29/10. Pessoa com deficiência e acompanhante podem ter gratuidade conforme regras e documentação.',
 'O VIVE informa acesso pelo lado Aracoeli com plataforma e elevador para a Terrazza Italia e elevadores panorâmicos. Confirmar operação, medidas, peso e entrada exata para a cadeira motorizada; não usar a escadaria principal.',
 'intitle:"Vittoriano"', [('VIVE — ingresso e acessibilidade','https://vive.cultura.gov.it/en/visit'),('Terraço panorâmico','https://vive.cultura.gov.it/it/vittoriano/cosa-vedere/terrazza-panoramica')])

add('roma-capitolino','Monte Capitolino e Piazza del Campidoglio',2,'10:15','10:50',None,
 ['O Capitólio é uma das colinas históricas de Roma e um lugar fundamental para compreender a representação do poder na cidade. A praça atual foi reorganizada no Renascimento a partir de um projeto de Michelangelo, que criou uma relação entre fachadas, pavimento e perspectiva. O conjunto transforma a chegada à colina em uma experiência espacial deliberada.',
  'A estátua equestre de Marco Aurélio ocupa o centro da composição; a peça ao ar livre é uma reprodução, enquanto o original pertence aos Museus Capitolinos. Os palácios preservam funções e coleções distintas, e a vista para o Fórum permite antecipar o próximo trecho. A visita proposta é à praça e ao entorno, sem ingresso automático nos museus.'],
 [('Chegada à colina','Escolher a rota compatível com a cadeira, sem supor que toda rampa monumental seja confortável.'),('Praça e Marco Aurélio','Observe o desenho e as relações entre os três palácios.'),('Ligação para o Fórum','Mirante apenas se o trajeto for viável; confirmar entrada acessível do parque arqueológico.')],
 'A praça é visita externa gratuita. Museus Capitolinos são uma visita independente e não cabem como inclusão automática nesta manhã.',
 'A Cordonata tem inclinação e irregularidades. Consultar alternativa pelas vias de acesso à colina; não confundir a escadaria de Aracoeli com rota para cadeira. Mirantes e acessos aos museus exigem conferência separada.',
 'intitle:"Piazza del Campidoglio"', [('Museus Capitolinos — visita e entorno','https://www.museicapitolini.org/en'),('Turismo Roma — Campidoglio','https://www.turismoroma.it/it/luoghi/piazza-del-campidoglio')])

add('roma-forum','Fórum Romano',2,'11:15','12:30',None,
 ['O Fórum Romano foi o principal centro de vida pública da cidade antiga, reunindo atividade política, religiosa, judicial e cerimonial. Suas ruínas não correspondem a um único projeto: edifícios de épocas diferentes foram construídos, alterados e substituídos. Essa sobreposição explica por que um mapa histórico ou uma visita guiada faz tanta diferença na leitura do sítio.',
  'Observe a Via Sacra, os arcos, templos e basílicas como partes de uma rede de circulação e poder. A monumentalidade hoje fragmentada pede imaginação, mas também atenção aos vestígios reais. Para o grupo, o objetivo será um percurso selecionado e acessível, continuando dentro do mesmo complexo para o Palatino. Não é preciso alcançar todos os pontos para compreender o lugar.'],
 [('Entrada e orientação','Conferir portão e percurso indicado pela equipe, usando mapa acessível.'),('Centro cívico','Relacionar templos, basílicas e arcos às funções públicas.'),('Continuação ao Palatino','Permanecer no complexo conforme regras do ingresso; pausa antes da subida.')],
 'Conferir ingresso combinado com Palatino/Coliseu e número de acessos permitidos. Não sair para almoçar supondo reentrada livre no Fórum/Palatino. O roteiro prevê refeição depois dessas duas etapas. Gratuidade de PCD/acompanhante e menor depende das regras oficiais.',
 'Pedras antigas, inclinações e trechos expostos. Solicitar o percurso acessível efetivamente aberto; plataformas e elevadores precisam estar operacionais. Se o esforço for alto, reduzir o Palatino em favor do Coliseu reservado.',
 'intitle:"Roman Forum"', [('Parco del Colosseo — Fórum Romano','https://colosseo.it/en/area/the-roman-forum/'),('Parco — ingressos e horários','https://colosseo.it/en/opening-times-and-tickets/')])

add('roma-palatino','Monte Palatino',2,'12:40','13:25',None,
 ['O Palatino reúne o imaginário das origens de Roma e a materialidade das residências imperiais. Sua posição elevada, próxima ao Fórum e ao Circo Máximo, ajudou a fazer da colina um lugar privilegiado para a representação do governo. Ao longo do período imperial, palácios, jardins e áreas de cerimônia mudaram profundamente sua paisagem.',
  'Mais que uma coleção de ruínas isoladas, a colina permite perceber a relação entre residência, administração e vista sobre a cidade. O passeio deve selecionar um setor e um ponto de observação viáveis, sem exigir a subida a todo mirante. Após a visita, a pausa de almoço deve respeitar a janela do Coliseu e as regras de saída do complexo.'],
 [('Percurso escolhido','Seguir apenas a rota acessível indicada no dia.'),('Arquitetura imperial','Relacionar pátios e estruturas aos usos residenciais e cerimoniais.'),('Saída e almoço','Prever 13h30–14h30 para refeição e descanso, com deslocamento e segurança para o Coliseu.')],
 'Integra modalidades de ingresso do parque, mas salas e áreas especiais podem exigir bilhete específico. Confirmar o produto adquirido e os acessos; não presumir que todos os interiores estejam incluídos.',
 'É a etapa de maior ganho de altura da manhã. Verificar rampas/elevadores e autonomia da cadeira. Alternativa: abreviar a colina ou observar o Fórum por pontos viáveis, preservando o horário do Coliseu.',
 'intitle:"Palatine Hill"', [('Parco — Palatino','https://colosseo.it/en/area/the-palatine/'),('Parco — regras de visita','https://colosseo.it/en/opening-times-and-tickets/')])

add('roma-coliseu','Coliseu',2,'15:00','16:00','Coliseu, Fórum Romano e Palatino',
 ['Construído no século I pela dinastia Flávia, o Coliseu foi projetado para receber espetáculos públicos e grandes multidões. Sua organização de entradas, corredores e arquibancadas revela soluções de engenharia e uma estrutura social inscrita no próprio espaço. A imagem dos arcos externos é apenas a primeira camada da visita.',
  'No interior, a arena e as estruturas inferiores ajudam a compreender a preparação dos espetáculos e a relação entre público e poder imperial. Observe o edifício a partir das áreas autorizadas pelo ingresso, sem presumir que subsolo, arena ou níveis especiais façam parte de qualquer bilhete. Neste novo roteiro, o Coliseu encerra a Roma Antiga: seu horário confirmado determina o ritmo de toda a manhã.'],
 [('Chegada antecipada','Reserva proposta às 15h; chegar com margem para documento e segurança.'),('Percurso interno','Reconhecer arena, galerias e arquibancadas pelo trajeto permitido.'),('Encerramento','Retornar ou jantar cedo; Monti pode ser opção de refeição, não nova visita obrigatória.')],
 '15h é proposta, não ingresso comprado. Confirmar operação de outono e última entrada; se não houver sessão adequada, reajustar as etapas anteriores. Conferir bilhete combinado, identificação, gratuidade e áreas especiais. Não contar com o primeiro domingo em 29/10.',
 'Confirmar entrada acessível e elevadores operacionais para a modalidade escolhida. O percurso tem controle de segurança e desníveis; subsolo e áreas especiais não têm acesso automaticamente equivalente ao circuito básico.',
 'intitle:"Colosseum"', [('Parco — Coliseu','https://colosseo.it/en/area/the-colosseum/'),('Parco — regras e ingressos','https://colosseo.it/en/tickets/regulation-for-visitors-and-terms-and-conditions-for-the-purchase-of-admission-tickets-to-the-archaeological-park-of-the-colosseum/')])

add('vaticano-saopedro','Basílica e Praça de São Pedro',3,'08:00','09:30','Basílica e Praça de São Pedro',
 ['A Basílica de São Pedro reúne arquitetura, arte e a memória religiosa ligada ao apóstolo. O edifício renascentista e barroco sucedeu a antiga basílica e recebeu contribuições de grandes artistas. A cúpula, a escala da nave e o baldaquino ajudam a compreender a intenção de criar um espaço de grande força simbólica.',
  'Na praça, a colunata de Bernini organiza a chegada dos visitantes e a relação com a fachada. A visita básica à basílica deve ser distinguida de cúpula, necrópole, visitas guiadas e outros serviços. A audiência papal citada na imagem não é parte automática deste passeio: depende do calendário pontifício, de procedimento próprio e de condições de acesso. Não há audiência confirmada para sexta-feira, 30/10.'],
 [('Praça','Observar a colunata e combinar entrada e ponto de encontro.'),('Basílica','Selecionar obras e setores conforme abertura e fluxo do dia.'),('Saída para os Museus','Usar rota externa confirmada; não presumir passagem direta pela Sistina.')],
 'Entrada básica gratuita, sujeita à segurança e à liturgia. Serviços e áreas especiais podem ter cobrança/reserva. Audiência papal exige consulta ao calendário oficial e bilhete/procedimento próprios; não é garantida por visitar a basílica.',
 'Confirmar o ponto de acolhimento para cadeira motorizada e o caminho sem escadas. Vestimenta compatível com templo religioso. A cúpula não deve ser considerada acessível como a nave.',
 'intitle:"Saint Peter" basilica', [('Basílica — site oficial','https://www.basilicasanpietro.va/en'),('Casa Pontifícia — audiências','https://www.vatican.va/content/vatican/en/prenotazione-celebrazioni-udienze.html')])

add('vaticano-museus','Museus Vaticanos e Capela Sistina',3,'10:30','14:00','Museus Vaticanos e Capela Sistina',
 ['Os Museus Vaticanos reúnem coleções formadas ao longo de séculos de patronato papal, combinando antiguidades, galerias e espaços decorados. A visita não deve ser pensada apenas como um corredor até a Capela Sistina: os ambientes revelam relações entre poder, conhecimento e arte. Selecionar destaques evita esgotar o grupo antes do final do percurso.',
  'Na Capela Sistina, o teto e o Juízo Final de Michelangelo convivem com ciclos pictóricos de outros artistas. Escala, narrativa e uso religioso se encontram no mesmo espaço, cuja observação pede tempo e silêncio. As regras locais de fotografia devem ser respeitadas. O percurso acessível pode diferir do fluxo turístico padrão e precisa ser organizado previamente para a cadeira motorizada.'],
 [('Entrada e percurso adaptado','Reserva sugerida às 10h30, após trajeto externo desde São Pedro.'),('Galerias prioritárias','Escolher poucas coleções e pausas conforme orientação da equipe.'),('Capela Sistina e saída','Seguir regras de silêncio/foto e prever almoço antes do castelo.')],
 'CORREÇÃO DA IMAGEM: a regra habitual de domingo gratuito é o último domingo do mês, com exceções do calendário, e não o primeiro. Em 30/10, sexta, usar ingresso/reserva ou gratuidade individual elegível. Confirmar documentos de deficiência e acompanhante e matrícula de Arthur. Não confundir prioridade com visita sem procedimento.',
 'Consultar previamente a admissibilidade da cadeira motorizada, medidas/peso e necessidade de transferência para cadeira convencional em algum trecho. Informar limitações de transferência antes da reserva. O percurso até a Sistina e a saída devem ser confirmados integralmente.',
 'intitle:"Vatican Museums"', [('Museus — abertura e fechamento','https://www.museivaticani.va/content/museivaticani/en/info/orari-musei-vaticani.html'),('Museus — acessibilidade','https://www.museivaticani.va/content/museivaticani/en/organizza-visita/servizi-per-i-visitatori/accessibilita/agevolazioni-e-servizi-per-visitatori-con-disabilita-.html')])

add('roma-castel','Castel Sant’Angelo',3,'16:00','17:30','Via della Conciliazione e Castel Sant’Angelo',
 ['Castel Sant’Angelo nasceu como mausoléu de Adriano no século II e foi transformado sucessivamente em fortaleza, residência papal e prisão. Sua posição junto ao Tibre e perto de São Pedro ajuda a explicar a importância estratégica adquirida pelo monumento. A leitura do exterior já permite observar a massa circular antiga e as transformações defensivas.',
  'Os espaços internos mostram usos muito diferentes daqueles de um túmulo imperial. O castelo se liga à história do poder pontifício e hoje funciona como museu nacional. A visita após os Museus Vaticanos deve permanecer flexível: se houver cansaço ou incompatibilidade da rota interna com a cadeira, o entorno e a ponte oferecem uma experiência válida sem prometer acesso a todos os níveis.'],
 [('Chegada pelo entorno de São Pedro','Almoço e descanso entre 14h e 15h; deslocamento com margem até o castelo.'),('Mausoléu e fortaleza','Observe o núcleo circular e as adaptações defensivas.'),('Interior ou exterior','Escolha a modalidade compatível com o grupo; não obrigar subida aos terraços.')],
 'Ingresso integral anunciado a €18 desde julho/2026; verificar isenções, documentação e eventual exposição. Em 30/10 não se aplica o primeiro domingo. A visita exterior não equivale ao ingresso no museu.',
 'Confirmar quais pavimentos são alcançáveis, funcionamento dos equipamentos e compatibilidade da cadeira motorizada. Não anunciar o monumento inteiro como acessível; manter exterior e ponte como alternativa.',
 'intitle:"Castel Sant" Angelo', [('Museu — informação oficial','https://direzionemuseiroma.cultura.gov.it/museo-nazionale-di-castel-santangelo/'),('Ingressos oficiais','https://portale.museiitaliani.it/')])

add('roma-spagna','Piazza di Spagna',4,'09:00','09:45',None,
 ['Piazza di Spagna é um encontro entre comércio, sociabilidade e paisagem monumental. A Barcaccia, de Pietro e Gian Lorenzo Bernini, ocupa o plano mais baixo, enquanto a escadaria conduz visualmente à igreja de Trinità dei Monti. O efeito depende do desnível: a praça pode ser plenamente compreendida sem subir seus degraus.',
  'A escadaria do século XVIII consolidou uma ligação entre a cidade e a colina, tornando-se uma imagem recorrente de Roma. Para o grupo, a sequência segue depois pela região norte, em direção à Piazza del Popolo, em vez de retornar ao centro do primeiro dia. Observe a fonte e as perspectivas a partir de locais que não interrompam a circulação.'],
 [('Barcaccia','Observe a forma de embarcação e a água junto ao plano da praça.'),('Perspectiva da escadaria','Apreciar a vista de baixo; não usar degraus como percurso.'),('Ligação ao Popolo','Seguir pela região da Via del Babuino, confirmando calçadas e travessias.')],
 'Praça pública gratuita. Respeitar regras de uso da escadaria, sem sentar, comer ou bloquear passagens conforme sinalização. Não há necessidade de comprar ingresso para ver a praça.',
 'Visita proposta no nível inferior, sem subida pela escadaria. Para alcançar mirantes altos, usar rota/veículo acessível independente; não presumir acesso pelos mesmos caminhos de pedestres.',
 'intitle:"Piazza di Spagna"', [('Turismo Roma — Piazza di Spagna','https://www.turismoroma.it/it/luoghi/piazza-di-spagna'),('Turismo Roma — acessibilidade','https://www.turismoroma.it/')])

add('roma-popolo','Piazza del Popolo e Santa Maria del Popolo',4,'10:15','11:30',None,
 ['Piazza del Popolo organiza uma das grandes entradas históricas de Roma. O obelisco e a composição urbana ajudam a compreender a chegada de vias e perspectivas, enquanto a porta marca a relação com o antigo limite da cidade. A praça também serve como ligação para a paisagem do Pincio, que deve ser alcançada por uma rota viável para o grupo.',
  'Santa Maria del Popolo guarda um patrimônio artístico importante, incluindo obras de Caravaggio na Capela Cerasi. A igreja deve ser distinguida das chamadas igrejas gêmeas vistas em outra posição da praça. A visita interna depende de horários, culto e acesso às capelas; se não estiver disponível, o passeio externo continua fazendo sentido.'],
 [('Praça e obelisco','Reconheça os eixos e a relação com a porta histórica.'),('Santa Maria del Popolo','Consultar entrada e observar obras sem interromper o culto.'),('Ligação ao parque','Não subir por escadas ao Pincio; confirmar via alternativa ou transporte.')],
 'Praça gratuita. Consultar horários e regras da basílica; não prometer capelas abertas ou serviços gratuitos além da visita ordinária. Não há ingresso combinado com Galleria Borghese.',
 'Confirmar entrada sem degraus na igreja e a passagem para a área alta. O trajeto entre Popolo e Villa Borghese envolve desnível: prever transporte acessível se necessário.',
 'intitle:"Piazza del Popolo"', [('Basílica — site oficial','https://santamariadelpopoloroma.it/'),('Ministério da Cultura — Santa Maria del Popolo','https://cultura.gov.it/luogo/santa-maria-del-popolo')])

add('roma-borghese','Villa Borghese e Pincio',4,'12:00','13:00','Villa Borghese e Pincio',
 ['Villa Borghese reúne jardins e percursos de uma antiga propriedade aristocrática transformada em espaço de uso público. O parque permite uma pausa em relação à densidade do centro e apresenta outra ideia de cidade: paisagem planejada, áreas de passeio e instituições culturais distribuídas em um terreno amplo.',
  'O Pincio oferece uma relação visual com a Piazza del Popolo e com o tecido urbano, mas parque, mirante e museu não são a mesma visita. O roteiro escolhe um trecho curto e confortável, seguido de almoço, antes da Galleria Borghese. Evitar atravessar toda a área verde é essencial para preservar energia e chegar ao museu no horário reservado.'],
 [('Trecho selecionado do parque','Escolher alamedas firmes e adequadas à cadeira, evitando caminhos de terra após chuva.'),('Mirante, se viável','O Pincio é opcional conforme rota e piso; não obrigar desvio longo.'),('Almoço e ida à Galleria','Pausa de 13h–14h; confirmar distância e entrada real do museu.')],
 'Parque e passeios públicos não equivalem ao ingresso da Galleria. A entrada no museu exige reserva independente, inclusive em condições de gratuidade. Não anunciar “Villa Borghese paga” como regra geral.',
 'Terreno amplo, caminhos inclinados e superfícies variadas. Escolher percurso específico, não apenas “parque acessível”. Planejar banheiro, bateria da cadeira e possível transporte entre setores.',
 'intitle:"Villa Borghese" gardens', [('Turismo Roma — Villa Borghese','https://www.turismoroma.it/it/luoghi/villa-borghese'),('Galleria — informação de visita','https://galleriaborghese.cultura.gov.it/en/visita/info-biglietti/')])

add('roma-galleria','Galleria Borghese',4,'14:30','16:30',None,
 ['A Galleria Borghese ocupa a villa ligada à coleção do cardeal Scipione Borghese, reunindo pintura e escultura em um ambiente concebido para exibir arte e prestígio. Obras de Bernini, Caravaggio e outros mestres permitem relacionar o colecionismo à produção artística de Roma. A escala relativamente concentrada favorece uma seleção atenta, em vez de uma maratona de salas.',
  'Nas esculturas, observe movimento, pontos de vista e transformação dos materiais; nas pinturas, compare luz e construção narrativa. Acesso aos pavimentos e condições de elevador precisam ser tratados com antecedência, pois uma cadeira motorizada pode não acompanhar todo o percurso sem adaptações. A visita deve ser planejada em função das necessidades reais de Orlei, inclusive a possibilidade ou não de transferência.'],
 [('Chegada com antecedência','14h30 é proposta: confirmar turno disponível, ingresso e procedimento de acessibilidade.'),('Seleção de obras','Escolher destaques de escultura e pintura conforme salas alcançáveis.'),('Encerramento','Tempo para loja/saída apenas se confortável; retorno ao hotel e descanso.')],
 'Museu com reserva obrigatória conforme disponibilidade. Primeiro domingo pode ter entrada gratuita com reserva, mas 31/10 é sábado. Confirmar tarifa vigente, documentos de deficiência/acompanhante e procedimento para seis; não presumir acesso por estar no parque.',
 'O museu informa equipamentos de acesso e cadeiras menores para uso em elevador. Confirmar dimensões, peso, pavimentos e eventual transferência da cadeira motorizada para a convencional antes de pagar. Se transferência não for possível, solicitar solução compatível ou substituir a visita.',
 'intitle:"Galleria Borghese"', [('Galleria — ingressos oficiais','https://galleriaborghese.cultura.gov.it/en/visita/info-biglietti/'),('Galleria — acessibilidade','https://galleriaborghese.cultura.gov.it/en/visita/accessibilita/')])

# Preservar referências antigas, retirando as alternativas da agenda de quatro dias.
for key,title in [('toscana-rural','Toscana rural — alternativa sem data'),('roma-trastevere','Trastevere — alternativa sem data')]:
    old=guides[key]
    stages.append(dict(key=key,old_title=old['title'],title=title,place=old['city'],start='',end='',description='ALTERNATIVA SEM DATA — fora do roteiro principal dos quatro dias de Roma. Reagendar somente por decisão do administrador, sem somar às visitas já propostas. Guias, fotos e memórias preservados.',day=0,sequence=0))

# Avisos e pausa aparecem nas páginas, fora dos dados de ingresso da atração.
for s in stages:
    if s['day']:
        g=guides[s['key']]
        g['route_summary']=[{'day':d,'date':'2026-10-'+DAYS[d][0],'title':DAYS[d][1],'places':[r['title'] for r in stages if r['day']==d]} for d in DAYS]
        g['tips'] += ['Restaurantes: confirmar entrada sem degraus, espaço à mesa e banheiro. Nenhuma reserva foi feita.','Nos quatro dias, todas as gratuidades dependem de regras vigentes e documentação; não repetir automaticamente os rótulos das imagens.']

(ROOT/'roma_four_days.json').write_text(json.dumps({'common':COMMON,'stages':stages},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path.write_text(json.dumps(guides,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Atrações de Roma:',sum(s['day']>0 for s in stages),'Catálogo total:',len(guides))

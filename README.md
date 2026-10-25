# Plantrip

Aplicação de planejamento e diário coletivo de viagem em português. Python 3.11+ sem dependências externas, SQLite e JavaScript nativo. Suporta várias viagens, cada uma com seu grupo de participantes.

## Executar localmente

```powershell
python app.py
```

Abra http://localhost:8000. No primeiro acesso crie o administrador; não há senha padrão. Em **Usuários**, o administrador cadastra e edita nome/e-mail dos participantes. Compartilhe as credenciais pessoalmente. O cadastro público é fechado após a configuração inicial.

Em **Viagens**, cadastre nome, datas, locais e observações, e marque os usuários que participarão do grupo. Use **Editar / participantes** para alterar o grupo posteriormente. A inclusão autoriza consultar etapas, comentar e publicar fotos/vídeos no diário da viagem. Ao remover um participante, seu conteúdo permanece no grupo, mas ele perde o acesso. Administradores podem gerenciar e consultar todas as viagens. O seletor lateral alterna a viagem ativa. O menu **Companheiros** mostra apenas o grupo selecionado.

A primeira viagem **Europa (27/10/2026 a 12/11/2026)** é criada automaticamente com Roma, Paris, Londres e Madrid, 28 sugestões de passeios e os deslocamentos informados. Saída de Roma em 01/11 às 18h, chegada a Paris às 23h. As chegadas a Londres e Madrid permanecem sem horário até confirmação; os passeios nesses dias são condicionais. Os horários das atrações são propostas, sem garantia de ingressos. Referências dos órgãos de turismo estão nas descrições. As sugestões não se duplicam a cada reinício e podem ser editadas pelo administrador.

Na atualização de um banco antigo, o conteúdo já existente é preservado em **Minha viagem anterior**, com os usuários existentes atribuídos ao grupo. O administrador pode corrigir nome e período. Os participantes da Europa são definidos explicitamente no menu **Viagens**.

## Recursos

### Guias das atrações

Os 28 passeios da Europa possuem páginas próprias em `/attractions/ID`, abertas pelo cartão ou pelo link **Conhecer a atração · Guia completo**. Cada guia reúne história, percurso sugerido, galeria de referência, recomendações, orientação de chegada, acessibilidade e links das instituições responsáveis. Os horários continuam ligados à etapa do roteiro. Há apresentação guiada em slides, ampliação das fotos, leitura da história pelo navegador quando disponível e impressão do guia.

O botão **Fotos e relato** publica no diário do viajante com vínculo à atração. As memórias de todos os participantes vinculadas ao mesmo passeio aparecem juntas na página, além dos comentários da etapa. Esse vínculo continua funcionando se o administrador alterar o título do passeio. O acesso às páginas e aos comentários segue as permissões da viagem.

As 58 fotos de referência ficam em `static/guide-photos`, com autor, fonte e licença apresentados na galeria e nos slides. As fotos mantêm suas licenças originais; não fazem parte das memórias pessoais dos viajantes. As páginas podem representar o lugar em outra época, e não garantem condições atuais de obras ou acesso. O conteúdo editorial está em `guides.json`, com fontes oficiais por passeio e data de revisão; não há busca ou geração automática no acesso. As propostas de percurso e duração são estimativas editoriais, sem reserva ou compra de ingresso.

Para revisar o catálogo, altere `scripts/build_guides.py` e execute `python scripts/build_guides.py`; as fotos já importadas são preservadas. O script opcional `python scripts/fetch_guide_photos.py` baixa novamente apenas imagens ausentes e exige internet. `python scripts/check_guide_links.py` consulta a disponibilidade das referências; alguns sites oficiais bloqueiam verificações automáticas. Os guias são vinculados por chave estável ao inicializar o aplicativo, preservando o conteúdo existente.

### Planejamento e diário

- Ordem das etapas: em **Logística** e **Passeios**, o administrador arrasta a alça **⠿** para mover uma etapa antes ou depois de outra, inclusive entre dias. A nova sequência é salva por viagem e módulo e aparece para todos os participantes, sem alterar datas e horários. Limpe a busca para arrastar. **Restaurar por data** retoma a ordem cronológica; novas etapas entram no final de uma sequência personalizada. No teclado, foque a alça e use **Alt + ↑ / ↓**.
- Logística: voos, hotéis, trens, carros, passeios, atrações, restaurantes e outros. Timeline ordenada por dia e horário, com edição e exclusão pelo administrador.
- Documentos por etapa: cada voo/viagem e hotel da Europa (Fortaleza → Madrid, Madrid → Roma, Hotel Roma, Roma → Paris, Hotel Paris, Paris → Londres, Hotel Londres, Londres → Madrid, Hotel Madrid, Madrid → Fortaleza) é uma etapa de Logística. O administrador abre a etapa e usa **Anexar documentos** (PDF ou fotos) ou **Remover arquivo**; os participantes do grupo consultam os arquivos. Na atualização de um banco existente o app grava antes uma cópia `backup-before-logistica-*.db` em `data/` e converte as etapas antigas sem arquivos/comentários (as chegadas separadas viram parte da etapa de viagem).
- Passeios: roteiro diário, descrição, horários, fotos, vídeos, apresentação manual com setas do teclado e comentários do grupo.
- Diário: cada participante publica e edita suas memórias. Filtro por autor, busca por ponto visitado e apresentação agrupada por local (utilize o mesmo nome do local para reunir as publicações).
- Arquivos privados vinculados às etapas: JPG, PNG, WebP, GIF, MP4, WebM, MOV e PDF, até 100 MB por arquivo. A reprodução de MOV depende do navegador; prefira MP4/WebM.
- Comentários em todas as etapas, perfis consultáveis pelo diário de cada companheiro e armazenamento persistente no servidor.

O diário começa vazio, sem publicações fictícias. Datas e horários das etapas são locais ao destino, informados pelo administrador, sem conversão de fuso. As apresentações usam conteúdo enviado pelo grupo. Não há rastreamento GPS, extração automática de reservas, geração de conteúdo por IA, envio de e-mails nem integração com Polarsteps, Milepost ou PastBook. Esses produtos serviram apenas de inspiração conceitual.

## VPS com Docker

Repositório: `https://github.com/Ozeus1/plantrip.git`. Domínio de produção: `https://plantrip.orleibarbosa.com.br/`.

Siga o [guia de implantação para VPS com outros sites](deploy/README.md). Ele cobre proxy Nginx/Caddy, HTTPS, criação do administrador, importação privada dos dados locais, backups e atualizações. O Compose usa por padrão `127.0.0.1:18080`, ajustável pelo `.env`, e não ocupa diretamente 80/443.

```sh
cp .env.example .env
docker compose up -d --build
docker compose exec plantrip python scripts/create_admin.py
```

Coloque o proxy reverso existente com HTTPS na frente de `127.0.0.1:18080`. O Compose mantém `COOKIE_SECURE=1` e desativa o cadastro público inicial com `ALLOW_SETUP=0`; o script acima cria o primeiro administrador pelo terminal. Preserve o cabeçalho Host original no proxy e ajuste o limite de uploads para pelo menos 100 MB. O servidor HTTP embutido é destinado ao uso local e grupos pequenos; mantenha-o atrás do proxy na VPS.

O volume `plantrip-data` contém o banco e os arquivos. Faça backup de todo o volume com a aplicação parada para garantir consistência. Não envie dados pessoais, banco ou uploads ao Git. Sem Docker, configure `HOST`, `PORT` e `DATA_DIR` e execute `python app.py` com um gerenciador de serviços. A foto de capa e as fontes usam URLs externas; sem internet, a interface mantém fontes alternativas e o fundo verde.

## Verificação

```sh
python -m unittest discover -s tests -v
node --check static/app.js
node --check static/attractions.js
node --check static/reorder.js
node tests/test_reorder.js
```

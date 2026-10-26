# Implantação: plantrip.orleibarbosa.com.br

Este procedimento adiciona um serviço independente à VPS. O contêiner não publica as portas 80 ou 443. O proxy existente continua responsável pelos outros sites e pelo HTTPS.

**Infraestrutura informada: Nginx.** Siga a seção Nginx abaixo. Ela pressupõe o Nginx instalado no host da VPS; se ele estiver em contêiner, o encaminhamento precisa usar a rede compartilhada descrita na seção de proxies em contêiner.

## 1. Código e configuração

Na VPS Linux, com Git e Docker Compose v2 já instalados:

```sh
sudo mkdir -p /opt/plantrip
sudo chown "$USER":"$(id -gn)" /opt/plantrip
git clone https://github.com/Ozeus1/plantrip.git /opt/plantrip
cd /opt/plantrip
cp .env.example .env
```

Antes de subir, confira se a porta escolhida está livre:

```sh
sudo ss -ltnp | grep ':18080 ' || true
```

Se houver serviço nessa porta, altere `PLANTRIP_PORT` no `.env` e o destino no proxy. Mantenha `COOKIE_SECURE=1` para HTTPS e `ALLOW_SETUP=0`. O aplicativo Python executado diretamente continua com configuração local independente, na porta 8000.

```sh
docker compose config --quiet
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:18080/api/state
```

O retorno inicial terá `user: null` e `setup: false`, pois o primeiro administrador será criado pelo terminal:

```sh
docker compose exec plantrip python scripts/create_admin.py
```

O comando solicita nome, e-mail e senha sem exibir a senha e não modifica um administrador existente. Para testar login via HTTP local, use um túnel SSH e `COOKIE_SECURE=0` temporariamente; na publicação HTTPS volte para `1` e recrie o serviço.

## 2. Domínio e proxy existente

O registro DNS A deve apontar para o IPv4 público da VPS. Só configure AAAA se houver IPv6 funcionando no servidor. Use apenas a opção correspondente à infraestrutura atual.

### Nginx instalado no host

Confira antes se já existe um virtual host para este domínio. Se existir, edite apenas seu encaminhamento; não instale outro bloco com o mesmo `server_name`.

Se o domínio **já tem um bloco HTTPS e certificado**, mantenha as diretivas de certificado e o redirecionamento HTTP existentes. Copie o trecho de proxy:

```sh
sudo mkdir -p /etc/nginx/snippets
sudo cp deploy/nginx-plantrip-proxy.conf /etc/nginx/snippets/plantrip-proxy.conf
```

Dentro do `server {}` HTTPS exclusivo do domínio, substitua o `location /` anterior por:

```nginx
include /etc/nginx/snippets/plantrip-proxy.conf;
```

Não mantenha dois blocos `location /` no mesmo servidor. Se houver outras diretivas de tamanho de upload ou timeout no mesmo contexto, ajuste as existentes para evitar duplicação. Valide e só então recarregue:

```sh
sudo nginx -t && sudo systemctl reload nginx
```

Em Debian/Ubuntu, **sem virtual host prévio** para o domínio, use o modelo completo em vez da inclusão acima:

```sh
sudo cp deploy/nginx-plantrip.conf /etc/nginx/sites-available/plantrip.conf
sudo ln -s /etc/nginx/sites-available/plantrip.conf /etc/nginx/sites-enabled/plantrip.conf
sudo nginx -t && sudo systemctl reload nginx
```

Após o DNS propagar, use o mecanismo de certificados já adotado na VPS. Se for Certbot com plugin Nginx já instalado:

```sh
sudo certbot --nginx -d plantrip.orleibarbosa.com.br
sudo nginx -t
sudo systemctl reload nginx
```

O modelo começa com HTTP para permitir a emissão do certificado. Confirme o redirecionamento para HTTPS antes de entrar no aplicativo. Se já houver certificado para o domínio, mantenha o bloco HTTPS e seus caminhos de certificado, aplicando nele as diretivas de proxy do modelo.

### Caddy instalado no host

Adicione o conteúdo de `deploy/Caddyfile.plantrip` ao Caddyfile que já atende os outros domínios, valide e recarregue usando o procedimento atual da VPS. O Caddy gerencia o certificado desse domínio. Não execute um segundo proxy nas mesmas portas.

### Nginx Proxy Manager ou Traefik em contêiner

`127.0.0.1` dentro do contêiner do proxy aponta para o próprio proxy. Conecte o serviço Plantrip à rede Docker externa já usada pelo proxy e encaminhe para `plantrip:8000`. Use um arquivo de override específico dessa VPS com o nome real da rede e, no caso do Traefik, suas labels de roteador/entrypoint/certresolver. Não publique a aplicação em `0.0.0.0` para contornar a rede. Em Nginx Proxy Manager, mantenha o Host original, configure domínio, SSL, limite de 100 MB e timeouts adequados. Essa integração depende da rede e da configuração existentes; os exemplos Nginx/Caddy pressupõem proxy no host.

## 3. Dados locais e uploads

O Git leva código e as fotos públicas dos guias. Usuários, senhas, reservas, documentos privados, fotos pessoais e backups permanecem fora dele.

Uma instalação nova gera o roteiro Europa e começa sem as contas e arquivos privados do computador. Para transferir o que já foi cadastrado localmente, pare o servidor local e copie **toda a pasta `data/`**, com banco e subpasta `uploads/`, por um canal privado (SCP/SFTP), para `/opt/plantrip/import-data/` na VPS. Não envie isso ao GitHub. Depois:

```sh
cd /opt/plantrip
docker compose stop plantrip
docker compose run --rm --user root --entrypoint sh -v /opt/plantrip/import-data:/import:ro plantrip -c 'cp -a /import/. /data/ && chown -R 10001:10001 /data'
docker compose up -d plantrip
```

Esse comando substitui os dados do volume pelos importados: faça backup do volume antes se já houver conteúdo na VPS. A cópia integral mantém os vínculos entre banco e uploads. Se importar um banco com administrador, use a conta existente; não execute cadastro de outra conta inicial. A pasta de importação contém informação privada: restrinja seu acesso e remova a cópia temporária após validar sua cópia de segurança.

## 4. Atualização apenas do Plantrip

Faça um backup antes de atualizar. Dentro de `/opt/plantrip`:

```sh
git pull --ff-only origin main
docker compose up -d --build plantrip
docker compose ps
docker compose logs --tail=100 plantrip
```

Evite comandos globais de limpeza Docker. `docker compose down -v` remove os dados e não deve fazer parte da atualização. O volume persistente é `plantrip_plantrip-data` com o nome de projeto fornecido neste repositório. Não troque o nome de projeto sem também migrar o volume.

## 5. Backup consistente

O exemplo cria um arquivo que contém banco e uploads. Guarde-o fora do repositório e em local privado:

```sh
cd /opt/plantrip
mkdir -p backups
chmod 700 backups
docker compose stop plantrip
(umask 077; docker compose run --rm -T --entrypoint tar plantrip -czf - -C /data . > "backups/plantrip-data-$(date +%Y%m%d-%H%M%S).tar.gz")
docker compose up -d plantrip
```

O arquivo é criado pelo usuário do terminal, com acesso privado e data no nome. Confirme o código de saída e a integridade do arquivo antes de considerá-lo um backup válido. A restauração deve ser feita com o serviço parado e o volume previamente copiado.

## 6. Verificação final

Abra `https://plantrip.orleibarbosa.com.br`, confira o certificado, faça login e teste uma foto/PDF, reprodução de vídeo e salvamento da ordem. Confira também os demais sites da VPS após recarregar o proxy. Nenhuma alteração remota é executada automaticamente por estes arquivos.
# Atualização do roteiro Roma e Toscana — outubro de 2026

Atualização posterior: `europa-london-no-museums-v1` retira Tate e British Museum da agenda, preservando os guias, fotos, comentários e memórias. Sherlock Holmes e Madame Tussauds deixam de aparecer nas sugestões. Após o almoço, segue-se ao Millennium Bridge (14h45) e St Paul’s (15h15), com interior opcional sujeito a reserva e acesso confirmado. Mantém os monumentos e transportes; faz backup antes de aplicar uma única vez. Para instalar: `git pull --ff-only origin main` e `docker compose up -d --build plantrip`.

## Londres em dois dias — 09 e 10/11/2026

A migração `europa-london-two-days-202611-v1` faz backup `backup-before-london-two-days-*.db`, preserva IDs existentes, arquivos, comentários e memórias, e reorganiza 13 paradas:

- 09/11: Buckingham exterior, St James’s Park, Abadia de Westminster, cabines, Big Ben, Parlamento exterior e London Eye/South Bank.
- 10/11: Torre de Londres, Tower Bridge exterior, London Bridge, Tate Modern como visita curta opcional, Millennium Bridge e St Paul’s exterior. Para entrar em St Paul’s, é preciso retirar Tate e antecipar a visita; o circuito completo chega depois da última entrada turística habitual.

British Museum e Covent Garden/Soho ficam como alternativas sem data, deixando 11/11 livre. Chegada a Londres continua a confirmar após saída de Paris em 08/11 às 23h; não comprar ingressos matinais sem resolver essa logística. Transporte de saída para Madrid em 12/11 às 06h permanece intacto. O Fifteen fechado, restrição de cadeira no Sherlock Holmes Museum, fechamento habitual de Windsor às terças, diferença entre Tower/London Bridge e entre King’s Cross/Studio Tour estão documentados nas alternativas. As páginas têm fotos licenciadas, história, fontes, mobilidade e navegação dos dois dias. A lista/timestamps fornecidos pelo grupo servem de referência ao vídeo; informações operacionais foram pesquisadas nas instituições responsáveis.

## Roma reorganizada em quatro dias (atualização posterior)

A migração `europa-roma-four-days-202610-v1` é aplicada uma única vez ao iniciar o aplicativo, depois dos roteiros anteriores. Faz backup `backup-before-roma-four-days-*.db` no diretório de dados e mantém os IDs antigos e seus arquivos, comentários e vínculos de memórias. Cria paradas individuais para completar as atrações das imagens:

- 28/10: Trevi, Adriano, Pantheon, San Luigi, Navona e Campo de’ Fiori; início à tarde após chegada/descanso.
- 29/10: Venezia, Vittoriano, Capitólio, Fórum, Palatino e Coliseu; horário do Coliseu condicionado à reserva e operação de inverno.
- 30/10: São Pedro, Museus Vaticanos/Sistina e Castel Sant’Angelo; audiência papal não confirmada.
- 31/10: Spagna, Popolo/Santa Maria del Popolo, Villa/Pincio e Galleria Borghese.

Toscana e Trastevere permanecem como alternativas **sem data**, fora desses quatro dias. Paris, Londres, Madrid e transportes não são alterados. As 19 paradas têm ao menos duas fotos licenciadas; os guias compostos de Museus/Sistina e Popolo/basílica têm quatro. Incluem história, rotas, alimentação, reservas, fontes oficiais e observações para cadeira motorizada. Os quatro dias podem ser navegados nas páginas dos guias. O histórico do planejamento anterior fica recolhido em seção própria. Após a migração, edições manuais não são sobrescritas a cada reinício.

Atualização na VPS: `git pull --ff-only origin main` e `docker compose up -d --build plantrip`. Não reimportar o banco local sobre o banco da VPS.

O roteiro Paris/Champagne do PDF também é aplicado uma única vez pela migração `europa-paris-champagne-202611-v1`, com backup `backup-before-paris-*.db`. Mantém chegada em Paris em 01/11 às 23h (o PDF pressupunha chegada mais cedo), conserva a logística e os vínculos existentes, muda Louvre para 02/11 e inclui Champagne/Reims com Veuve Clicquot em 05/11. Versailles fica fora do programa principal como alternativa a reagendar, sem reserva. As páginas de Toscana e Champagne comparam produtoras/maisons com fontes oficiais, contatos e pendências de acessibilidade. A migração não realiza reservas nem envia mensagens aos estabelecimentos.

A versão com `roma2026.py` adapta uma única vez os passeios da viagem Europa (27/10/2026): centro histórico em 28/10, Vaticano em 29/10, Toscana em 30/10 e Roma Antiga em 31/10. Ao iniciar o aplicativo, cria `backup-before-roma-*.db` no diretório de dados antes da alteração. IDs existentes, fotos, comentários e vínculos com memórias são preservados; observações anteriores ficam registradas no texto da etapa. Edições posteriores não são sobrescritas a cada reinício. Não reimporte o banco local sobre o banco em uso na VPS.

Depois de `git pull --ff-only origin main` e `docker compose up -d --build plantrip`, confira o menu Passeios. Os horários são propostas; vinícola, veículo acessível e restaurantes continuam pendentes de confirmação. Trastevere foi mantido somente como alternativa opcional em 01/11. Os novos guias de Toscana e Castel Sant’Angelo ainda não possuem fotos editoriais; recebem as memórias publicadas pelo grupo.


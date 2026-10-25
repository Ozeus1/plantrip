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

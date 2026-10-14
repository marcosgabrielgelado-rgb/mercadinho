# Mercado Web

Aplicativo web responsivo para catálogo de supermercado, com painel privado para administrar produtos, preços, imagens e ofertas.

## O que já funciona

- Página pública com produtos, imagens, preços e categorias.
- Busca por nome, marca, categoria e descrição.
- Filtro para ver apenas as ofertas.
- Ofertas calculadas automaticamente quando o preço anterior é maior que o atual.
- Painel administrativo com usuário e senha.
- Criar, editar e remover produtos.
- Enviar imagens do computador (PNG, JPG, JPEG, WEBP ou GIF, até 5 MB) ou usar um link de imagem.
- Marcar produtos como visíveis/ocultos e destacar produtos.
- Personalizar nome e frases do supermercado.
- Dados salvos em SQLite no computador, permanecendo após fechar e abrir o aplicativo.
- Layout adaptável a celulares, tablets e computadores.

O projeto vem com produtos de exemplo para que você veja o catálogo funcionando. Edite ou exclua os exemplos e cadastre os produtos reais da loja.

## Instalar no Windows

1. Instale o Python 3.11 ou superior em https://www.python.org/downloads/windows/ . Durante a instalação, marque **Add Python to PATH**.
2. Extraia o ZIP inteiro para uma pasta, por exemplo `C:\MercadoWeb`.
3. Dê dois cliques em `instalar_windows.bat` e aguarde a instalação das dependências.
4. Depois, dê dois cliques em `iniciar_windows.bat`. O site abre em `http://127.0.0.1:5000`.
5. A janela preta precisa continuar aberta enquanto você usa o site. Feche-a para encerrar o servidor local.

## Entrar na administração

- Endereço: `http://127.0.0.1:5000/admin/login`
- Usuário inicial: `admin`
- Senha inicial: `Mercado@2026!`

No menu do site, clique em **Área do gerente** para entrar. Para adicionar produtos, use **Novo produto**. Para fazer uma oferta, informe um preço anterior maior que o preço atual. O site calcula e mostra o desconto automaticamente.

## Onde os dados ficam

- Banco de dados: `instance/mercado.db`
- Imagens enviadas: `static/uploads/`
- Configurações de ambiente e credenciais: `.env`

Faça cópia de segurança do banco e da pasta `static/uploads` antes de mover ou reinstalar o projeto. Não apague esses arquivos se quiser manter seus dados.

## Segurança e publicação online

Por padrão, o aplicativo escuta apenas `127.0.0.1`, então abre no próprio computador. Isso não publica automaticamente o catálogo na internet nem torna o site acessível aos clientes fora da máquina.

Para publicar online, será necessário contratar/configurar uma hospedagem e definir as variáveis de ambiente nela. **Troque `ADMIN_PASSWORD` e `SECRET_KEY` antes de publicar, mantenha `.env` privado, use HTTPS e configure `COOKIE_SECURE=1`.** Não suba o arquivo `.env` para repositórios públicos. Para uma hospedagem com armazenamento temporário, configure armazenamento persistente para o banco e para as imagens; caso contrário, arquivos enviados podem sumir numa reinicialização.

Há um `Dockerfile` e um `Procfile` como ponto de partida para hospedagem, mas a publicação e a configuração de armazenamento persistente não são feitas pelo instalador local.

## Observações

- Os produtos e preços de demonstração são fictícios. Substitua-os pelos dados reais antes de divulgar o catálogo.
- As fotos de exemplo vêm de URLs externas e precisam de internet para carregar. As imagens enviadas pelo painel ficam guardadas no projeto.
- Este é um catálogo de produtos, não um sistema de caixa, estoque integrado, pagamento ou entrega.

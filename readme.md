# TermWeb — Huawei VRP Web Console

Aplicação web local para abrir sessões SSH interativas com equipamentos Huawei VRP. A interface usa xterm.js no navegador; o backend FastAPI estabelece a conexão SSH por meio do Netmiko e faz a comunicação com o terminal usando WebSocket.

## Funcionalidades

- Conexão SSH interativa com switches e roteadores Huawei VRP.
- Cadastro local de equipamentos (nome, endereço, porta e usuário padrão).
- Cadastro de macros com comandos para execução no terminal.
- Persistência local de equipamentos e macros em SQLite.
- Criação automática do banco e das macros iniciais na primeira execução.

## Quickstart — Windows

### Pré-requisitos

- Python instalado e disponível no terminal.
- A pasta do projeto aberta no PowerShell ou no Prompt de Comando.

### 1. Criar e ativar o ambiente virtual

No PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

No Prompt de Comando (CMD):

```bat
py -m venv venv
venv\Scripts\activate.bat
```

Se o ambiente virtual já existir, basta ativá-lo.

### 2. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 3. Iniciar para uso somente neste computador

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Abra [http://localhost:8000](http://localhost:8000) no navegador. Para encerrar o servidor, volte ao terminal e pressione `Ctrl+C`.

Também é possível iniciar com `iniciar_terminal.bat`. Esse script abre o navegador e inicia o servidor em `0.0.0.0`, tornando-o acessível a outros dispositivos da rede; leia a seção de segurança antes de usá-lo.

## Uso pela rede local

Para permitir conexões de outros dispositivos na rede, inicie o servidor com:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Depois, acesse `http://<IP_DO_COMPUTADOR>:8000` a partir do outro dispositivo, substituindo o marcador pelo endereço local do computador que executa o servidor. A rede e o firewall também precisam permitir essa conexão.

## Estrutura do projeto

```text
.
├── main.py                 # Backend FastAPI, API REST e WebSocket SSH
├── index.html              # Interface web e terminal xterm.js
├── database.py             # Configuração do SQLAlchemy e do SQLite
├── models.py               # Modelos e schemas de switches e macros
├── requirements.txt        # Dependências Python
├── app.ico                 # Ícone usado pelo backend
├── gerar_icone.py          # Script para gerar o ícone
├── iniciar_terminal.bat    # Inicialização do servidor no Windows
├── parar_terminal.bat      # Script local para encerrar processos Python
└── .gitignore              # Arquivos locais ignorados pelo Git
```

## Dados locais

O backend cria `terminal_data.db` na pasta do projeto quando inicia. O banco armazena os equipamentos cadastrados (incluindo endereços e usuários padrão) e as macros. O `.gitignore` ignora arquivos `*.db` para evitar que esses dados sejam enviados ao GitHub.

As macros iniciais são inseridas automaticamente quando a lista de macros é consultada pela primeira vez e ainda está vazia.

## Segurança e limitações

- O backend não implementa autenticação de usuários. Qualquer pessoa que consiga acessar a aplicação pode consultar ou alterar os equipamentos e macros cadastrados.
- A comunicação atual usa HTTP e WebSocket sem criptografia. A senha SSH é enviada como parâmetro da URL do WebSocket; não use a aplicação em redes não confiáveis nem a exponha diretamente à internet.
- Para uso seguro por mais de um computador, coloque a aplicação atrás de um proxy com HTTPS/WSS, controle de acesso e configuração adequada de rede antes de disponibilizá-la.
- As senhas dos equipamentos são fornecidas ao conectar e não são armazenadas no banco SQLite pela aplicação.
- `parar_terminal.bat` encerra todos os processos `python.exe` e `pythonw.exe` do Windows, não somente o servidor deste projeto. Prefira `Ctrl+C` no terminal que iniciou o servidor.


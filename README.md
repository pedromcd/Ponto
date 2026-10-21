# Ponto Facial | Demonstração pública

Aplicação de demonstração para gestão de presença, correção auditável de marcações e fechamento mensal, construída com **Python, FastAPI, SQLite, Jinja2 e OpenPyXL**.

> **Escopo desta versão:** o sistema original foi concebido para reconhecimento facial, mas o código biométrico e os dados de colaboradores não fazem parte desta publicação. Esta versão demonstra os fluxos administrativos com dados totalmente fictícios. **Não é um REP-P homologado e não serve como registro oficial de jornada.** Não está pronta para implantação empresarial sem autenticação apropriada, avaliação de segurança, privacidade e requisitos trabalhistas.

## Funcionalidades

- Cadastro e desativação de funcionários fictícios.
- Visualização diária de marcações e horas computadas.
- Visão de fechamento por mês e funcionário.
- Correção manual com motivo e responsável registrados.
- Desconsideração auditável, sem apagar a marcação original.
- Exportações CSV e Excel.
- Dados de teste sem câmera e sem cadastro biométrico.
- Proteção por token nas operações administrativas fora do modo demonstração (mínimo de demonstração; não substitui autenticação com usuários).

## Como executar

Python 3.10+:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Defina ambiente de demonstração:

```powershell
$env:PONTO_DEMO="1"
$env:PONTO_DB="data/demo.db"
python semear.py
uvicorn app.main:app --reload
```

Em Linux/macOS use `export PONTO_DEMO=1` e `export PONTO_DB=data/demo.db`.

Abra http://127.0.0.1:8000/fechamento. Acesse também `/funcionarios`, `/diario` e `/health`.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Segurança e privacidade

Não publique `data/*.db`, modelos faciais, imagens de funcionários, credenciais, exportações e backups. Em `PONTO_DEMO=1`, todas as operações administrativas estão abertas propositalmente para teste local. **Não exponha este modo à internet.** Fora do modo demo, escritas e exportações exigem o cabeçalho `X-Admin-Token` configurado por `PONTO_ADMIN_TOKEN`. As páginas de consulta continuam acessíveis; portanto, o projeto não deve ser hospedado com dados pessoais reais.

## Limitações conhecidas

- Nenhuma câmera ou reconhecimento facial nesta versão pública.
- O cálculo das horas usa pares de entrada e saída; não interpreta jornada contratual, feriados, adicionais ou regras legais.
- Dias sem marcações não são classificados automaticamente como faltas.
- Sem gestão de usuários ou perfis, proteção CSRF, controle de acesso completo ou trilha imutável.
- Destinado a demonstração e estudo, não a uso oficial.

Autor: [Pedro Marques Correa Domingues](https://github.com/pedromcd).

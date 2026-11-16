[English](README.en.md) | **Português**

# ⏱️ Ponto Facial — Demonstração pública

**Sistema web de controle de ponto com cálculo de horas, correções auditáveis e fechamento mensal, feito com Python, FastAPI, SQLite, Jinja2 e OpenPyXL.**

> **Escopo desta versão:** o sistema original foi concebido com registro por **reconhecimento facial**. O código biométrico e os dados de colaboradores **não fazem parte** desta publicação. Esta versão demonstra os fluxos administrativos com dados totalmente fictícios. **Não é um REP-P homologado e não serve como registro oficial de jornada.**

---

## 🎯 Objetivo

Em empresas pequenas, o controle de ponto costuma ser feito em papel ou planilha, e o fechamento do mês vira um trabalho manual: somar horas, encontrar marcações faltando e corrigir erros sem perder o histórico.

Este projeto automatiza essa rotina:

- registra entradas e saídas;
- calcula as horas trabalhadas por dia e **sinaliza inconsistências** (por exemplo, uma entrada sem saída);
- permite **corrigir** marcações sem apagar nada, mantendo motivo e responsável;
- gera o **fechamento mensal** por funcionário e o exporta para **Excel e CSV**.

---

## ✨ Funcionalidades

- **Funcionários:** cadastro com nome e departamento e desativação, sem apagar o histórico.
- **Visão diária:** marcações do dia e horas computadas para cada funcionário.
- **Fechamento mensal:** resumo do mês por funcionário, com detalhamento dia a dia.
- **Marcação manual:** registra uma entrada ou saída esquecida, sempre com **motivo** e **responsável**.
- **Desconsiderar marcação:** uma marcação errada é marcada como ignorada, com motivo e responsável. **O registro original nunca é apagado**, o que preserva a trilha de auditoria.
- **Pendências:** dias com entrada sem saída (ou saída sem entrada) são sinalizados no fechamento.
- **Exportação** do mês em **CSV** e **Excel (.xlsx)**.
- **Dados de demonstração** gerados por script, sem câmera e sem biometria.
- **Proteção das operações de escrita** por token fora do modo de demonstração.

---

## ⚙️ Como funciona

### Cálculo das horas

As marcações válidas do dia (as não desconsideradas) são percorridas em ordem cronológica e pareadas como **entrada → saída**:

```text
08:00 entrada ─┐
12:00 saída  ──┘  4h00
13:00 entrada ─┐
17:30 saída  ──┘  4h30
                  ─────
                  8h30  (sem pendência)
```

Se aparecem duas entradas seguidas, uma saída sem entrada ou uma entrada sem saída no fim do dia, o dia é marcado como **pendente** para revisão, em vez de gerar um número de horas silenciosamente errado.

### Modelo de dados

```text
employees(id, name, department, active)

punches(id, employee_id, occurred_at, kind ∈ {entrada, saida},
        source ∈ {demo, manual}, reason, actor,
        ignored, ignored_reason, ignored_by)
```

- `source` diferencia marcações automáticas de marcações manuais.
- `reason`/`actor` registram quem fez uma correção manual e por quê.
- `ignored`/`ignored_reason`/`ignored_by` implementam a desconsideração auditável.
- Um índice em `(employee_id, occurred_at)` acelera as consultas de dia e de mês.

### Rotas

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Página inicial |
| `GET` | `/health` | Health check |
| `GET` / `POST` | `/funcionarios` | Lista e cadastra funcionários |
| `POST` | `/funcionarios/{id}/desativar` | Desativa um funcionário |
| `GET` | `/diario?day=AAAA-MM-DD` | Visão diária |
| `GET` | `/fechamento?month=AAAA-MM` | Fechamento do mês |
| `GET` | `/fechamento/{id}?month=AAAA-MM` | Fechamento detalhado de um funcionário |
| `POST` | `/marcacoes` | Marcação manual (motivo e responsável obrigatórios) |
| `POST` | `/marcacoes/{id}/desconsiderar` | Desconsidera uma marcação de forma auditável |
| `GET` | `/exportar.csv?month=AAAA-MM` | Exporta o mês em CSV |
| `GET` | `/exportar.xlsx?month=AAAA-MM` | Exporta o mês em Excel |

---

## 🛠️ Tecnologias

- **Python 3.10+**, **FastAPI**: rotas, validação e formulários
- **Jinja2**: páginas renderizadas no servidor
- **SQLite**: banco de dados, com restrições `CHECK` e chaves estrangeiras
- **OpenPyXL**: geração do Excel
- **pytest**: testes automatizados
- **GitHub Actions**: os testes rodam a cada push e pull request

---

## ▶️ Como executar

Python 3.10+:

```bash
git clone https://github.com/pedromcd/Ponto.git
cd Ponto
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure o modo de demonstração, gere os dados fictícios e suba o servidor:

```powershell
# Windows PowerShell
$env:PONTO_DEMO="1"
$env:PONTO_DB="data/demo.db"
python semear.py
uvicorn app.main:app --reload
```

```bash
# Linux/macOS
export PONTO_DEMO=1
export PONTO_DB=data/demo.db
python semear.py
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000/fechamento`. Também estão disponíveis `/funcionarios`, `/diario` e `/health`.

## ✅ Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

Os testes cobrem o health check, cadastro e desativação de funcionários, marcação manual com exportação, rejeição de correções inválidas e a exigência do token de administrador fora do modo de demonstração. Eles rodam automaticamente no GitHub Actions.

---

## 🧩 Estrutura

```text
Ponto/
├── app/
│   ├── main.py          # Rotas, banco, cálculo de horas e exportações
│   └── templates/       # Páginas Jinja2: início, funcionários, diário, fechamento, detalhe
├── semear.py            # Gera dados fictícios de demonstração
├── tests/test_app.py    # Testes com pytest
├── .github/workflows/   # CI: testes no GitHub Actions
├── requirements.txt / requirements-dev.txt
└── .env.example
```

---

## 🔒 Segurança e privacidade

- Não publique `data/*.db`, modelos faciais, imagens de funcionários, credenciais, exportações ou backups.
- Com `PONTO_DEMO=1`, todas as operações administrativas ficam abertas de propósito para teste local. **Não exponha esse modo na internet.**
- Fora do modo demo, escritas e exportações exigem o cabeçalho `X-Admin-Token`, configurado por `PONTO_ADMIN_TOKEN`. As páginas de consulta continuam acessíveis, então o projeto não deve ser hospedado com dados pessoais reais.

## ⚠️ Limitações conhecidas

- Sem câmera nem reconhecimento facial nesta versão pública.
- O cálculo usa pares de entrada e saída; não interpreta jornada contratual, feriados, adicionais nem regras trabalhistas.
- Dias sem marcação não são classificados automaticamente como falta.
- Sem gestão de usuários e perfis, proteção CSRF, controle de acesso completo ou trilha imutável.

## 🚧 Próximos passos

- Reintegrar o registro por reconhecimento facial como um serviço separado (veja o projeto [Controle de Acesso por Reconhecimento Facial](https://github.com/pedromcd/Controle-de-acesso-por-reconhecimento-facial)).
- Adicionar login com perfis (administrador, gestor, funcionário).
- Configurar jornadas contratuais para calcular horas extras e faltas.

---

## 👨‍💻 Autor

**Pedro Marques Correa Domingues** · [GitHub](https://github.com/pedromcd) · [Portfólio](https://pedromcd.github.io)

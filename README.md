# Ponto Facial

Sistema web de registro de ponto com reconhecimento facial, desenvolvido em Python com FastAPI, SQLite e InsightFace.

O projeto foi pensado para uso em uma máquina dedicada, como um totem de ponto, permitindo registrar entradas e saídas por reconhecimento facial e acompanhar as marcações ao longo do dia e do período.

## Funcionalidades

- cadastro de funcionários com captura facial;
- registro de entrada e saída por reconhecimento facial;
- quadro diário com as marcações de cada funcionário;
- fechamento por período;
- identificação de dias sem registro e sequências incompletas;
- inclusão manual de marcações com motivo e autor;
- desconsideração de marcações sem apagar o registro original;
- exportação do fechamento em Excel;
- exportação da relação completa de registros em CSV;
- suporte a banco SQLite;
- configuração por variáveis de ambiente.

## Tecnologias

- Python
- FastAPI
- Jinja2
- SQLite
- InsightFace / ONNX Runtime
- OpenPyXL
- HTML, CSS e JavaScript

## Telas principais

| Rota | Função |
| --- | --- |
| `/` | Totem para registrar entrada e saída |
| `/diario` | Visão das marcações do dia |
| `/funcionarios` | Cadastro e gerenciamento de funcionários |
| `/fechamento` | Fechamento e pendências do período |
| `/fechamento/{id}` | Espelho individual de um funcionário |

## Executar em modo de demonstração

Requer Python 3.10 ou superior.

No Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-teste.txt

python semear.py
$env:PONTO_BANCO="dados/demo.db"

uvicorn app.main:app --port 8000
```

Depois abra:

```text
http://localhost:8000/fechamento
```

O script `semear.py` gera dados fictícios para demonstrar as telas e o fluxo de fechamento sem depender de câmera.

## Executar com reconhecimento facial

Instale todas as dependências:

```powershell
pip install -r requirements.txt
```

Inicie a aplicação:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra:

```text
http://localhost:8000
```

Na primeira utilização do reconhecimento facial, o InsightFace pode baixar os modelos necessários para `dados/modelos/`.

## Configuração

As principais opções são definidas por variáveis de ambiente:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `PONTO_LIMIAR` | `0.45` | Similaridade mínima para reconhecimento |
| `PONTO_MARGEM` | `0.06` | Diferença mínima entre os dois melhores resultados |
| `PONTO_CARENCIA` | `60` | Intervalo, em segundos, para repetir o mesmo tipo de marcação |
| `PONTO_CAPTURAS` | `5` | Quantidade de capturas usadas no cadastro facial |
| `PONTO_MODELO` | `buffalo_l` | Modelo utilizado pelo InsightFace |
| `PONTO_DET_SIZE` | `640` | Resolução usada na detecção |
| `PONTO_AREA_MIN` | `0.020` | Área mínima do rosto no quadro |
| `PONTO_BANCO` | `dados/ponto.db` | Caminho do banco SQLite |

## Testes

```bash
pip install pytest httpx
python -m pytest tests/ -v
```

Os testes do projeto não dependem da câmera.

## Observações

O sistema foi projetado originalmente para execução local em uma máquina dedicada.

A aplicação não deve ser exposta diretamente à internet sem uma camada adequada de autenticação, autorização e HTTPS.

O reconhecimento facial também não implementa liveness detection, portanto uma imagem apresentada à câmera pode ser aceita como rosto válido.

Arquivos de banco, modelos, backups, exportações e outros dados locais não devem ser versionados no repositório.

## Estrutura

```text
app/
├── main.py
├── db.py
├── faces.py
├── fechamento.py
├── planilha.py
├── settings.py
└── templates/

tests/
dados/
instalacao/
```

## Autor

Pedro Marques Correa Domingues

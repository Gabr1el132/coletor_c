# Coletor de Submissões em C

Script Python para coletar submissões de exercícios em C de plataformas de juízes online,
com foco na geração de datasets para análise de erros comuns de iniciantes.

**Plataformas suportadas:** CodeBench · BOCA · VPL (Moodle)

---

## Instalação

```bash
pip install -r requirements.txt
```

> Python 3.10+ recomendado.

---

## Uso

### CodeBench

```bash
python collect.py codebench \
  --url https://codebench.ufam.edu.br \
  --user professor@email.com \
  --password SENHA

# Apenas um curso específico
python collect.py codebench \
  --url https://codebench.ufam.edu.br \
  --user professor@email.com \
  --password SENHA \
  --course-id 42

# Apenas submissões erradas, máximo 200 por exercício
python collect.py codebench \
  --user professor@email.com --password SENHA \
  --only-wrong --max-per-exercise 200
```

### BOCA (instância local)

```bash
python collect.py boca \
  --url http://localhost/boca \
  --user admin \
  --password SENHA \
  --contest-id 1
```

> O usuário precisa ser **admin** ou **staff** para acessar o painel de runs.
> Se o BOCA estiver em subpath diferente (ex: `/sistema/boca`), ajuste `--url`.

### VPL via Moodle

```bash
# Com token (recomendado — gerar em Moodle > Preferências > Tokens de segurança)
python collect.py vpl \
  --url https://moodle.minhainstituicao.edu.br \
  --token SEU_TOKEN_AQUI

# Com usuário e senha (gera token automaticamente)
python collect.py vpl \
  --url https://moodle.minhainstituicao.edu.br \
  --user professor \
  --password SENHA \
  --course-id 101
```

> O admin do Moodle precisa habilitar as funções:
> `mod_vpl_get_vpl_instances`, `mod_vpl_get_all_submissions`, `mod_vpl_get_submission_files`
> em **Administração > Plugins > Serviços Web > Funções externas**.

---

## Opções globais

| Flag | Descrição | Padrão |
|---|---|---|
| `--output DIR` | Diretório raiz de saída | `./output` |
| `--only-wrong` | Coleta apenas WA/CE/TLE/RE | desativado |
| `--max-per-exercise N` | Limite de submissões por exercício | sem limite |

---

## Estrutura de saída

```
output/
├── codebench/
│   ├── metadata.json          ← índice de todas as submissões
│   ├── 101_soma_de_dois/
│   │   ├── 48321.c
│   │   └── 48399.c
│   └── 102_fatorial/
│       └── 48501.c
├── boca/
│   ├── metadata.json
│   └── A/
│       ├── 1.c
│       └── 2.c
└── vpl/
    ├── metadata.json
    └── 55_hello_world/
        └── 9901.c
```

### metadata.json (exemplo de entrada)

```json
{
  "platform": "codebench",
  "exercise_id": "101",
  "exercise_name": "Soma de dois inteiros",
  "submission_id": "48321",
  "verdict": "CE",
  "language": "C",
  "student_id": "usr_7f3a",
  "timestamp": "2024-03-15T14:22:01",
  "extra": { "course_id": "12", "course_name": "Programação I" },
  "file": "output/codebench/101_soma_de_dois/48321.c"
}
```

---

## Habilitando serviços VPL no Moodle (passo a passo)

1. Entre como administrador do Moodle
2. Acesse **Administração do site > Plugins > Serviços web > Gerenciar serviços**
3. Habilite o serviço **VPL** (ou crie um serviço personalizado)
4. Em **Funções externas**, adicione:
   - `mod_vpl_get_vpl_instances`
   - `mod_vpl_get_all_submissions`
   - `mod_vpl_get_submission_files`
5. Gere um token em **Preferências do usuário > Tokens de segurança**

---

## Dicas para o BOCA

- Se você tiver acesso direto ao banco PostgreSQL, descomente a classe
  `BocaDBCollector` em `collectors/boca.py` — é muito mais rápido.
- O usuário precisa ter perfil **admin** ou **staff** para ver o fonte das runs.
- Para múltiplos contests, rode o script várias vezes com `--contest-id` diferente.

---

## Próximos passos (análise de erros)

Com o dataset coletado, você pode:

```python
import json, pathlib

meta = json.loads(pathlib.Path("output/codebench/metadata.json").read_text())

# Distribuição de erros
from collections import Counter
verdicts = Counter(s["verdict"] for s in meta)
print(verdicts)
# Counter({'WA': 412, 'CE': 198, 'AC': 130, 'TLE': 44, 'RE': 21})

# Filtrar só erros de compilação
ce_files = [s["file"] for s in meta if s["verdict"] == "CE"]
```

Para análise mais profunda, ferramentas como `clang-tidy`, `cppcheck` ou
análise AST com `pycparser` podem ser integradas ao pipeline.

---

## Licença

MIT — use livremente para pesquisa acadêmica.

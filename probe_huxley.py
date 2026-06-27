#!/usr/bin/env python3
"""
Diagnóstico da API do TheHuxley
================================
Útil para confirmar endpoints e ver a estrutura real dos JSONs
antes de rodar a coleta completa.

Uso:
    python probe_huxley.py --user email@prof.com --password SENHA

O script vai:
  1. Fazer login e mostrar o token + dados do usuário
  2. Listar suas turmas
  3. Listar os questionários da primeira turma
  4. Listar submissões do primeiro problema do primeiro questionário
  5. Buscar o detalhe da primeira submissão em C (com o código)
  6. Salvar tudo em huxley_probe.json para inspeção

Se algum endpoint falhar, o script mostra a resposta crua para
você inspecionar e ajustar collectors/thehuxley.py.
"""

import argparse
import json
import sys
import time
import requests

BASE = "https://www.thehuxley.com"
API  = f"{BASE}/api/v1"


def jprint(data, label=""):
    if label:
        print(f"\n{'='*60}\n{label}\n{'='*60}")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])


def main():
    p = argparse.ArgumentParser(description="Sonda endpoints da API do TheHuxley")
    p.add_argument("--user",     required=True, help="Login/e-mail do professor")
    p.add_argument("--password", required=True)
    p.add_argument("--group-id", help="Força uma turma específica")
    p.add_argument("--out", default="huxley_probe.json", help="Arquivo de saída")
    args = p.parse_args()

    session = requests.Session()
    session.headers.update({
        "User-Agent":   "SubmissionCollector/1.0 (probe)",
        "Content-Type": "application/json",
        "Accept":       "application/json",
    })

    probe = {}

    # ── 1. Login ──────────────────────────────────────────────────────────────
    print("\n[1/5] Fazendo login…")
    resp = session.post(f"{API}/user/login",
                        json={"login": args.user, "password": args.password})
    print(f"  Status: {resp.status_code}")
    if resp.status_code != 200:
        print("  ERRO - resposta crua:")
        print(resp.text[:1000])
        sys.exit(1)

    login_data = resp.json()
    probe["login"] = login_data
    token = login_data.get("token")
    user  = login_data.get("user", {})
    uid   = user.get("id") or user.get("userId")

    if not token:
        print("  ERRO: sem campo 'token' na resposta. Verifique o formato:")
        jprint(login_data)
        sys.exit(1)

    session.headers["Authorization"] = f"Token {token}"
    print(f"  ✓ Token obtido. Usuário: {user.get('name', uid)} (id={uid})")

    # ── 2. Turmas ─────────────────────────────────────────────────────────────
    print("\n[2/5] Listando turmas do professor…")
    r = session.get(f"{API}/group", params={"professor": uid, "limit": 20, "offset": 0})
    print(f"  Status: {r.status_code}  URL: {r.url}")
    if r.status_code != 200:
        print("  ERRO - resposta crua:")
        print(r.text[:1000])
        # Tenta URL alternativa
        r2 = session.get(f"{API}/group", params={"user": uid, "limit": 20})
        print(f"  Tentativa alternativa (?user=): {r2.status_code}")
        print(r2.text[:500])
        sys.exit(1)

    groups_raw = r.json()
    probe["groups_raw"] = groups_raw
    groups = groups_raw if isinstance(groups_raw, list) else groups_raw.get("data", [])
    jprint(groups[:3], "Primeiras turmas")
    print(f"  ✓ {len(groups)} turma(s) encontrada(s).")

    if not groups:
        print("  Nenhuma turma. Encerrando probe.")
        _save(probe, args.out)
        return

    # Usa --group-id se fornecido, senão pega a primeira
    if args.group_id:
        group = next((g for g in groups if str(g.get("id")) == args.group_id), groups[0])
    else:
        group = groups[0]
    gid   = group.get("id")
    gname = group.get("name", str(gid))
    print(f"  Usando turma: '{gname}' (id={gid})")

    # ── 3. Questionários ──────────────────────────────────────────────────────
    print(f"\n[3/5] Listando questionários da turma {gid}…")
    time.sleep(0.3)
    r = session.get(f"{API}/quizz", params={"group": gid, "limit": 20, "offset": 0})
    print(f"  Status: {r.status_code}  URL: {r.url}")
    quizzes_raw = r.json()
    probe["quizzes_raw"] = quizzes_raw
    quizzes = quizzes_raw if isinstance(quizzes_raw, list) else quizzes_raw.get("data", [])
    jprint(quizzes[:2], "Primeiros questionários")
    print(f"  ✓ {len(quizzes)} questionário(s).")

    if not quizzes:
        print("  Nenhum questionário. Encerrando probe.")
        _save(probe, args.out)
        return

    quiz = quizzes[0]
    qid  = quiz.get("id")

    # ── 4. Problemas do questionário ──────────────────────────────────────────
    print(f"\n[4/5] Listando problemas do questionário {qid}…")
    time.sleep(0.3)
    r = session.get(f"{API}/quizzProblem", params={"quizz": qid, "limit": 50, "offset": 0})
    print(f"  Status: {r.status_code}  URL: {r.url}")
    qprobs_raw = r.json()
    probe["quizzProblems_raw"] = qprobs_raw
    qprobs = qprobs_raw if isinstance(qprobs_raw, list) else qprobs_raw.get("data", [])
    jprint(qprobs[:2], "Primeiros problemas do questionário")
    print(f"  ✓ {len(qprobs)} problema(s) no questionário.")

    if not qprobs:
        print("  Sem problemas. Encerrando probe.")
        _save(probe, args.out)
        return

    qp  = qprobs[0]
    pid = (qp.get("problem") or {}).get("id") or qp.get("problemId")
    print(f"  Usando problema id={pid}")

    # ── 5. Submissões ─────────────────────────────────────────────────────────
    print(f"\n[5a/5] Listando submissões do problema {pid} na turma {gid}…")
    time.sleep(0.3)
    r = session.get(f"{API}/submission",
                    params={"group": gid, "problem": pid, "limit": 20, "offset": 0})
    print(f"  Status: {r.status_code}  URL: {r.url}")
    subs_raw = r.json()
    probe["submissions_raw"] = subs_raw
    subs = subs_raw if isinstance(subs_raw, list) else subs_raw.get("data", [])
    jprint(subs[:2], "Primeiras submissões")
    print(f"  ✓ {len(subs)} submissão(ões).")

    # Busca detalhe de uma submissão em C
    c_sub = next(
        (s for s in subs
         if str(s.get("language", "")).upper().startswith("C")
         and "CPP" not in str(s.get("language", "")).upper()),
        subs[0] if subs else None
    )

    if c_sub:
        sid = c_sub.get("id")
        print(f"\n[5b/5] Buscando detalhe da submissão {sid}…")
        time.sleep(0.3)
        r2 = session.get(f"{API}/submission/{sid}")
        print(f"  Status: {r2.status_code}  URL: {r2.url}")
        detail = r2.json()
        probe["submission_detail"] = detail

        code = detail.get("source") or detail.get("code") or detail.get("sourceCode", "")
        if code:
            print(f"  ✓ Código obtido! Primeiras linhas:\n")
            print("    " + "\n    ".join(code.splitlines()[:8]))
        else:
            print("  ⚠ Campo de código não encontrado. Campos disponíveis:")
            print("    ", list(detail.keys()))

    _save(probe, args.out)
    print(f"\n✓ Probe concluído. Dados salvos em '{args.out}'")
    print("  Abra esse arquivo para inspecionar a estrutura real dos JSONs")
    print("  e ajustar collectors/thehuxley.py se necessário.")


def _save(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

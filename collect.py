#!/usr/bin/env python3
"""
Coletor de Submissões em C para Análise de Erros de Iniciantes
Suporte: CodeBench | BOCA | VPL (Moodle)

Uso:
    python collect.py codebench --url https://codebench.ufam.edu.br --user prof@email.com --password SENHA
    python collect.py boca     --url http://localhost/boca --user admin --password SENHA
    python collect.py vpl      --url https://moodle.inst.edu.br --token SEU_TOKEN_MOODLE

Os arquivos .c coletados são salvos em ./output/<plataforma>/<exercicio>/<submissao>.c
Um arquivo metadata.json é gerado com informações de cada submissão.
"""

import argparse
import sys
import logging
from pathlib import Path

from collectors.codebench import CodeBenchCollector
from collectors.boca import BocaCollector
from collectors.vpl import VplCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("collector.log"),
    ],
)
log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coleta submissões em C de plataformas de juízes online",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output", default="output", help="Diretório raiz de saída (padrão: ./output)"
    )
    parser.add_argument(
        "--max-per-exercise",
        type=int,
        default=0,
        help="Limite de submissões por exercício (0 = sem limite)",
    )
    parser.add_argument(
        "--only-wrong",
        action="store_true",
        help="Coletar apenas submissões incorretas (WA/CE/TLE/RE)",
    )

    sub = parser.add_subparsers(dest="platform", required=True)

    # ── CodeBench ──────────────────────────────────────────────────────────────
    cb = sub.add_parser("codebench", help="Coletar do CodeBench (UFAM)")
    cb.add_argument("--url", default="https://codebench.ufam.edu.br")
    cb.add_argument("--user", required=True, help="E-mail do professor")
    cb.add_argument("--password", required=True)
    cb.add_argument("--course-id", help="ID do curso (omitir lista todos os cursos do usuário)")

    # ── BOCA ───────────────────────────────────────────────────────────────────
    boca = sub.add_parser("boca", help="Coletar do BOCA (instância local)")
    boca.add_argument("--url", required=True, help="URL base do BOCA (ex: http://localhost/boca)")
    boca.add_argument("--user", required=True, help="Usuário admin/staff")
    boca.add_argument("--password", required=True)
    boca.add_argument("--contest-id", default="1", help="ID do contest (padrão: 1)")

    # ── VPL / Moodle ───────────────────────────────────────────────────────────
    vpl = sub.add_parser("vpl", help="Coletar do VPL (plugin Moodle)")
    vpl.add_argument("--url", required=True, help="URL base do Moodle")
    vpl.add_argument(
        "--token",
        help="Token de serviço do Moodle (gerar em Moodle > Preferências > Tokens de segurança)",
    )
    vpl.add_argument("--user", help="Usuário Moodle (alternativa ao token)")
    vpl.add_argument("--password", help="Senha Moodle (alternativa ao token)")
    vpl.add_argument("--course-id", help="ID do curso Moodle")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    options = {
        "output_dir": output_dir,
        "max_per_exercise": args.max_per_exercise,
        "only_wrong": args.only_wrong,
    }

    collectors = {
        "codebench": CodeBenchCollector,
        "boca": BocaCollector,
        "vpl": VplCollector,
    }

    collector_cls = collectors[args.platform]
    collector = collector_cls(args, options)

    log.info(f"Iniciando coleta em [{args.platform.upper()}] → {output_dir}")
    try:
        collector.run()
    except KeyboardInterrupt:
        log.warning("Coleta interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        log.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

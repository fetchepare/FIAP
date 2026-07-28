"""
Script standalone para inicializar e popular o banco de dados.

Execute da raiz do projeto:
    python seed_db.py

Pode ser rodado múltiplas vezes com segurança — não duplica dados.
Para resetar o banco do zero, use:
    python seed_db.py --reset
"""
import sys
from pathlib import Path

# Garante que a raiz do projeto está no path independente de onde o script é chamado
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.database.db import DB_PATH, init_db, get_conn
from src.database.seed import seed


def main():
    reset = "--reset" in sys.argv
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Banco removido: {DB_PATH}")

    init_db()
    seed()

    with get_conn() as c:
        counts = {
            "pacientes":         c.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0],
            "leituras_vitais":   c.execute("SELECT COUNT(*) FROM leituras_vitais").fetchone()[0],
            "resultados_audio":  c.execute("SELECT COUNT(*) FROM resultados_audio").fetchone()[0],
            "resultados_video":  c.execute("SELECT COUNT(*) FROM resultados_video").fetchone()[0],
            "resultados_fusao":  c.execute("SELECT COUNT(*) FROM resultados_fusao").fetchone()[0],
            "alertas":           c.execute("SELECT COUNT(*) FROM alertas").fetchone()[0],
        }

    print(f"\nBanco: {DB_PATH}")
    print("─" * 40)
    for tabela, n in counts.items():
        print(f"  {tabela:<22} {n} registros")
    print("─" * 40)
    print("✅ Banco inicializado com sucesso.\n")
    print("Para iniciar a API:")
    print("  uvicorn src.api.main:app --reload --port 8000\n")


if __name__ == "__main__":
    main()

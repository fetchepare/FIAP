"""CLI administrativa: python -m guardia.cli create-user|init"""
import argparse
import getpass

from . import auth, db


def main():
    ap = argparse.ArgumentParser(prog="guardia")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init")
    cu = sp.add_parser("create-user")
    cu.add_argument("username"); cu.add_argument("full_name"); cu.add_argument("role", choices=["admin", "profissional", "auditor"])
    a = ap.parse_args()
    if a.cmd == "init":
        pw = auth.bootstrap_admin()
        print("Banco pronto." + (f" Senha inicial do admin (guarde!): {pw}" if pw else ""))
    else:
        db.init_db()
        auth.create_user(a.username, a.full_name, getpass.getpass("Senha: "), a.role, actor="cli")
        print("Usuário criado.")


if __name__ == "__main__":
    main()

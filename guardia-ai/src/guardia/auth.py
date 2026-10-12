"""Autenticação (bcrypt + lockout), JWT e RBAC."""
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from . import config, db

PERMISSIONS = {
    "analyze": {"admin", "profissional"},
    "review": {"admin", "profissional"},
    "view_own": {"admin", "profissional"},
    "view_all": {"admin", "auditor"},
    "view_audit": {"admin", "auditor"},
    "manage_users": {"admin"},
    "ask": {"admin", "profissional"},
}


class AuthError(Exception):
    pass


class Forbidden(Exception):
    pass


def can(role: str, perm: str) -> bool:
    return role in PERMISSIONS.get(perm, set())


def require(user: dict, perm: str) -> None:
    if not can(user["role"], perm):
        db.audit(user["username"], "ACCESS_DENIED", {"perm": perm})
        raise Forbidden(f"Perfil '{user['role']}' sem permissão para '{perm}'.")


def validate_password(pw: str) -> None:
    if len(pw) < 10 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        raise AuthError("Senha deve ter ao menos 10 caracteres, com letras e números.")


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()


def create_user(username: str, full_name: str, password: str, role: str, actor: str = "system") -> int:
    validate_password(password)
    if role not in {"admin", "profissional", "auditor"}:
        raise AuthError("Perfil inválido.")
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,32}", username):
        raise AuthError("Usuário: 3–32 caracteres [a-z0-9._-].")
    with db.conn() as c:
        try:
            cur = c.execute(
                "INSERT INTO users(username,full_name,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                (username, full_name.strip(), hash_password(password), role, db.now()),
            )
        except Exception as e:  # UNIQUE
            raise AuthError("Usuário já existe.") from e
        uid = cur.lastrowid
    db.audit(actor, "USER_CREATED", {"username": username, "role": role})
    return uid


def authenticate(username: str, password: str) -> dict:
    """Mensagem de erro genérica (não revela se o usuário existe)."""
    username = username.strip().lower()
    generic = AuthError("Usuário ou senha inválidos.")
    with db.conn() as c:
        u = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not u:
            bcrypt.checkpw(b"x", bcrypt.hashpw(b"y", bcrypt.gensalt(rounds=12)))  # equaliza tempo
            fail = ("unknown_user", None)
        elif not u["active"]:
            fail = ("inactive", None)
        elif u["locked_until"] and datetime.fromisoformat(u["locked_until"]) > datetime.now(timezone.utc):
            fail = ("locked", AuthError(f"Conta bloqueada por {config.LOCK_MIN} min após tentativas inválidas."))
        elif not bcrypt.checkpw(password.encode(), u["password_hash"].encode()):
            n = u["failed_attempts"] + 1
            lock = None
            if n >= config.MAX_FAILED:
                lock = (datetime.now(timezone.utc) + timedelta(minutes=config.LOCK_MIN)).isoformat()
                n = 0
            c.execute("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?", (n, lock, u["id"]))
            fail = ("bad_password" + ("+LOCK" if lock else ""), None)
        else:
            c.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?", (u["id"],))
            fail = None
    if fail:
        db.audit(username, "LOGIN_FAIL", fail[0])
        raise (fail[1] or generic)
    db.audit(username, "LOGIN_OK")
    return {"id": u["id"], "username": u["username"], "full_name": u["full_name"], "role": u["role"]}


def issue_token(user: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_TTL_MIN)
    return jwt.encode({"sub": user["username"], "role": user["role"], "uid": user["id"], "exp": exp},
                      config.get_secret(), algorithm=config.JWT_ALG)


def user_from_token(token: str) -> dict:
    try:
        p = jwt.decode(token, config.get_secret(), algorithms=[config.JWT_ALG])
    except jwt.PyJWTError as e:
        raise AuthError("Token inválido ou expirado.") from e
    with db.conn() as c:
        u = c.execute("SELECT id,username,full_name,role,active FROM users WHERE id=?", (p["uid"],)).fetchone()
    if not u or not u["active"]:
        raise AuthError("Usuário inativo.")
    return {k: u[k] for k in ("id", "username", "full_name", "role")}


def bootstrap_admin() -> str | None:
    """Cria o admin inicial se não houver usuários. Senha: GUARDIA_ADMIN_PASSWORD ou gerada (retornada)."""
    db.init_db()
    with db.conn() as c:
        if c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]:
            return None
    env_pw = os.getenv("GUARDIA_ADMIN_PASSWORD")
    pw = env_pw or (secrets.token_urlsafe(12) + "9a")
    create_user("admin", "Administrador", pw, "admin")
    return None if env_pw else pw

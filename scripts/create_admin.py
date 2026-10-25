"""Cria o primeiro administrador no terminal; a senha não passa por argumentos ou logs."""
import getpass
import secrets
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

def main():
    app.init()
    with app.db() as c:
        if c.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            print('Já existe um administrador. Nenhuma conta foi alterada.')
            return
    name=input('Nome do administrador: ').strip()
    email=input('E-mail: ').strip().lower()
    password=getpass.getpass('Senha (mínimo 8 caracteres): ')
    confirmation=getpass.getpass('Confirme a senha: ')
    if not name or '@' not in email or len(password)<8 or password!=confirmation:
        raise SystemExit('Dados inválidos ou senhas diferentes. Nenhuma conta foi criada.')
    salt=secrets.token_hex(16)
    with app.db() as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():raise SystemExit('Administrador já criado por outra sessão.')
        c.execute('INSERT INTO users(name,email,password,salt,role) VALUES(?,?,?,?,?)',(name,email,app.password(password,salt),salt,'admin'))
        from europe import seed
        from attractions import attach_guides
        seed(c);attach_guides(c)
    print('Administrador criado. Entre no site usando seu e-mail e sua senha.')

if __name__=='__main__':main()

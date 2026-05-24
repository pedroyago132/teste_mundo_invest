from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uuid
from datetime import datetime
import uvicorn
from graphql_service import (
    graphql_create_card,
    graphql_update_card
)

from schemas.index import (
    Client,
    Card,
    UpdateCard
)

app = FastAPI()

# =========================
# SQLITE
# =========================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)




cursor = conn.cursor()




# =========================
# TABELA CLIENTS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome TEXT,
    cliente_email TEXT UNIQUE,
    tipo_solicitacao TEXT,
    valor_patrimonio REAL,
    created_at TEXT
)
""")

# =========================
# TABELA CARDS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    pipefy_card_id TEXT,
    event_id TEXT,
    card_name TEXT,
    cliente_nome TEXT,
    cliente_email TEXT,
    valor_patrimonio REAL,
    tipo_solicitacao TEXT,
    status TEXT,
    prioridade TEXT,
    ultima_alteracao TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id)
)
""")

conn.commit()



# =========================
# CREATE CLIENT
# =========================

@app.post("/clients")
def create_client(client: Client):

    created_at = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO clients (
            cliente_nome,
            cliente_email,
            tipo_solicitacao,
            valor_patrimonio,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        client.cliente_nome,
        client.cliente_email,
        client.tipo_solicitacao,
        client.valor_patrimonio,
        created_at
    ))

    conn.commit()

    client_id = cursor.lastrowid

    return {
        "data": {
            "client": {
                "id": client_id,
                "cliente_nome": client.cliente_nome,
                "cliente_email": client.cliente_email,
                "tipo_solicitacao": client.tipo_solicitacao,
                "valor_patrimonio": client.valor_patrimonio,
                "created_at": created_at
            }
        }
    }

# =========================
# CREATE CARD
# =========================

@app.post("/cards")
def create_card(card: Card):

    # =========================
    # LOCALIZA CLIENTE
    # =========================

    cursor.execute(
        "SELECT * FROM clients WHERE cliente_email = ?",
        (card.cliente_email,)
    )

    client = cursor.fetchone()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    client_id = client[0]
    cliente_nome = client[1]
    cliente_email = client[2]
    tipo_solicitacao = client[3]
    valor_patrimonio = client[4]

    # =========================
    # REGRAS
    # =========================

    prioridade = (
        "prioridade_alta"
        if valor_patrimonio >= 200000
        else "prioridade_normal"
    )

    status = "Processado"

    # =========================
    # IDS
    # =========================

    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    pipefy_card_id = f"card_{uuid.uuid4().hex[:10]}"

    ultima_alteracao = datetime.utcnow().isoformat()

    # =========================
    # GRAPHQL CREATE CARD
    # =========================

    graphql_payload = graphql_create_card(
        pipefy_card_id,
        cliente_nome,
        cliente_email,
        tipo_solicitacao,
        valor_patrimonio
    )

    # =========================
    # SALVA LOCAL
    # =========================

    cursor.execute("""
        INSERT INTO cards (
            client_id,
            pipefy_card_id,
            event_id,
            card_name,
            cliente_nome,
            cliente_email,
            valor_patrimonio,
            tipo_solicitacao,
            status,
            prioridade,
            ultima_alteracao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        pipefy_card_id,
        event_id,
        card.card_name,
        cliente_nome,
        cliente_email,
        valor_patrimonio,
        tipo_solicitacao,
        "Em Análise",
        prioridade,
        ultima_alteracao
    ))

    conn.commit()

    return {
        "data": {
            "graphql": graphql_payload,
            "local_card": {
                "pipefy_card_id": pipefy_card_id,
                "event_id": event_id,
                "cliente_nome": cliente_nome,
                "cliente_email": cliente_email,
                "valor_patrimonio": valor_patrimonio,
                "status": "Em Análise",
                "prioridade": prioridade,
                "ultima_alteracao": ultima_alteracao
            }
        }
    }


# =========================
# GET CLIENTS
# =========================

@app.get("/clients")
def get_clients():

    cursor.execute("""
        SELECT * FROM clients
    """)

    rows = cursor.fetchall()

    return {
        "data": [
            {
                "id": row[0],
                "cliente_nome": row[1],
                "cliente_email": row[2],
                "tipo_solicitacao": row[3],
                "valor_patrimonio": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    }

# =========================
# UPDATE CARD
# =========================

@app.patch("/cards/{pipefy_card_id}")
def update_card(
    pipefy_card_id: str,
    update: UpdateCard
):

    cursor.execute(
        "SELECT * FROM cards WHERE pipefy_card_id = ?",
        (pipefy_card_id,)
    )

    card = cursor.fetchone()

    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card não encontrado"
        )

    campos = []
    valores = []

    if update.card_name is not None:
        campos.append("card_name = ?")
        valores.append(update.card_name)

    if update.status is not None:
        campos.append("status = ?")
        valores.append(update.status)

    if update.prioridade is not None:
        campos.append("prioridade = ?")
        valores.append(update.prioridade)
    

    if update.prioridade is not None:
        campos.append("cliente_nome = ?")
        valores.append(update.cliente_nome)

   
    if update.prioridade is not None:
        campos.append("valor_patrimonio = ?")
        valores.append(update.valor_patrimonio)   

    ultima_alteracao = datetime.utcnow().isoformat()

    campos.append("ultima_alteracao = ?")
    valores.append(ultima_alteracao)

    query = f"""
        UPDATE cards
        SET {', '.join(campos)}
        WHERE pipefy_card_id = ?
    """

    valores.append(pipefy_card_id)

    cursor.execute(query, valores)

    conn.commit()

    graphql_payload = graphql_update_card(
        pipefy_card_id,
        update.status or card[9],
        update.prioridade or card[10]
    )

    cursor.execute(
        "SELECT * FROM cards WHERE pipefy_card_id = ?",
        (pipefy_card_id,)
    )

    updated_card = cursor.fetchone()

    return {
        "data": {
            "graphql": graphql_payload,
            "updated_card": {
                "id": updated_card[0],
                "pipefy_card_id": updated_card[2],
                "event_id": updated_card[3],
                "card_name": updated_card[4],
                "cliente_nome": updated_card[5],
                "cliente_email": updated_card[6],
                "valor_patrimonio": updated_card[7],
                "tipo_solicitacao": updated_card[8],
                "status": "Processado",
                "prioridade": updated_card[10],
                "ultima_alteracao": updated_card[11]
            }
        }
    }

# =========================
# GET CARDS
# =========================

@app.get("/cards")
def get_cards():

    cursor.execute("SELECT * FROM cards")

    rows = cursor.fetchall()

    return {
        "data": [
            {
                "id": row[0],
                "pipefy_card_id": row[2],
                "event_id": row[3],
                "card_name": row[4],
                "cliente_nome": row[5],
                "cliente_email": row[6],
                "valor_patrimonio": row[7],
                "tipo_solicitacao": row[8],
                "status": row[9],
                "prioridade": row[10],
                "ultima_alteracao": row[11]
            }
            for row in rows
        ]
    }

# =========================
# RUN
# =========================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
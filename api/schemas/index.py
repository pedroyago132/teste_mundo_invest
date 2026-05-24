from pydantic import BaseModel

from graphql_service import (
    graphql_create_card,
    graphql_update_card
)

class Client(BaseModel):
    cliente_nome: str
    cliente_email: str
    tipo_solicitacao: str
    valor_patrimonio: float


class Card(BaseModel):
    cliente_email: str
    card_name: str
    nome_cliente: str
    tipo_solicitacao: str
    valor_patrimonio: str


class UpdateCard(BaseModel):
    card_name: str | None = None
    cliente_nome: str | None = None
    valor_patrimonio: str | None = None
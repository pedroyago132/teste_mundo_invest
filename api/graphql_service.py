def graphql_create_card(
    pipefy_card_id,
    cliente_nome,
    cliente_email,
    tipo_solicitacao,
    valor_patrimonio
):

    mutation = """
    mutation CreateCard($input: CreateCardInput!) {
      createCard(input: $input) {
        card {
          id
          title
        }
      }
    }
    """

    variables = {
        "input": {
            "pipe_id": 12345,
            "title": cliente_nome,
            "fields_attributes": [
                {
                    "field_id": "cliente_nome",
                    "field_value": cliente_nome
                },
                {
                    "field_id": "cliente_email",
                    "field_value": cliente_email
                },
                {
                    "field_id": "tipo_solicitacao",
                    "field_value": tipo_solicitacao
                },
                {
                    "field_id": "valor_patrimonio",
                    "field_value": str(valor_patrimonio)
                }
            ]
        }
    }

    return {
        "mutation": mutation,
        "variables": variables,
        "simulated_response": {
            "card": {
                "id": pipefy_card_id,
                "title": cliente_nome
            }
        }
    }


def graphql_update_card(
    pipefy_card_id,
    status,
    prioridade
):

    mutation = """
    mutation UpdateCardField($input: UpdateCardFieldInput!) {
      updateCardField(input: $input) {
        card {
          id
        }
      }
    }
    """

    variables = {
        "input": {
            "card_id": pipefy_card_id,
            "field_id": "status",
            "new_value": status
        }
    }

    prioridade_variables = {
        "input": {
            "card_id": pipefy_card_id,
            "field_id": "prioridade",
            "new_value": prioridade
        }
    }

    return {
        "status_mutation": {
            "mutation": mutation,
            "variables": variables
        },
        "prioridade_mutation": {
            "mutation": mutation,
            "variables": prioridade_variables
        }
    }


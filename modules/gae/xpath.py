xpath_search_extrato_cda_error_page = """
//table[
    .//td[
        @id='fundoMenu'
        and normalize-space() = 'Erro'
    ]
]
"""

xpath_gae_app_name_header = """
//div[
    @id='cabecalho'
    and .//text()[
        normalize-space() = 'GAE - GESTÃO DA ARRECADAÇÃO ESTADUAL'
    ]
]
"""

xpath_sefaz_sso_login__aviso_senha_expirada = """
//div[
    @class='errors'
    and contains(normalize-space(.), 'Sua senha expirou')
]
"""

xpath_sefaz_sso_login_button = """
//input[
    @value='ENTRAR'
    and @type='submit'
]
"""

xpath_sefaz_sso_logout_button = """
//button[
    normalize-space(.) = 'Sair'
    and @onclick="location.href='/cas/logout';"
]
"""

xpath__extrato_debito_nao_liquidado__tabela_debitos_por_tipo = """
//legend[
    contains(normalize-space(.), 'DÉBITOS POR TIPO')
]/following::table[
    @id='tbDebitosPorTipo'
]
"""

xpath__extrato_debito_nao_liquidado__tabela_debitos_por_tipo__linha_divida_ativa = """
.//tr[
    td[
        contains(normalize-space(.), '20 - DÍVIDA ATIVA')
    ]
]/td[
  count(
    //table[@id='tbDebitosPorTipo']//th[normalize-space(.)='TOTAL']
    /preceding-sibling::th
  ) + 1
]
"""

xpath__extrato_debito_nao_liquidado__sem_debito = """
//fieldset[
    @class='FieldArea'
]//b[
    normalize-space(text())='Nenhum registro encontrado'
]
"""

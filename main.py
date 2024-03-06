import yfinance as yf
import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import numpy as np

# Definindo o layout do aplicativo Dash
app = dash.Dash(__name__)

# Definindo os ativos disponíveis para seleção no dropdown
available_assets = ['TAEE11.SA', 'ITSA4.SA', 'BBAS3.SA', 'PETR4.SA', 'TGMA3.SA', 'AGRO3.SA', 'VULC3.SA', 'CMIG4.SA',
                    'USIM5.SA', 'KLBN11.SA']


def simulate_portfolio(assets, allocations, start_date, end_date, initial_investment=0, monthly_investment=0):
    # Obtém os preços ajustados de cada ativo
    prices = pd.DataFrame({asset: yf.download(asset, start=start_date, end=end_date)['Adj Close'] for asset in assets})

    # Calcula o retorno diário de cada ativo
    daily_returns = prices.pct_change()

    # Remove o primeiro dia, que pode conter valores nulos após o cálculo do retorno
    daily_returns = daily_returns.dropna()

    # Adiciona o investimento inicial ao primeiro dia
    portfolio_value = initial_investment + np.sum(daily_returns.iloc[0] * allocations * initial_investment)

    # Lista para armazenar o valor do portfólio em cada data
    portfolio_values = [portfolio_value]

    # Loop para simular o investimento mensal e calcular o valor do portfólio em cada data
    for date, daily_return in daily_returns.iloc[1:].iterrows():
        # Calcula o valor do portfólio após o aporte mensal
        if date.day == 1:  # Verifica se é o primeiro dia do mês
            portfolio_value += monthly_investment

        # Atualiza o valor do portfólio para cada ativo com base nos retornos diários e alocações
        portfolio_value *= (1 + np.sum(daily_return * allocations))

        # Adiciona o valor do portfólio na lista
        portfolio_values.append(portfolio_value)

    # Converte a lista para um DataFrame de pandas
    portfolio_cumulative_returns = pd.Series(portfolio_values, index=daily_returns.index)

    return portfolio_cumulative_returns


# Layout do aplicativo
app.layout = html.Div([
    html.H1("Simulação de Carteira de Investimentos"),
    html.Div([
        html.Label("Selecione os ativos:"),
        dcc.Dropdown(
            id='asset-dropdown',
            options=[{'label': asset, 'value': asset} for asset in available_assets],
            value=['TAEE11.SA'],
            multi=True
        )
    ]),

    html.Div([
        html.Label("Data de início:"),
        dcc.Input(id='start-date-input', type='text', value='2018-07-30')
    ]),
    html.Div([
        html.Label("Data de término:"),
        dcc.Input(id='end-date-input', type='text', value='2023-07-30')
    ]),
    html.Div([
        html.Label("Investimento inicial:"),
        dcc.Input(id='initial-investment-input', type='number', value=10000)
    ]),
    html.Div([
        html.Label("Aporte mensal:"),
        dcc.Input(id='monthly-investment-input', type='number', value=1000)
    ]),

    # Botão para simular
    html.Button('Simular', id='simulate-button', n_clicks=0),


    dcc.Graph(id='portfolio-value-graph'),

    dcc.Graph(id='portfolio-relative-performance-graph')
])


# Função de callback para atualizar os gráficos quando o botão for clicado
@app.callback(
    [Output('portfolio-value-graph', 'figure'),
     Output('portfolio-relative-performance-graph', 'figure')],
    [Input('simulate-button', 'n_clicks')],
    [State('asset-dropdown', 'value'),
     State('start-date-input', 'value'),
     State('end-date-input', 'value'),
     State('initial-investment-input', 'value'),
     State('monthly-investment-input', 'value')]
)
def update_graphs(n_clicks, selected_assets, start_date, end_date, initial_investment, monthly_investment):

    if n_clicks > 0:
        # Simula a carteira de investimentos
        allocations = 1 / len(selected_assets)
        simulate_portfolio(selected_assets, allocations, start_date, end_date, initial_investment, monthly_investment)

    # Obtém os dados históricos do IBOV
    ibov_data = yf.download('^BVSP', start=start_date, end=end_date)['Adj Close']
    ibov_daily_returns = ibov_data.pct_change().dropna()

    # Simula o investimento inicial e aportes mensais no IBOV
    ibov_investment_values = [initial_investment]

    for i in range(1, len(ibov_daily_returns)):
        if ibov_daily_returns.index[i].day == 1:  # Verifica se é o primeiro dia do mês
            ibov_investment_values.append(ibov_investment_values[-1] + monthly_investment)
        else:
            ibov_investment_values.append(ibov_investment_values[-1])

        ibov_investment_values[-1] *= (1 + ibov_daily_returns[i])

    ibov_cumulative_returns = pd.Series(ibov_investment_values, index=ibov_daily_returns.index)

    # Calcula o desempenho relativo em relação ao investimento inicial
    allocations = 1 / len(selected_assets)
    portfolio_returns = simulate_portfolio(selected_assets, allocations, start_date, end_date, initial_investment,
                                           monthly_investment)

    portfolio_relative_performance = ((portfolio_returns - initial_investment) / initial_investment) * 100
    ibov_relative_performance = ((ibov_cumulative_returns - initial_investment) / initial_investment) * 100

    # Gráfico da evolução do valor do portfólio e do valor do patrimônio investindo apenas no IBOV
    portfolio_value_graph = {
        'data': [
            {'x': portfolio_returns.index, 'y': portfolio_returns, 'name': 'Carteira Simulada com Aportes'},
            {'x': ibov_cumulative_returns.index, 'y': ibov_cumulative_returns, 'name': 'IBOV com Aportes'}
        ],
        'layout': {
            'title': 'Evolução do Valor do Portfólio e do Patrimônio Investindo no IBOV',
            'xaxis': {'title': 'Data'},
            'yaxis': {'title': 'Valor (R$)'},
            'hovermode': 'x'
        }
    }

    # Gráfico do desempenho da carteira e do IBOV em relação ao investimento inicial
    portfolio_relative_performance_graph = {
        'data': [
            {'x': portfolio_relative_performance.index, 'y': portfolio_relative_performance,
             'name': 'Carteira Simulada com Aportes'},
            {'x': ibov_relative_performance.index, 'y': ibov_relative_performance, 'name': 'IBOV com Aportes'}
        ],
        'layout': {
            'title': 'Desempenho da Carteira e do IBOV em relação ao Investimento Inicial',
            'xaxis': {'title': 'Data'},
            'yaxis': {'title': 'Desempenho Relativo (%)'},
            'hovermode': 'x'
        }
    }

    return portfolio_value_graph, portfolio_relative_performance_graph


if __name__ == '__main__':
    app.run_server(debug=True)

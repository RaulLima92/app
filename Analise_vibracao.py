import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, time

# Função para carregar os dados do Excel dinamicamente
@st.cache_data
def load_data():
    return pd.read_excel('vibra 1.xlsx')

# Carregar os dados ao iniciar o aplicativo
df = load_data()

# Converter colunas de tempo para o formato datetime, se necessário
for col in df.columns:
    if 'Time' in col:
        df[col] = pd.to_datetime(df[col])

# Filtrar colunas que contêm 'ValueY' (grandezas) e 'Time' (tempos)
value_columns = [col for col in df.columns if 'ValueY' in col]
time_columns = [col for col in df.columns if 'Time' in col]

# Criar um dicionário associando os valores aos tempos correspondentes
column_dict = {value_columns[i]: time_columns[i] for i in range(len(value_columns))}

# Função para calcular estatísticas e contagem de valores que atingem 95% da máxima
def calculate_statistics(df, value_column):
    data = df[value_column]
    max_val = data.max()
    min_val = data.min()
    mean_val = data.mean()
    ninety_percent_max = 0.95 * max_val
    count_above_ninety_percent_max = (data >= ninety_percent_max).sum()
    
    return mean_val, max_val, min_val, count_above_ninety_percent_max

# Função para verificar se os valores estão dentro dos limites aceitáveis
def check_acceptability(df, value_column, vibration_type):
    data = df[value_column]
    rms_val = data.mean()  # Exemplo: usando o valor médio como RMS

    if vibration_type == "Relativa":
        if rms_val > 100:
            status = "Inaceitável"
            color = "red"
        elif 50 <= rms_val <= 99.9:
            status = "Alerta"
            color = "orange"
        else:
            status = "Aceitável"
            color = "green"
        reference_values = "Aceitável: <= 50 mm/s, Alerta: 50 - 99.9 mm/s, Inaceitável: > 100 mm/s"
        norma = "Norma utilizada: ISO 10816"
    elif vibration_type == "Absoluta":
        if rms_val > 7.0:
            status = "Inaceitável"
            color = "red"
        elif 5.0 <= rms_val <= 7.0:
            status = "Alerta"
            color = "orange"
        else:
            status = "Aceitável"
            color = "green"
        reference_values = "Aceitável: <= 5.0 mm/s, Alerta: 5.0 - 7.0 mm/s, Inaceitável: > 7.0 mm/s"
        norma = "Norma utilizada: ISO 10816"
    
    return status, color, reference_values, norma

st.title("Gráficos de Monitoramento do CS")

# Menu lateral para filtros
with st.sidebar:
    st.header("Filtros")

    # Seleção da grandeza
    selected_value_column = st.selectbox("Selecione a Grandeza:", value_columns)
    
    # Seleção de múltiplas grandezas (para comparação)
    selected_value_columns = st.multiselect("Selecione múltiplas Grandezas para Comparação:", value_columns, default=[selected_value_column])
    
    # Seleção da data inicial e final
    start_date = st.date_input("Data Inicial:", min_value=df[column_dict[selected_value_column]].min().date(), max_value=df[column_dict[selected_value_column]].max().date(), value=df[column_dict[selected_value_column]].min().date())
    end_date = st.date_input("Data Final:", min_value=df[column_dict[selected_value_column]].min().date(), max_value=df[column_dict[selected_value_column]].max().date(), value=df[column_dict[selected_value_column]].max().date())

    # Seleção de hora e minuto inicial e final em um único campo
    start_time = st.time_input("Horário inicial", value=time(0, 0))
    start_seconds = st.number_input("Segundos iniciais", min_value=0, max_value=59, value=0)
    
    end_time = st.time_input("Horário final", value=time(23, 59))
    end_seconds = st.number_input("Segundos finais", min_value=0, max_value=59, value=59)

# Combinar data e hora com segundos
start_datetime = datetime.combine(start_date, time(start_time.hour, start_time.minute, start_seconds))
end_datetime = datetime.combine(end_date, time(end_time.hour, end_time.minute, end_seconds))

# Filtrar o dataframe pelo intervalo de tempo selecionado
filtered_df = df[(df[column_dict[selected_value_column]] >= start_datetime) & (df[column_dict[selected_value_column]] <= end_datetime)]

# Criar o gráfico com as colunas selecionadas e adicionar hovermode
fig = px.line(filtered_df, x=column_dict[selected_value_column], y=selected_value_columns, 
              title=f'Gráfico Comparativo de {selected_value_columns}')
fig.update_layout(
    hovermode='x',  # Hover horizontal para seguir a linha do gráfico
    xaxis_title="Tempo",
    yaxis_title="Valores"
)
fig.update_traces(
    hovertemplate='Tempo: %{x}<br>Valor: %{y}<extra></extra>'  # Formato do hover
)

# Exibir o gráfico
st.plotly_chart(fig, use_container_width=True)

# Calcular estatísticas com os dados filtrados
mean_val, max_val, min_val, count_above_ninety_percent_max = calculate_statistics(filtered_df, selected_value_column)

# Exibir as estatísticas
st.subheader("Estatísticas:")
st.write(f"Máxima: {max_val:.3f}")
st.write(f"Média: {mean_val:.3f}")
st.write(f"Mínima: {min_val:.3f}")
st.write(f"Contagem de valores que atingem 95% da máxima: {count_above_ninety_percent_max}")

# Avaliação de Aceitabilidade
vibration_type = st.sidebar.radio("Selecione o Tipo de Vibração:", ['Relativa', 'Absoluta'])

status, color, reference_values, norma = check_acceptability(df, selected_value_column, vibration_type)

# Exibir o status da vibração
st.markdown(f"<span style='color:{color};font-size:20px;'>Status de vibração ({vibration_type}): {status}</span>", unsafe_allow_html=True)
st.write(f"Valores de Referência: {reference_values} ({norma})")

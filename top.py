import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime
import plotly.graph_objects as go

def main():
    st.header('두 기업 주식 데이터 비교 분석')
    st.sidebar.markdown('분석할 기업을 선택하세요')

    # Using "with" notation
    with st.sidebar:
        company1 = st.text_input("첫 번째 기업명", "")
        company2 = st.text_input("두 번째 기업명", "")

    today = datetime.datetime.now()
    jan_1 = datetime.date(today.year, 1, 1)

    # Using "with" notation
    with st.sidebar:
        d = st.date_input(
            "시작일 - 종료일",
            (jan_1, today.date()),
            format="YYYY-MM-DD",
        )

    accept = st.sidebar.button("데이터 비교")

    if accept and company1 and company2:
        ticker_symbol1 = get_ticker_symbol(company1)
        ticker_symbol2 = get_ticker_symbol(company2)

        if ticker_symbol1 and ticker_symbol2:
            df_company1 = get_stock_data(ticker_symbol1, d[0], d[1])
            df_company2 = get_stock_data(ticker_symbol2, d[0], d[1])

            # 시각화
            plot_stock_comparison(df_company1, df_company2)
        else:
            st.error("입력한 기업 중 하나 이상의 정보를 찾을 수 없습니다.")
            
def get_stock_data(stock_code, start_date, end_date):
    df = fdr.DataReader(stock_code, start_date, end_date)
    df['Returns'] = df['Close'].pct_change() * 100  # 주가 수익률 계산
    df.index = df.index.date
    return df

def get_ticker_symbol(company_name):
    df = get_stock_info()
    code = df[df['회사명'] == company_name]['Symbol'].values
    ticker_symbol = code[0] if len(code) > 0 else None
    return ticker_symbol

def get_stock_info():
    base_url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
    method = "download"
    url = "{0}?method={1}".format(base_url, method)
    df = pd.read_html(url, header=0, encoding='cp949')[0]
    df['Symbol'] = df['Symbol'].apply(lambda x: f"{x:06d}")
    df = df[['회사명', 'Symbol']]
    return df

def plot_stock_comparison(df1, df2):
    st.subheader("두 기업의 주식 데이터 비교")
    fig = go.Figure()

    # 종가 비교
    fig.add_trace(go.Scatter(x=df1.index, y=df1['Close'], mode='lines', name=f'{df1["Symbol"].iloc[0]} 종가'))
    fig.add_trace(go.Scatter(x=df2.index, y=df2['Close'], mode='lines', name=f'{df2["Symbol"].iloc[0]} 종가'))

    # 변동률 비교
    fig.add_trace(go.Scatter(x=df1.index, y=df1['Returns'], mode='lines', name=f'{df1["Symbol"].iloc[0]} 변동률'))
    fig.add_trace(go.Scatter(x=df2.index, y=df2['Returns'], mode='lines', name=f'{df2["Symbol"].iloc[0]} 변동률'))

    fig.update_layout(title='두 기업의 주식 데이터 비교', xaxis_title='날짜', yaxis_title='값')
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go

def main():
    st.header('주식 골든크로스와 데드크로스 시각화')
    st.sidebar.markdown('분석할 기업을 선택하세요')

    with st.sidebar:
        company = st.text_input("기업명", "")

    today = pd.Timestamp.today()
    jan_1 = pd.Timestamp(today.year, 1, 1)

    with st.sidebar:
        start_date = st.date_input(
            "분석 시작일",
            jan_1,
            format="YYYY-MM-DD",
        )
        end_date = st.date_input(
        "분석 종료일",
        today,
        format="YYYY-MM-DD",
    )

    accept = st.sidebar.button("골든크로스/데드크로스 시각화")

    if accept and company:
        ticker_symbol = get_ticker_symbol(company)

        if ticker_symbol:
            df = get_stock_data(ticker_symbol, start_date, today)
            plot_golden_dead_cross(df)
            plot_price_change(df)
            plot_average_price_change(df)
            plot_close_price_changes(df)
        else:
            st.error("입력한 기업의 정보를 찾을 수 없습니다.")

def get_stock_data(stock_code, start_date, end_date):
    df = fdr.DataReader(stock_code, start_date, end_date)
    df['Short_MA'] = df['Close'].rolling(window=5).mean()
    df['Long_MA'] = df['Close'].rolling(window=20).mean()
    return df

def get_ticker_symbol(company_name):
    df = get_stock_info()
    code = df[df['회사명'] == company_name]['종목코드'].values
    ticker_symbol = code[0] if len(code) > 0 else None
    return ticker_symbol

def get_stock_info():
    base_url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
    method = "download"
    url = "{0}?method={1}".format(base_url, method)
    df = pd.read_html(url, header=0, encoding='cp949')[0]
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    df = df[['회사명', '종목코드']]
    return df

def plot_golden_dead_cross(df):
    st.subheader("골든크로스와 데드크로스 시각화")
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='종가'))
    fig.add_trace(go.Scatter(x=df.index, y=df['Short_MA'], mode='lines', name='단기 이동평균선'))
    fig.add_trace(go.Scatter(x=df.index, y=df['Long_MA'], mode='lines', name='장기 이동평균선'))

    golden_cross_points = df[(df['Short_MA'] > df['Long_MA']) & (df['Short_MA'].shift(1) <= df['Long_MA'].shift(1))].index
    dead_cross_points = df[(df['Short_MA'] < df['Long_MA']) & (df['Short_MA'].shift(1) >= df['Long_MA'].shift(1))].index

    fig.add_trace(go.Scatter(x=golden_cross_points, y=df['Short_MA'][golden_cross_points],
                             mode='markers', marker=dict(color='green', size=10, symbol='triangle-up'),
                             name='골든크로스'))
    fig.add_trace(go.Scatter(x=dead_cross_points, y=df['Short_MA'][dead_cross_points],
                             mode='markers', marker=dict(color='red', size=10, symbol='triangle-down'),
                             name='데드크로스'))

    fig.update_layout(
        title=dict(text='골든크로스와 데드크로스 시각화', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='날짜', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='값', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)

def plot_price_change(df):
    st.subheader("골든크로스와 데드크로스 전후 주가 수익률 변화")
    fig = go.Figure()

    df['Price_Change'] = df['Close'].pct_change() * 100

    for event_points in [df.index, df[(df['Short_MA'] > df['Long_MA'])].index, df[(df['Short_MA'] < df['Long_MA'])].index]:
        fig.add_trace(go.Scatter(x=event_points, y=df['Price_Change'][event_points],
                                 mode='lines', marker=dict(size=8), line=dict(width=2)))

    fig.update_layout(
        title=dict(text='골든크로스와 데드크로스 전후 주가 수익률 변화', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='날짜', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='주가 수익률 (%)', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)

def plot_average_price_change(df):
    st.subheader("골든크로스와 데드크로스 전후 10일간 종가 평균 증감")
    fig = go.Figure()

    golden_cross_points = df[(df['Short_MA'] > df['Long_MA']) & (df['Short_MA'].shift(1) <= df['Long_MA'].shift(1))].index
    dead_cross_points = df[(df['Short_MA'] < df['Long_MA']) & (df['Short_MA'].shift(1) >= df['Long_MA'].shift(1))].index

    for event_points in [golden_cross_points, dead_cross_points]:
        for point in event_points:
            # 골든크로스/데드크로스 전후 10일간의 종가 데이터 추출
            before_cross = df['Close'][point - pd.DateOffset(days=10):point].mean()
            after_cross = df['Close'][point:point + pd.DateOffset(days=10)].mean()

            fig.add_trace(go.Scatter(x=[point - pd.DateOffset(days=10), point, point + pd.DateOffset(days=10)],
                                     y=[before_cross, df['Close'][point], after_cross],
                                     mode='lines+markers', marker=dict(size=8),
                                     line=dict(width=2), name=f'Point {point}'))

    fig.update_layout(
        title=dict(text='골든크로스와 데드크로스 전후 10일간 종가 평균 증감', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='날짜', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='종가 평균', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)

def plot_close_price_changes(df):
    st.subheader("골든크로스와 데드크로스 전후 종가 변화")
    fig = go.Figure()

    golden_cross_points = df[(df['Short_MA'] > df['Long_MA']) & (df['Short_MA'].shift(1) <= df['Long_MA'].shift(1))].index
    dead_cross_points = df[(df['Short_MA'] < df['Long_MA']) & (df['Short_MA'].shift(1) >= df['Long_MA'].shift(1))].index

    for event_points in [golden_cross_points, dead_cross_points]:
        for point in event_points:
            # 골든크로스/데드크로스 전후 종가 데이터 추출
            before_cross = df['Close'][point - pd.DateOffset(days=10):point]
            after_cross = df['Close'][point:point + pd.DateOffset(days=10)]

            fig.add_trace(go.Scatter(x=before_cross.index, y=before_cross,
                                     mode='lines+markers', marker=dict(size=8),
                                     line=dict(width=2), name=f'Point {point} - Before'))
            fig.add_trace(go.Scatter(x=after_cross.index, y=after_cross,
                                     mode='lines+markers', marker=dict(size=8),
                                     line=dict(width=2), name=f'Point {point} - After'))

    fig.update_layout(
        title=dict(text='골든크로스와 데드크로스 전후 종가 변화', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='날짜', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='종가', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)

if __name__ == "__main__":
    main()

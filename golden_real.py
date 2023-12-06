import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from io import BytesIO
import base64

def main():
    st.header('돈을 똑똑하게 벌어보자!')
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
            plot_golden_cross_returns(df, start_date, today)
            plot_dead_cross_returns(df, start_date, today)
            download_csv_button(df, f"{company}_stock_data.csv")
        else:
            st.error("입력한 기업의 정보를 찾을 수 없습니다.")

#단기이동평균,장기이동평균 계산 함수
def get_stock_data(stock_code, start_date, end_date):
    df = fdr.DataReader(stock_code, start_date, end_date)
    df['Short_MA'] = df['Close'].rolling(window=5).mean()
    df['Long_MA'] = df['Close'].rolling(window=20).mean()
    return df

#입력받은 기억명의 종목코드 반환 함수
def get_ticker_symbol(company_name):
    df = get_stock_info()
    code = df[df['회사명'] == company_name]['종목코드'].values
    ticker_symbol = code[0] if len(code) > 0 else None
    return ticker_symbol

#KRX 기업정보 스크래핑 및 데이터프레임으로 변환
@st.cache_data
def get_stock_info():
    base_url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
    method = "download"
    url = "{0}?method={1}".format(base_url, method)
    df = pd.read_html(url, header=0, encoding='cp949')[0]
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    df = df[['회사명', '종목코드']]
    return df

#입력받은 주식 데이터프레임을 사용하여 주식의 종가 및 이동평균 데이터 시각화
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

#골든크로스 발생한 지점부터 일정 기간 후 주식 수익률을 box plot으로 시각화
def plot_golden_cross_returns(df, start_date, end_date):
    st.subheader("골든크로스 매매 후 수익률 변화")
    golden_cross_points = df[(df['Short_MA'] > df['Long_MA']) & (df['Short_MA'].shift(1) <= df['Long_MA'].shift(1))].index
    returns_1_month = []
    returns_3_months = []
    returns_6_months = []

    for point in golden_cross_points:
        end_date_1_month = point + pd.DateOffset(months=1)
        end_date_3_months = point + pd.DateOffset(months=3)
        end_date_6_months = point + pd.DateOffset(months=6)

        if end_date_1_month <= end_date and end_date_1_month in df.index:
            returns_1_month.append((df['Close'][end_date_1_month] / df['Close'][point] - 1) * 100)
        if end_date_3_months <= end_date and end_date_3_months in df.index:
            returns_3_months.append((df['Close'][end_date_3_months] / df['Close'][point] - 1) * 100)
        if end_date_6_months <= end_date and end_date_6_months in df.index:
            returns_6_months.append((df['Close'][end_date_6_months] / df['Close'][point] - 1) * 100)

    fig = go.Figure()
    fig.add_trace(go.Box(y=returns_1_month, name='1개월 후'))
    fig.add_trace(go.Box(y=returns_3_months, name='3개월 후'))
    fig.add_trace(go.Box(y=returns_6_months, name='6개월 후'))

    fig.update_layout(
        title=dict(text='골든크로스 매매 후 수익률 변화', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='매매 시점', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='수익률 (%)', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)


#데드크로스 발생한 지점부터 일정 기간 후 주식 수익률을 box plot으로 시각화
def plot_dead_cross_returns(df, start_date, end_date):
    st.subheader("데드크로스 매매 후 수익률 변화")
    dead_cross_points = df[(df['Short_MA'] < df['Long_MA']) & (df['Short_MA'].shift(1) >= df['Long_MA'].shift(1))].index
    returns_1_month = []
    returns_3_months = []
    returns_6_months = []

    for point in dead_cross_points:
        end_date_1_month = point + pd.DateOffset(months=1)
        end_date_3_months = point + pd.DateOffset(months=3)
        end_date_6_months = point + pd.DateOffset(months=6)

        if end_date_1_month <= end_date and end_date_1_month in df.index:
            returns_1_month.append((df['Close'][end_date_1_month] / df['Close'][point] - 1) * 100)
        if end_date_3_months <= end_date and end_date_3_months in df.index:
            returns_3_months.append((df['Close'][end_date_3_months] / df['Close'][point] - 1) * 100)
        if end_date_6_months <= end_date and end_date_6_months in df.index:
            returns_6_months.append((df['Close'][end_date_6_months] / df['Close'][point] - 1) * 100)

    fig = go.Figure()
    fig.add_trace(go.Box(y=returns_1_month, name='1개월 후'))
    fig.add_trace(go.Box(y=returns_3_months, name='3개월 후'))
    fig.add_trace(go.Box(y=returns_6_months, name='6개월 후'))

    fig.update_layout(
        title=dict(text='데드크로스 매매 후 수익률 변화', font=dict(family='Arial', size=20, color='darkblue')),
        xaxis_title=dict(text='매매 시점', font=dict(family='Arial', size=16, color='darkgreen')),
        yaxis_title=dict(text='수익률 (%)', font=dict(family='Arial', size=16, color='darkgreen')),
        font=dict(family='Arial, sans-serif', size=12, color='black'),
        legend=dict(font=dict(family="Arial, sans-serif", size=12, color="black"))
    )

    st.plotly_chart(fig)

#csv 버튼
def download_csv_button(df, filename):
    csv_data = df.to_csv(index=False, encoding='utf-8')
    b64 = base64.b64encode(csv_data.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">CSV 파일 다운로드</a>'
    st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


import gradio as gr
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import os

alt.renderers.enable('default')

df = pd.read_csv('Weather_cleaned.csv')
df['Date'] = pd.to_datetime(df['Date'])

current_date = datetime.strptime('2024-06-01', '%Y-%m-%d')

def load_css():
    with open('style.css', 'r') as file:
        css_content = file.read()
    return css_content


def get_weather_data(current_date, duration):
    current_hour = datetime.now().hour
    next_date = current_date + timedelta(days=1)
    data = df[(df['Date'] <= current_date) & (df['Date'] > current_date - timedelta(days=duration))]
    # df['Time'] = df['Time'].astype(str).str[:2].astype(int)
    # data = df[ ((df['Date'] == current_date) & (df['Time'] >= current_hour)) |
    # ((df['Date'] == current_date + timedelta(days=duration)) & (df['Time'] <= current_hour + 1)) |
    # ((df['Date'] > current_date) & (df['Date'] < current_date + timedelta(days=duration)))]  # All dates in between]
    return data

def get_weather_data_per_day(current_date):
    next_day = current_date + timedelta(days=1)
    return df[(df['Date'] >= current_date) & (df['Date'] < next_day)]

def truncate_date(date):
    return date.strftime('%m-%d')

def get_day_of_week(date):
    return date.strftime('%A')

def get_weather_data_7_days():
    data = get_weather_data(current_date, 7)
    data = data.groupby(data['Date'].dt.date).agg(
        min_temp=('Temp (°C)', 'min'),
        max_temp=('Temp (°C)', 'max')
    ).reset_index()
    summary = "<div class='summary-container'><h2>7-Day Weather Forecast</h2>"

    for i in range(7):
        date = data['Date'].iloc[i]
        min_temp = data['min_temp'].iloc[i]
        max_temp = data['max_temp'].iloc[i]
        summary += (
        "<div class='forecast-card'>"
            "<div class='forecast-info'>"
                f"<div class='forecast-day'>{get_day_of_week(date)}</div>"
                f"<div class='forecast-date'>{truncate_date(date)}</div>"
            "</div>"
            "<div class='forecast-weather'>"
                "<img src='https://www.awxcdn.com/adc-assets/images/weathericons/6.svg' class='weather-icon'>"
                f"<div class='forecast-temp'><span class='max-temp'>{max_temp:.1f}°</span> "
                f"<span class='min-temp'>{min_temp:.1f}°</span></div>"
            "</div>"
        "</div>"
        )

    summary += "</div>"
    return summary

def get_chart_data():
    data = get_weather_data(current_date, 7)
    data = data.groupby(data['Date'].dt.date).agg(
        min_temp=('Temp (°C)', 'min'),
        max_temp=('Temp (°C)', 'max')
    ).reset_index()

    # print(data)
    data['Date'] = data['Date'].astype(str)
    x_axis = alt.X('Date:T', axis=alt.Axis(labelAngle=0, format='%d-%m'))

    chart = alt.Chart(data).mark_area().encode(
        x=x_axis,
        y=alt.Y('min_temp', title='Temperature (°C)', scale=alt.Scale(domain=[0, 50])),
        y2='max_temp',
        color=alt.value('yellow'),
        opacity=alt.value(0.3)
    ).properties(
        width=800,
        height=400,
    ) + alt.Chart(data).mark_line().encode(
        x='Date',
        y='min_temp',
        color=alt.value('blue')
    ) + alt.Chart(data).mark_line().encode(
        x='Date',
        y='max_temp',
        color=alt.value('red')
    )
    return chart

def chart_line():
    current_hour = datetime.now().hour-4
    next_date = current_date + timedelta(days=1)
    df = get_weather_data(current_date, 7)
    data = df.copy()
    data['Date+Time'] = pd.to_datetime(data['Date'].astype(str) + ' ' + data['Time'].astype(str).str.zfill(2) + 'h')
    data['Time'] = data['Time'].astype(str).str[:2].astype(int)
    # add "h" to the time column
    data['Time'] = data['Time'].astype(str) + "h"
    # Define X-axis with correct formatting
    x_axis = alt.X(
        'Date+Time:T',
        axis=alt.Axis(labelAngle=0, grid=True, title='Date',  format='%m/%d')
    )

    # Create the line chart with points and add a legend for Temperature
    chart_line = alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=120)).encode(
        x=x_axis,
        y=alt.Y('Temp (°C):Q', title='Temperature (°C)', scale=alt.Scale(domain=[18, 50], zero=False)),
        color=alt.Color('Legend:N', scale=alt.Scale(domain=["Temperature"], range=["blue"]),legend=alt.Legend(orient='bottom')),
        tooltip=['Date+Time:T', 'Time:N', 'Temp (°C):Q']
    ).transform_calculate(
        Legend="'Temperature'"  # Adds a fixed legend label
    ).properties(
        width=800,
        height=400
    )
    return chart_line


def get_current_weather():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    data_per_day = get_weather_data_per_day(current_date)

    temperature = f"{data_per_day['Temp (°C)'].mean():.1f}°C"
    wind = f"{data_per_day['Wind (km/h)'].mean():.1f} km/h"
    rain = f"{data_per_day['Rain (mm)'].sum():.1f} mm"

    summary = (
        "<div class='current-weather'>"
        "<div class='current_weather_header'>"
            f"<h2>CURRENT WEATHER</h2>"
            f"<p class='time'>{current_time}</p>"
        "</div>"
        "<hr style='margin: 16px 0;'>"
        f"<div class='weather-info'><div>🌡️ Temperature: {temperature}</div>"
        f"<div>💨 Wind: {wind}</div><div>🌧️ Rain: {rain}</div></div>"
        "</div>"
    )
    return summary

def get_hourly_weather_data():
    current_hour = datetime.now().hour
    next_date = current_date + timedelta(days=1)
    df['Time'] = df['Time'].astype(str).str[:2].astype(int)

    # Fix filtering logic for hourly data
    data = df[((df['Date'] == current_date) & (df['Time'] >= current_hour)) |
              ((df['Date'] == next_date) & (df['Time'] < current_hour))]

    html = "<div class='hourly-container'><h2>Hourly Weather Forecast</h2><p>Forecast for the next 24 hours</p></div>"
    html += "<div class='hourly-forecast'>"

    for i in range(len(data)):
        hour = data['Time'].iloc[i]
        weather_icon = "https://www.awxcdn.com/adc-assets/images/weathericons/6.svg" if hour < 18 else "https://www.awxcdn.com/adc-assets/images/weathericons/36.svg"

        html += (
            "<div class='hour-card'>"
            f"<h3>{hour}:00</h3>"  # Fix hour formatting
            f"<img src='{weather_icon}' class='hour-icon'>"
            f"<p>{data['Temp (°C)'].iloc[i]:.1f}°C</p>"
            "</div>"
        )

    html += "</div>"
    return html

with gr.Blocks(css=load_css()) as demo:  # Ensure correct relative path to CSS file
    weather_summary_output = gr.HTML()
    hourly_weather_output = gr.HTML()
    seven_day_weather_output = gr.HTML()
    weather_chart_output = gr.Plot(elem_id="chart-container")
    chart_line_output = gr.Plot(elem_id="chart-line-container")

    demo.load(fn=get_current_weather, outputs=[weather_summary_output])
    demo.load(fn=get_hourly_weather_data, outputs=[hourly_weather_output])
    demo.load(fn=get_weather_data_7_days, outputs=[seven_day_weather_output])
    demo.load(fn=get_chart_data, outputs=[weather_chart_output])
    demo.load(fn=chart_line, outputs=[chart_line_output])

if __name__ == "__main__":
    print("init project")
    port = int(os.environ.get("PORT", 7860))  # Render provides the PORT
    demo.launch(server_name="0.0.0.0", server_port=port, debug=True)  # Must bind to 0.0.0.0


# from flask import Flask, render_template
# import altair as alt
# import pandas as pd

# app = Flask(__name__)

# @app.route('/chart')
# def index():
#     # Generate Altair chart
#     chart = alt.Chart(data).mark_line(point=True).encode(
#         x='Date+Time:T',
#         y='Temp (°C):Q',
#         color=alt.Color('Legend:N', title="Legend",
#                         scale=alt.Scale(domain=["Temperature"], range=["blue"]),
#                         legend=alt.Legend(orient="bottom", anchor="middle"))
#     ).properties(width=800, height=400)

#     chart.save('static/chart.json')
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)

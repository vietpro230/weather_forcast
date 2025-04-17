import gradio as gr
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# Enable Altair's default renderer
alt.renderers.enable('default')

# Load and preprocess data
df = pd.read_csv('Weather_cleaned.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Set a fixed current date for consistency (can be updated dynamically if needed)
current_date = datetime.strptime('2024-06-01', '%Y-%m-%d')

# Load CSS file
def load_css():
    try:
        with open('style.css', 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ""  # Return empty string if CSS file is missing

# Fetch weather data for a given duration
def get_weather_data(current_date, duration):
    end_date = current_date + timedelta(days=duration)
    return df[(df['Date'] <= end_date) & (df['Date'] > current_date - timedelta(days=duration))]

# Fetch weather data for a single day
def get_weather_data_per_day(current_date):
    next_day = current_date + timedelta(days=1)
    return df[(df['Date'] >= current_date) & (df['Date'] < next_day)]

# Utility functions for formatting
def truncate_date(date):
    return date.strftime('%m-%d')

def get_day_of_week(date):
    return date.strftime('%A')

# Generate 7-day weather forecast HTML
def get_weather_data_7_days():
    data = get_weather_data(current_date, 7)
    data = data.groupby(data['Date'].dt.date).agg(
        min_temp=('Temp (°C)', 'min'),
        max_temp=('Temp (°C)', 'max')
    ).reset_index()

    summary = "<div class='summary-container'><h2>7-Day Weather Forecast</h2>"
    for i in range(min(7, len(data))):  # Ensure we don't exceed available data
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
            "</div></div>"
        )
    summary += "</div>"
    return summary

# Generate 7-day weather chart
def get_chart_data():
    data = get_weather_data(current_date, 7)
    data = data.groupby(data['Date'].dt.date).agg(
        min_temp=('Temp (°C)', 'min'),
        max_temp=('Temp (°C)', 'max')
    ).reset_index()
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
        height=400
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

# Generate hourly line chart
def chart_line():
    current_hour = datetime.now().hour - 4  # Adjust for timezone if needed
    data = get_weather_data(current_date, 7).copy()
    data['Date+Time'] = pd.to_datetime(data['Date'].astype(str) + ' ' + data['Time'].astype(str).str.zfill(2) + ':00')

    x_axis = alt.X('Date+Time:T', axis=alt.Axis(labelAngle=0, grid=True, title='Date', format='%m/%d'))
    chart = alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=120)).encode(
        x=x_axis,
        y=alt.Y('Temp (°C):Q', title='Temperature (°C)', scale=alt.Scale(domain=[18, 50], zero=False)),
        color=alt.Color('Legend:N', scale=alt.Scale(domain=["Temperature"], range=["blue"]), legend=alt.Legend(orient='bottom')),
        tooltip=['Date+Time:T', 'Time:N', 'Temp (°C):Q']
    ).transform_calculate(
        Legend="'Temperature'"
    ).properties(
        width=800,
        height=400
    )
    return chart

# Generate current weather summary
def get_current_weather():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    data_per_day = get_weather_data_per_day(current_date)

    temperature = f"{data_per_day['Temp (°C)'].mean():.1f}°C" if not data_per_day.empty else "N/A"
    wind = f"{data_per_day['Wind (km/h)'].mean():.1f} km/h" if not data_per_day.empty else "N/A"
    rain = f"{data_per_day['Rain (mm)'].sum():.1f} mm" if not data_per_day.empty else "N/A"

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

# Generate hourly weather forecast HTML
def get_hourly_weather_data():
    current_hour = datetime.now().hour
    next_date = current_date + timedelta(days=1)
    df['Time'] = df['Time'].astype(str).str[:2].astype(int)
    data = df[((df['Date'] == current_date) & (df['Time'] >= current_hour)) |
              ((df['Date'] == next_date) & (df['Time'] < current_hour))]

    html = "<div class='hourly-container'><h2>Hourly Weather Forecast</h2><p>Forecast for the next 24 hours</p></div>"
    html += "<div class='hourly-forecast'>"
    for i in range(min(len(data), 24)):  # Limit to 24 hours
        hour = data['Time'].iloc[i]
        weather_icon = "https://www.awxcdn.com/adc-assets/images/weathericons/6.svg" if hour < 18 else "https://www.awxcdn.com/adc-assets/images/weathericons/36.svg"
        html += (
            "<div class='hour-card'>"
            f"<h3>{hour}:00</h3>"
            f"<img src='{weather_icon}' class='hour-icon'>"
            f"<p>{data['Temp (°C)'].iloc[i]:.1f}°C</p>"
            "</div>"
        )
    html += "</div>"
    return html

# Build Gradio interface
with gr.Blocks(css=load_css()) as demo:
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

# Launch the app
demo.launch(share=True, debug=True, pwa=True)

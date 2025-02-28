import requests

API_Key = "d5468ece27682dc66b748749ac377e16"
Base_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherApp:
    @staticmethod
    def get_weather(city):
        url = f"{Base_URL}?q={city}&appid={API_Key}&units=metric"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            main = data["main"]
            weather = data['weather'][0]
            wind = data.get("wind", {})

            temp = main['temp']
            feels_like = main['feels_like']
            humidity = main['humidity']
            pressure = main['pressure']
            description = weather['description']
            wind_speed = wind.get("speed", "N/A")

            #Displaying the results
            weather_info = (f"Weather in {city.capitalize()}: \n"
                            f"Temperature:  {temp}°C \n"
                            f"Feels Like:  {feels_like}°C\n"
                            f"Humidity:  {humidity}%\n"
                            f"Condition: {description.capitalize()}\n"
                            f"Wind Speed: {wind_speed} m/s\n"
                            f"Pressure: {pressure} hPa")
            # print(f"\nWeather in {city.capitalize()}: ")
            # print(f"Temperature:  {temp}°C ")
            # print(f"Feels Like:  {feels_like}°C")
            # print(f"Humidity:  {humidity}%")
            # print(f"Condition: {description.capitalize()}")
            # print(f"Wind Speed: {description.capitalize()}")
            # print(f"Pressure: {pressure} hPa")
            return weather_info
        else:
            print("City not found. Please enter a valid city name.")

def main():
    while True:
            # print("Welcome to Weather App!")
        city = input("Enter city name: ")
        if city.lower() != "bye" and city.lower() != "exit":
            result = WeatherApp.get_weather(city=city)
            print(result)
        else:
            exit()


if __name__ == "__main__":
    main()

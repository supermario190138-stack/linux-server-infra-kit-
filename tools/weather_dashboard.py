#!/usr/bin/env python3
"""
🌤️ Weather Dashboard
A comprehensive weather information tool that fetches real-time data from OpenWeatherMap API.
Displays current conditions, forecasts, and alerts in a beautiful formatted dashboard.

API: OpenWeatherMap (https://openweathermap.org/api)
Requires: OPENWEATHER_API_KEY environment variable or config file
"""

import requests
import sys
import os
import json
import argparse
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5"
GEOCODING_API_URL = "https://api.openweathermap.org/geo/1.0"
DEFAULT_UNITS = "metric"  # metric, imperial, standard
UNITS_CONFIG = {
    "metric": {"temp": "°C", "speed": "m/s", "pressure": "hPa"},
    "imperial": {"temp": "°F", "speed": "mph", "pressure": "inHg"},
    "standard": {"temp": "K", "speed": "m/s", "pressure": "hPa"}
}


# ==========================================
# 📊 DATA CLASSES
# ==========================================
@dataclass
class WeatherCondition:
    """Current weather condition data."""
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    main: str
    wind_speed: float
    wind_deg: int
    clouds: int
    visibility: int
    sunrise: int
    sunset: int
    uvi: float


@dataclass
class Forecast:
    """Weather forecast data."""
    dt: int
    temp_min: float
    temp_max: float
    description: str
    main: str
    humidity: int
    wind_speed: float
    precipitation: float


# ==========================================
# 🎯 WEATHER DASHBOARD CLASS
# ==========================================
class WeatherDashboard:
    """Manages weather data fetching and display."""
    
    def __init__(self, api_key: Optional[str] = None, units: str = "metric", timeout: int = 10):
        """
        Initialize Weather Dashboard.
        
        Args:
            api_key (str): OpenWeatherMap API key
            units (str): Temperature units (metric, imperial, standard)
            timeout (int): Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.units = units
        self.timeout = timeout
        self.current_weather = None
        self.forecast_data = None
        self.location_info = None
        
        if not self.api_key:
            raise ValueError("❌ API key required. Set OPENWEATHER_API_KEY env var or pass api_key parameter.")
    
    def get_coordinates(self, city: str, country_code: Optional[str] = None, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get geographic coordinates for a city using Geocoding API.
        
        Args:
            city (str): City name
            country_code (str): Optional ISO 3166 country code
            limit (int): Number of results
            
        Returns:
            Dict with lat/lon or None if not found
        """
        try:
            query = f"{city}"
            if country_code:
                query += f",{country_code}"
            
            url = f"{GEOCODING_API_URL}/direct"
            params = {
                "q": query,
                "limit": limit,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            if not results:
                print(f"❌ City not found: {city}")
                return None
            
            location = results[0]
            self.location_info = {
                "name": location.get("name"),
                "country": location.get("country"),
                "lat": location.get("lat"),
                "lon": location.get("lon"),
                "state": location.get("state")
            }
            
            return self.location_info
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Geocoding error: {str(e)}")
            return None
    
    def fetch_current_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather conditions.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Weather data dict or None
        """
        try:
            url = f"{OPENWEATHER_API_URL}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "units": self.units,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            self.current_weather = response.json()
            return self.current_weather
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Weather fetch error: {str(e)}")
            return None
    
    def fetch_forecast(self, lat: float, lon: float, days: int = 5) -> Optional[Dict[str, Any]]:
        """
        Fetch weather forecast (5-day forecast available with free tier).
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            days (int): Number of forecast days
            
        Returns:
            Forecast data dict or None
        """
        try:
            url = f"{OPENWEATHER_API_URL}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "units": self.units,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            self.forecast_data = response.json()
            return self.forecast_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Forecast fetch error: {str(e)}")
            return None
    
    def get_weather_emoji(self, main: str, description: str = "") -> str:
        """Get appropriate emoji for weather condition."""
        emoji_map = {
            "Clear": "☀️",
            "Clouds": "☁️",
            "Rain": "🌧️",
            "Drizzle": "🌦️",
            "Thunderstorm": "⛈️",
            "Snow": "❄️",
            "Mist": "🌫️",
            "Smoke": "💨",
            "Haze": "🌫️",
            "Dust": "🌪️",
            "Fog": "🌫️",
            "Sand": "🌪️",
            "Ash": "🌋",
            "Squall": "💨",
            "Tornado": "🌪️"
        }
        return emoji_map.get(main, "🌡️")
    
    def get_wind_direction(self, degree: int) -> str:
        """Convert wind degree to cardinal direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = round(degree / 22.5) % 16
        return directions[idx]
    
    def display_current_weather(self) -> None:
        """Display current weather in dashboard format."""
        if not self.current_weather:
            print("❌ No weather data available. Fetch data first.")
            return
        
        data = self.current_weather
        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]
        
        units = UNITS_CONFIG[self.units]
        emoji = self.get_weather_emoji(weather["main"], weather["description"])
        wind_dir = self.get_wind_direction(wind.get("deg", 0))
        
        # Location
        location_str = f"{self.location_info['name']}"
        if self.location_info.get("state"):
            location_str += f", {self.location_info['state']}"
        location_str += f", {self.location_info['country']}"
        
        print("\n" + "="*70)
        print(f"🌍 WEATHER DASHBOARD - {location_str}")
        print("="*70)
        
        # Current conditions
        print(f"\n{emoji} CURRENT CONDITIONS")
        print("-" * 70)
        print(f"Temperature:      {main['temp']:.1f}{units['temp']} (feels like {main['feels_like']:.1f}{units['temp']})")
        print(f"Condition:        {weather['main']} - {weather['description'].title()}")
        print(f"Humidity:         {main['humidity']}%")
        print(f"Pressure:         {main['pressure']} {units['pressure']}")
        print(f"Visibility:       {data.get('visibility', 0) / 1000:.1f} km")
        print(f"Cloud Coverage:   {data.get('clouds', {}).get('all', 0)}%")
        
        # Wind information
        print(f"\n💨 WIND CONDITIONS")
        print("-" * 70)
        print(f"Speed:            {wind['speed']:.1f} {units['speed']}")
        print(f"Direction:        {wind_dir} ({wind.get('deg', 0):.0f}°)")
        if "gust" in wind:
            print(f"Gust Speed:       {wind['gust']:.1f} {units['speed']}")
        
        # Sun information
        print(f"\n☀️  SUN INFORMATION")
        print("-" * 70)
        sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset = datetime.fromtimestamp(data["sys"]["sunset"])
        print(f"Sunrise:          {sunrise.strftime('%H:%M:%S')}")
        print(f"Sunset:           {sunset.strftime('%H:%M:%S')}")
        daylight = sunset - sunrise
        hours = daylight.seconds // 3600
        minutes = (daylight.seconds % 3600) // 60
        print(f"Daylight Hours:   {hours}h {minutes}m")
        
        print("\n" + "="*70 + "\n")
    
    def display_forecast(self, show_hourly: bool = False) -> None:
        """Display weather forecast in table format."""
        if not self.forecast_data:
            print("❌ No forecast data available. Fetch forecast first.")
            return
        
        forecasts = self.forecast_data["list"]
        units = UNITS_CONFIG[self.units]
        
        print("\n" + "="*70)
        print("📅 5-DAY FORECAST")
        print("="*70)
        print(f"{'Date':<12} {'Time':<8} {'Temp':<10} {'Condition':<20} {'Wind':<10} {'Rain%':<8}")
        print("-" * 70)
        
        for forecast in forecasts[::8]:  # Show one forecast per day (every 8 entries = ~24h)
            dt = datetime.fromtimestamp(forecast["dt"])
            temp = forecast["main"]["temp"]
            condition = forecast["weather"][0]["main"]
            wind_speed = forecast["wind"]["speed"]
            rain_chance = forecast.get("pop", 0) * 100
            
            emoji = self.get_weather_emoji(condition)
            
            print(f"{dt.strftime('%Y-%m-%d'):<12} {dt.strftime('%H:%M'):<8} "
                  f"{temp:>6.1f}{units['temp']:<2} {emoji} {condition:<15} "
                  f"{wind_speed:>5.1f}{units['speed']:<3} {rain_chance:>5.0f}%")
        
        print("="*70 + "\n")
    
    def display_hourly_forecast(self, hours: int = 24) -> None:
        """Display hourly forecast."""
        if not self.forecast_data:
            print("❌ No forecast data available.")
            return
        
        forecasts = self.forecast_data["list"][:hours//3]  # 3-hour intervals
        units = UNITS_CONFIG[self.units]
        
        print("\n" + "="*70)
        print(f"⏰ {hours}-HOUR FORECAST")
        print("="*70)
        print(f"{'Time':<12} {'Temp':<10} {'Condition':<20} {'Wind':<12} {'Humidity':<10}")
        print("-" * 70)
        
        for forecast in forecasts:
            dt = datetime.fromtimestamp(forecast["dt"])
            temp = forecast["main"]["temp"]
            condition = forecast["weather"][0]["main"]
            wind = forecast["wind"]["speed"]
            humidity = forecast["main"]["humidity"]
            
            emoji = self.get_weather_emoji(condition)
            
            print(f"{dt.strftime('%H:%M'):<12} {temp:>6.1f}{units['temp']:<2} "
                  f"{emoji} {condition:<15} {wind:>5.1f}{units['speed']:<5} {humidity:>6}%")
        
        print("="*70 + "\n")
    
    def save_to_json(self, filepath: str = "weather_data.json") -> bool:
        """Save current weather data to JSON file."""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "location": self.location_info,
                "current_weather": self.current_weather,
                "forecast": self.forecast_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Weather data saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to save data: {str(e)}")
            return False
    
    def get_weather_alerts(self) -> List[str]:
        """Generate weather alerts based on current conditions."""
        alerts = []
        
        if not self.current_weather:
            return alerts
        
        main = self.current_weather["main"]
        weather = self.current_weather["weather"][0]
        wind = self.current_weather["wind"]
        
        # Temperature alerts
        temp = main["temp"]
        if self.units == "metric" and temp < 0:
            alerts.append("❄️  Freezing temperature - Risk of ice on roads")
        elif self.units == "imperial" and temp < 32:
            alerts.append("❄️  Freezing temperature - Risk of ice on roads")
        
        if self.units == "metric" and temp > 35:
            alerts.append("🔥 High temperature warning - Heat advisory in effect")
        elif self.units == "imperial" and temp > 95:
            alerts.append("🔥 High temperature warning - Heat advisory in effect")
        
        # Weather alerts
        if weather["main"] in ["Thunderstorm", "Tornado"]:
            alerts.append("⚡ Severe weather alert - Take shelter immediately")
        
        if weather["main"] in ["Rain", "Drizzle"]:
            alerts.append("🌧️  Rain warning - Drive with caution")
        
        if weather["main"] in ["Snow"]:
            alerts.append("❄️  Snow warning - Travel may be hazardous")
        
        # Wind alerts
        if wind["speed"] > 10:
            alerts.append("💨 Strong wind warning - Secure loose objects")
        
        # Visibility alerts
        visibility = self.current_weather.get("visibility", 10000)
        if visibility < 1000:
            alerts.append("🌫️  Low visibility - Use headlights and reduce speed")
        
        return alerts


# ==========================================
# 🎛️ CLI INTERFACE
# ==========================================
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🌤️ Weather Dashboard - Real-time weather information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "New York"                   # Get weather for New York
  %(prog)s "London" -u imperial         # Weather in Fahrenheit
  %(prog)s "Tokyo" -f                   # Show 5-day forecast
  %(prog)s "Paris" -H 24                # Show 24-hour forecast
  %(prog)s "Sydney" -a                  # Show weather alerts
  %(prog)s "Berlin" -s weather.json     # Save data to JSON

Note: Requires OPENWEATHER_API_KEY environment variable
Get free API key at: https://openweathermap.org/api
        """
    )
    
    parser.add_argument(
        "city",
        help="City name to get weather for"
    )
    
    parser.add_argument(
        "-k", "--api-key",
        help="OpenWeatherMap API key (or set OPENWEATHER_API_KEY env var)"
    )
    
    parser.add_argument(
        "-u", "--units",
        choices=["metric", "imperial", "standard"],
        default="metric",
        help="Temperature units (default: metric)"
    )
    
    parser.add_argument(
        "-f", "--forecast",
        action="store_true",
        help="Show 5-day forecast"
    )
    
    parser.add_argument(
        "-H", "--hourly",
        type=int,
        metavar="HOURS",
        help="Show hourly forecast (specify hours: 24, 48, etc.)"
    )
    
    parser.add_argument(
        "-a", "--alerts",
        action="store_true",
        help="Show weather alerts"
    )
    
    parser.add_argument(
        "-s", "--save",
        metavar="FILE",
        help="Save weather data to JSON file"
    )
    
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize dashboard
        dashboard = WeatherDashboard(
            api_key=args.api_key,
            units=args.units,
            timeout=args.timeout
        )
        
        # Get coordinates
        print(f"🔍 Searching for: {args.city}...")
        location = dashboard.get_coordinates(args.city)
        if not location:
            sys.exit(1)
        
        print(f"✅ Found: {location['name']}, {location['country']}")
        
        # Fetch current weather
        print("📡 Fetching current weather...")
        dashboard.fetch_current_weather(location["lat"], location["lon"])
        
        # Display current weather
        dashboard.display_current_weather()
        
        # Forecast
        if args.forecast or args.hourly:
            print("📡 Fetching forecast...")
            dashboard.fetch_forecast(location["lat"], location["lon"])
        
        if args.forecast:
            dashboard.display_forecast()
        
        if args.hourly:
            dashboard.display_hourly_forecast(args.hourly)
        
        # Alerts
        if args.alerts:
            alerts = dashboard.get_weather_alerts()
            if alerts:
                print("\n" + "="*70)
                print("⚠️  WEATHER ALERTS")
                print("="*70)
                for alert in alerts:
                    print(f"  {alert}")
                print("="*70 + "\n")
            else:
                print("✅ No active weather alerts\n")
        
        # Save data
        if args.save:
            dashboard.save_to_json(args.save)
    
    except KeyboardInterrupt:
        print("\n\n👋 Exiting weather dashboard...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

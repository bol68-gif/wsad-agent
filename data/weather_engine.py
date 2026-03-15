import requests 
import config 
from datetime import datetime 
 
CITIES = config.BRAND.get("target_cities", [ 
    "Mumbai", "Pune", "Bangalore", "Delhi", "Chennai", "Hyderabad" 
]) 
 
CITY_COORDS = { 
    "Mumbai":    {"lat": 19.0760, "lon": 72.8777}, 
    "Pune":      {"lat": 18.5204, "lon": 73.8567}, 
    "Bangalore": {"lat": 12.9716, "lon": 77.5946}, 
    "Delhi":     {"lat": 28.6139, "lon": 77.2090}, 
    "Chennai":   {"lat": 13.0827, "lon": 80.2707}, 
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867}, 
} 
 
def get_city_weather(city): 
    try: 
        coords = CITY_COORDS.get(city, {}) 
        if not coords:
            return {
                "city": city,
                "condition": "Unknown",
                "rain_mm": 0,
                "intensity": "none",
                "trigger": False,
                "error": "Coordinates not found"
            }
        url = ( 
            f"https://api.openweathermap.org/data/2.5/weather" 
            f"?lat={coords['lat']}&lon={coords['lon']}" 
            f"&appid={config.WEATHER_API_KEY}&units=metric" 
        ) 
        res  = requests.get(url, timeout=10) 
        data = res.json() 
        rain_mm   = data.get("rain", {}).get("1h", 0) 
        condition = data["weather"][0]["description"].title() 
        temp      = data["main"]["temp"] 
        humidity  = data["main"]["humidity"] 
        intensity = get_rain_intensity(rain_mm) 
        return { 
            "city":      city, 
            "condition": condition, 
            "rain_mm":   rain_mm, 
            "temp":      temp, 
            "humidity":  humidity, 
            "intensity": intensity, 
            "timestamp": datetime.utcnow().isoformat(), 
            "trigger":   rain_mm >= config.AGENT.get("rain_threshold_mm", 50) 
        } 
    except Exception as e: 
        return { 
            "city":      city, 
            "condition": "Unknown", 
            "rain_mm":   0, 
            "intensity": "none", 
            "trigger":   False, 
            "error":     str(e) 
        } 
 
def get_all_cities_weather(): 
    return [get_city_weather(city) for city in CITIES] 
 
def get_rain_intensity(mm): 
    if mm == 0:       return "none" 
    elif mm < 10:     return "light" 
    elif mm < 50:     return "moderate" 
    elif mm < 100:    return "heavy" 
    else:             return "extreme" 
 
def check_rain_triggers(): 
    triggered = [] 
    for city_data in get_all_cities_weather(): 
        if city_data.get("trigger"): 
            triggered.append(city_data) 
    return triggered 

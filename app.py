from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import random

load_dotenv()
app = Flask(__name__)

# Flight API (Amadeus Sandbox)
def get_flights(origin, destination, departure_date):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {os.getenv('AMADEUS_API_KEY')}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1,
        "max": 5
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('data', []) if response.status_code == 200 else []
    except:
        return []

# Hotel API (Mock)
def get_hotels(city, checkin, checkout):
    return [
        {
            "name": "Grand Plaza Hotel",
            "price": random.randint(150, 300),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "city": city
        },
        {
            "name": "Seaside Resort",
            "price": random.randint(200, 400),
            "rating": round(random.uniform(4.0, 5.0), 1),
            "city": city
        }
    ]

# Ranking Algorithm
def rank_options(flights, hotels):
    ranked = []
    
    # Score flights
    max_flight_price = max((f['price']['total'] for f in flights), default=1)
    for flight in flights:
        duration_min = int(flight['itineraries'][0]['duration'][2:4])  # PT2H30M → 30
        score = (
            (100 - (flight['price']['total'] / max_flight_price * 100) * 0.4 +
            (100 - duration_min) * 0.3 +
            random.randint(70, 100) * 0.3 ) # Loyalty mock
        )
        ranked.append({
            'type': 'flight',
            'data': flight,
            'score': round(score, 1)
        })
    
    # Score hotels
    for hotel in hotels:
        score = (
            (100 - (hotel['price'] / 500 * 100)) * 0.6 +  # Max $500 assumed
            hotel['rating'] * 20  # 5-star = 100 points
        )
        ranked.append({
            'type': 'hotel',
            'data': hotel,
            'score': round(score, 1)
        })
    
    return sorted(ranked, key=lambda x: x['score'], reverse=True)[:5]

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/travel/recommendations')
def recommendations():
    flights = get_flights(
        request.args.get('from'),
        request.args.get('to'),
        request.args.get('start')
    )
    hotels = get_hotels(
        request.args.get('city', request.args.get('to')),
        request.args.get('checkin', request.args.get('start')),
        request.args.get('checkout', request.args.get('end'))
    )
    return jsonify(rank_options(flights, hotels))

if __name__ == '__main__':
    app.run(port=5001)
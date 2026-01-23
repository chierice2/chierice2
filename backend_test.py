#!/usr/bin/env python3
"""
Backend API Testing Script for Tourist Guide App
Tests all endpoints according to the review request
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://tourhub-9.preview.emergentagent.com/api"

class TouristGuideAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_email = "testuser@example.com"
        self.test_user_password = "testpassword123"
        self.test_user_name = "Test User"
        self.city_ids = []
        self.event_ids = []
        self.place_ids = []
        self.accommodation_ids = []
        self.itinerary_ids = []
        self.favorite_ids = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def make_request(self, method, endpoint, data=None, headers=None, auth_required=False):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        if auth_required and self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed for {method} {url}: {str(e)}", "ERROR")
            return None
            
    def test_seed_data(self):
        """Test seed data endpoint (already working according to test_result.md)"""
        self.log("Testing seed data endpoint...")
        
        response = self.make_request("POST", "/seed")
        if response and response.status_code == 200:
            self.log("✅ Seed data endpoint working")
            return True
        else:
            self.log(f"❌ Seed data failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_authentication(self):
        """Test authentication endpoints"""
        self.log("Testing authentication endpoints...")
        
        # Test registration
        register_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name,
            "preferred_language": "pt"
        }
        
        response = self.make_request("POST", "/auth/register", register_data)
        if response and response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.log("✅ User registration successful")
        else:
            # Try login if user already exists
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.make_request("POST", "/auth/login", login_data)
            if response and response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log("✅ User login successful")
            else:
                self.log(f"❌ Authentication failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
                
        # Test /auth/me endpoint
        response = self.make_request("GET", "/auth/me", auth_required=True)
        if response and response.status_code == 200:
            self.log("✅ /auth/me endpoint working")
            return True
        else:
            self.log(f"❌ /auth/me failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_cities(self):
        """Test cities endpoints"""
        self.log("Testing cities endpoints...")
        
        # Test GET /cities
        response = self.make_request("GET", "/cities")
        if response and response.status_code == 200:
            cities = response.json()
            if cities:
                self.city_ids = [city["_id"] for city in cities]
                self.log(f"✅ GET /cities working - Found {len(cities)} cities")
                
                # Test GET /cities/{id}
                city_id = self.city_ids[0]
                response = self.make_request("GET", f"/cities/{city_id}")
                if response and response.status_code == 200:
                    self.log("✅ GET /cities/{id} working")
                    return True
                else:
                    self.log(f"❌ GET /cities/{{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
            else:
                self.log("❌ No cities found", "ERROR")
                return False
        else:
            self.log(f"❌ GET /cities failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_events(self):
        """Test events endpoints"""
        self.log("Testing events endpoints...")
        
        # Test GET /events
        response = self.make_request("GET", "/events")
        if response and response.status_code == 200:
            events = response.json()
            if events:
                self.event_ids = [event["id"] for event in events]
                self.log(f"✅ GET /events working - Found {len(events)} events")
                
                # Test GET /events with city_id filter
                if self.city_ids:
                    city_id = self.city_ids[0]
                    response = self.make_request("GET", f"/events?city_id={city_id}")
                    if response and response.status_code == 200:
                        filtered_events = response.json()
                        self.log(f"✅ GET /events?city_id={{id}} working - Found {len(filtered_events)} events")
                    else:
                        self.log(f"❌ GET /events?city_id={{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                        return False
                
                # Test GET /events/{event_id}
                event_id = self.event_ids[0]
                response = self.make_request("GET", f"/events/{event_id}")
                if response and response.status_code == 200:
                    self.log("✅ GET /events/{event_id} working")
                    return True
                else:
                    self.log(f"❌ GET /events/{{event_id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
            else:
                self.log("❌ No events found", "ERROR")
                return False
        else:
            self.log(f"❌ GET /events failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_places(self):
        """Test places endpoints"""
        self.log("Testing places endpoints...")
        
        # Test GET /places
        response = self.make_request("GET", "/places")
        if response and response.status_code == 200:
            places = response.json()
            if places:
                self.place_ids = [place["id"] for place in places]
                self.log(f"✅ GET /places working - Found {len(places)} places")
                
                # Test GET /places with city_id filter
                if self.city_ids:
                    city_id = self.city_ids[0]
                    response = self.make_request("GET", f"/places?city_id={city_id}")
                    if response and response.status_code == 200:
                        filtered_places = response.json()
                        self.log(f"✅ GET /places?city_id={{id}} working - Found {len(filtered_places)} places")
                    else:
                        self.log(f"❌ GET /places?city_id={{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                        return False
                
                # Test GET /places with city_id and category filter
                response = self.make_request("GET", f"/places?city_id={city_id}&category=eat")
                if response and response.status_code == 200:
                    eat_places = response.json()
                    self.log(f"✅ GET /places?city_id={{id}}&category=eat working - Found {len(eat_places)} eat places")
                else:
                    self.log(f"❌ GET /places?city_id={{id}}&category=eat failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
                
                # Test GET /places/{place_id}
                place_id = self.place_ids[0]
                response = self.make_request("GET", f"/places/{place_id}")
                if response and response.status_code == 200:
                    self.log("✅ GET /places/{place_id} working")
                    return True
                else:
                    self.log(f"❌ GET /places/{{place_id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
            else:
                self.log("❌ No places found", "ERROR")
                return False
        else:
            self.log(f"❌ GET /places failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_accommodations(self):
        """Test accommodations endpoints"""
        self.log("Testing accommodations endpoints...")
        
        # Test GET /accommodations
        response = self.make_request("GET", "/accommodations")
        if response and response.status_code == 200:
            accommodations = response.json()
            if accommodations:
                self.accommodation_ids = [acc["id"] for acc in accommodations]
                self.log(f"✅ GET /accommodations working - Found {len(accommodations)} accommodations")
                
                # Test GET /accommodations with city_id filter
                if self.city_ids:
                    city_id = self.city_ids[0]
                    response = self.make_request("GET", f"/accommodations?city_id={city_id}")
                    if response and response.status_code == 200:
                        filtered_accommodations = response.json()
                        self.log(f"✅ GET /accommodations?city_id={{id}} working - Found {len(filtered_accommodations)} accommodations")
                    else:
                        self.log(f"❌ GET /accommodations?city_id={{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                        return False
                
                # Test GET /accommodations/{accommodation_id}
                accommodation_id = self.accommodation_ids[0]
                response = self.make_request("GET", f"/accommodations/{accommodation_id}")
                if response and response.status_code == 200:
                    self.log("✅ GET /accommodations/{accommodation_id} working")
                    return True
                else:
                    self.log(f"❌ GET /accommodations/{{accommodation_id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
            else:
                self.log("❌ No accommodations found", "ERROR")
                return False
        else:
            self.log(f"❌ GET /accommodations failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_itineraries(self):
        """Test itineraries endpoints"""
        self.log("Testing itineraries endpoints...")
        
        # Test GET /itineraries
        response = self.make_request("GET", "/itineraries")
        if response and response.status_code == 200:
            itineraries = response.json()
            if itineraries:
                self.itinerary_ids = [itin["id"] for itin in itineraries]
                self.log(f"✅ GET /itineraries working - Found {len(itineraries)} itineraries")
                
                # Test GET /itineraries with city_id filter
                if self.city_ids:
                    city_id = self.city_ids[0]
                    response = self.make_request("GET", f"/itineraries?city_id={city_id}")
                    if response and response.status_code == 200:
                        filtered_itineraries = response.json()
                        self.log(f"✅ GET /itineraries?city_id={{id}} working - Found {len(filtered_itineraries)} itineraries")
                    else:
                        self.log(f"❌ GET /itineraries?city_id={{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                        return False
                
                # Test GET /itineraries with city_id and type filter
                response = self.make_request("GET", f"/itineraries?city_id={city_id}&type=aventureiro")
                if response and response.status_code == 200:
                    adventure_itineraries = response.json()
                    self.log(f"✅ GET /itineraries?city_id={{id}}&type=aventureiro working - Found {len(adventure_itineraries)} adventure itineraries")
                else:
                    self.log(f"❌ GET /itineraries?city_id={{id}}&type=aventureiro failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
                
                # Test GET /itineraries/{itinerary_id}
                itinerary_id = self.itinerary_ids[0]
                response = self.make_request("GET", f"/itineraries/{itinerary_id}")
                if response and response.status_code == 200:
                    self.log("✅ GET /itineraries/{itinerary_id} working")
                    return True
                else:
                    self.log(f"❌ GET /itineraries/{{itinerary_id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                    return False
            else:
                self.log("❌ No itineraries found", "ERROR")
                return False
        else:
            self.log(f"❌ GET /itineraries failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_favorites(self):
        """Test favorites endpoints (requires authentication)"""
        self.log("Testing favorites endpoints...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for favorites testing", "ERROR")
            return False
            
        # Test POST /favorites (add favorite)
        if self.event_ids:
            favorite_data = {
                "item_type": "event",
                "item_id": self.event_ids[0]
            }
            
            response = self.make_request("POST", "/favorites", favorite_data, auth_required=True)
            if response and response.status_code == 200:
                favorite = response.json()
                self.favorite_ids.append(favorite["id"])
                self.log("✅ POST /favorites working - Added event to favorites")
            else:
                self.log(f"❌ POST /favorites failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
                
        # Add another favorite (place)
        if self.place_ids:
            favorite_data = {
                "item_type": "place",
                "item_id": self.place_ids[0]
            }
            
            response = self.make_request("POST", "/favorites", favorite_data, auth_required=True)
            if response and response.status_code == 200:
                favorite = response.json()
                self.favorite_ids.append(favorite["id"])
                self.log("✅ POST /favorites working - Added place to favorites")
            else:
                self.log(f"❌ POST /favorites (place) failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
                
        # Test GET /favorites
        response = self.make_request("GET", "/favorites", auth_required=True)
        if response and response.status_code == 200:
            favorites = response.json()
            self.log(f"✅ GET /favorites working - Found {len(favorites)} favorites")
        else:
            self.log(f"❌ GET /favorites failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
        # Test DELETE /favorites/{favorite_id}
        if self.favorite_ids:
            favorite_id = self.favorite_ids[0]
            response = self.make_request("DELETE", f"/favorites/{favorite_id}", auth_required=True)
            if response and response.status_code == 200:
                self.log("✅ DELETE /favorites/{favorite_id} working")
            else:
                self.log(f"❌ DELETE /favorites/{{favorite_id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
                
        # Test DELETE /favorites/by-item/{type}/{id}
        if self.place_ids:
            response = self.make_request("DELETE", f"/favorites/by-item/place/{self.place_ids[0]}", auth_required=True)
            if response and response.status_code == 200:
                self.log("✅ DELETE /favorites/by-item/{type}/{id} working")
                return True
            else:
                self.log(f"❌ DELETE /favorites/by-item/{{type}}/{{id}} failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
                
        return True
        
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("Starting Tourist Guide Backend API Tests...")
        self.log(f"Testing against: {self.base_url}")
        
        results = {}
        
        # Test seed data first to ensure we have data
        results["seed_data"] = self.test_seed_data()
        
        # Test authentication
        results["authentication"] = self.test_authentication()
        
        # Test cities (already working according to test_result.md)
        results["cities"] = self.test_cities()
        
        # Test events
        results["events"] = self.test_events()
        
        # Test places
        results["places"] = self.test_places()
        
        # Test accommodations
        results["accommodations"] = self.test_accommodations()
        
        # Test itineraries
        results["itineraries"] = self.test_itineraries()
        
        # Test favorites (requires authentication)
        results["favorites"] = self.test_favorites()
        
        # Summary
        self.log("\n" + "="*50)
        self.log("TEST RESULTS SUMMARY")
        self.log("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        return results

if __name__ == "__main__":
    tester = TouristGuideAPITester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)
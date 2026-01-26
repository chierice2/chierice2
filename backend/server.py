from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Models ====================

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    preferred_language: str = "pt"
    travel_style: Optional[str] = None  # chill, cultural, party, nature, foodie


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: str = Field(alias="_id")
    email: str
    name: str
    preferred_language: str
    created_at: datetime

    class Config:
        populate_by_name = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class CityBase(BaseModel):
    name: str
    slug: str
    description_pt: str
    description_en: str
    image_base64: Optional[str] = None


class City(CityBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class ExternalLinks(BaseModel):
    google_maps: Optional[str] = None
    instagram: Optional[str] = None
    website: Optional[str] = None
    airbnb: Optional[str] = None


class EventBase(BaseModel):
    city_id: str
    name_pt: str
    name_en: str
    description_pt: str
    description_en: str
    category: str
    tags: List[str] = []
    image_base64: Optional[str] = None
    external_links: ExternalLinks = ExternalLinks()


class Event(EventBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class PlaceBase(BaseModel):
    city_id: str
    name: str
    description_pt: str
    description_en: str
    category: str  # eat, drink, activity
    tags: List[str] = []
    image_base64: Optional[str] = None
    external_links: ExternalLinks = ExternalLinks()


class Place(PlaceBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class AccommodationBase(BaseModel):
    city_id: str
    name: str
    description_pt: str
    description_en: str
    tags: List[str] = []
    image_base64: Optional[str] = None
    external_links: ExternalLinks = ExternalLinks()


class Accommodation(AccommodationBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class ItineraryItem(BaseModel):
    name: str
    description: str
    type: str  # event, place, accommodation


class ItineraryBase(BaseModel):
    city_id: str
    name_pt: str
    name_en: str
    type: str  # aventureiro, cultural, chilling
    description_pt: str
    description_en: str
    items: List[ItineraryItem] = []
    image_base64: Optional[str] = None


class Itinerary(ItineraryBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class FavoriteCreate(BaseModel):
    item_type: str  # event, place, accommodation, itinerary
    item_id: str


class Favorite(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    item_type: str
    item_id: str
    created_at: datetime

    class Config:
        populate_by_name = True


# ==================== Auth Helper Functions ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return User(**user)


# ==================== Auth Routes ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "name": user_data.name,
        "preferred_language": user_data.preferred_language,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_dict["_id"]})
    
    user_response = User(
        _id=user_dict["_id"],
        email=user_dict["email"],
        name=user_dict["name"],
        preferred_language=user_dict["preferred_language"],
        created_at=user_dict["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_response)


@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    user_response = User(
        _id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        preferred_language=user["preferred_language"],
        created_at=user["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_response)


@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ==================== Cities Routes ====================

@api_router.get("/cities", response_model=List[City])
async def get_cities():
    cities = await db.cities.find().to_list(100)
    return [City(_id=str(city["_id"]), **{k: v for k, v in city.items() if k != "_id"}) for city in cities]


@api_router.get("/cities/{city_id}", response_model=City)
async def get_city(city_id: str):
    city = await db.cities.find_one({"_id": ObjectId(city_id)})
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return City(_id=str(city["_id"]), **{k: v for k, v in city.items() if k != "_id"})


# ==================== Events Routes ====================

@api_router.get("/events", response_model=List[Event])
async def get_events(city_id: Optional[str] = None):
    query = {"city_id": city_id} if city_id else {}
    events = await db.events.find(query).to_list(100)
    return [Event(_id=str(event["_id"]), **{k: v for k, v in event.items() if k != "_id"}) for event in events]


@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    event = await db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return Event(_id=str(event["_id"]), **{k: v for k, v in event.items() if k != "_id"})


# ==================== Places Routes ====================

@api_router.get("/places", response_model=List[Place])
async def get_places(city_id: Optional[str] = None, category: Optional[str] = None):
    query = {}
    if city_id:
        query["city_id"] = city_id
    if category:
        query["category"] = category
    
    places = await db.places.find(query).to_list(100)
    return [Place(_id=str(place["_id"]), **{k: v for k, v in place.items() if k != "_id"}) for place in places]


@api_router.get("/places/{place_id}", response_model=Place)
async def get_place(place_id: str):
    place = await db.places.find_one({"_id": ObjectId(place_id)})
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return Place(_id=str(place["_id"]), **{k: v for k, v in place.items() if k != "_id"})


# ==================== Accommodations Routes ====================

@api_router.get("/accommodations", response_model=List[Accommodation])
async def get_accommodations(city_id: Optional[str] = None):
    query = {"city_id": city_id} if city_id else {}
    accommodations = await db.accommodations.find(query).to_list(100)
    return [Accommodation(_id=str(acc["_id"]), **{k: v for k, v in acc.items() if k != "_id"}) for acc in accommodations]


@api_router.get("/accommodations/{accommodation_id}", response_model=Accommodation)
async def get_accommodation(accommodation_id: str):
    accommodation = await db.accommodations.find_one({"_id": ObjectId(accommodation_id)})
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return Accommodation(_id=str(accommodation["_id"]), **{k: v for k, v in accommodation.items() if k != "_id"})


# ==================== Itineraries Routes ====================

@api_router.get("/itineraries", response_model=List[Itinerary])
async def get_itineraries(city_id: Optional[str] = None, type: Optional[str] = None):
    query = {}
    if city_id:
        query["city_id"] = city_id
    if type:
        query["type"] = type
    
    itineraries = await db.itineraries.find(query).to_list(100)
    return [Itinerary(_id=str(itin["_id"]), **{k: v for k, v in itin.items() if k != "_id"}) for itin in itineraries]


@api_router.get("/itineraries/{itinerary_id}", response_model=Itinerary)
async def get_itinerary(itinerary_id: str):
    itinerary = await db.itineraries.find_one({"_id": ObjectId(itinerary_id)})
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return Itinerary(_id=str(itinerary["_id"]), **{k: v for k, v in itinerary.items() if k != "_id"})


# ==================== Favorites Routes ====================

@api_router.post("/favorites", response_model=Favorite)
async def create_favorite(favorite_data: FavoriteCreate, current_user: User = Depends(get_current_user)):
    # Check if already favorited
    existing = await db.favorites.find_one({
        "user_id": current_user.id,
        "item_type": favorite_data.item_type,
        "item_id": favorite_data.item_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")
    
    favorite_dict = {
        "user_id": current_user.id,
        "item_type": favorite_data.item_type,
        "item_id": favorite_data.item_id,
        "created_at": datetime.utcnow()
    }
    
    result = await db.favorites.insert_one(favorite_dict)
    favorite_dict["_id"] = str(result.inserted_id)
    
    return Favorite(**favorite_dict)


@api_router.get("/favorites", response_model=List[Favorite])
async def get_favorites(current_user: User = Depends(get_current_user)):
    favorites = await db.favorites.find({"user_id": current_user.id}).to_list(1000)
    return [Favorite(_id=str(fav["_id"]), **{k: v for k, v in fav.items() if k != "_id"}) for fav in favorites]


@api_router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: str, current_user: User = Depends(get_current_user)):
    result = await db.favorites.delete_one({
        "_id": ObjectId(favorite_id),
        "user_id": current_user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Favorite deleted"}


@api_router.delete("/favorites/by-item/{item_type}/{item_id}")
async def delete_favorite_by_item(item_type: str, item_id: str, current_user: User = Depends(get_current_user)):
    result = await db.favorites.delete_one({
        "user_id": current_user.id,
        "item_type": item_type,
        "item_id": item_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Favorite deleted"}


# ==================== Seed Data Route ====================

@api_router.post("/seed")
async def seed_data():
    """Seed database with sample data"""
    
    # Clear existing data
    await db.cities.delete_many({})
    await db.events.delete_many({})
    await db.places.delete_many({})
    await db.accommodations.delete_many({})
    await db.itineraries.delete_many({})
    
    # Insert cities
    cities = [
        {
            "name": "São Paulo",
            "slug": "sao-paulo",
            "description_pt": "A maior metrópole da América Latina, vibrante e cosmopolita",
            "description_en": "Latin America's largest metropolis, vibrant and cosmopolitan",
            "image_base64": None
        },
        {
            "name": "Rio de Janeiro",
            "slug": "rio-de-janeiro",
            "description_pt": "Cidade maravilhosa com praias icônicas e natureza exuberante",
            "description_en": "Marvelous city with iconic beaches and lush nature",
            "image_base64": None
        },
        {
            "name": "Salvador",
            "slug": "salvador",
            "description_pt": "Capital da cultura afro-brasileira com história rica",
            "description_en": "Capital of Afro-Brazilian culture with rich history",
            "image_base64": None
        },
        {
            "name": "Florianópolis",
            "slug": "florianopolis",
            "description_pt": "Ilha mágica com 42 praias paradisíacas",
            "description_en": "Magic island with 42 paradisiacal beaches",
            "image_base64": None
        }
    ]
    
    city_results = await db.cities.insert_many(cities)
    city_ids = [str(id) for id in city_results.inserted_ids]
    
    # Sample events for São Paulo
    events_sp = [
        {
            "city_id": city_ids[0],
            "name_pt": "Festival de Jazz no Parque",
            "name_en": "Jazz Festival in the Park",
            "description_pt": "Festival anual de jazz ao ar livre com artistas locais e internacionais",
            "description_en": "Annual outdoor jazz festival with local and international artists",
            "category": "music",
            "tags": ["local favorite", "music", "outdoor"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Ibirapuera+Park+São+Paulo",
                "instagram": "https://instagram.com/explore/tags/jazzsp",
                "website": None,
                "airbnb": None
            }
        },
        {
            "city_id": city_ids[0],
            "name_pt": "Feira de Arte da Paulista",
            "name_en": "Paulista Art Fair",
            "description_pt": "Feira de arte e artesanato aos domingos na Avenida Paulista",
            "description_en": "Art and craft fair on Sundays at Paulista Avenue",
            "category": "art",
            "tags": ["hidden gem", "art", "local favorite"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Avenida+Paulista+São+Paulo",
                "instagram": "https://instagram.com/explore/tags/feirapaulista",
                "website": None,
                "airbnb": None
            }
        }
    ]
    
    await db.events.insert_many(events_sp)
    
    # Sample places for São Paulo
    places_sp = [
        {
            "city_id": city_ids[0],
            "name": "Bar do Arnesto",
            "description_pt": "Boteco tradicional paulistano com petiscos autênticos e chopp gelado",
            "description_en": "Traditional São Paulo bar with authentic snacks and cold draft beer",
            "category": "drink",
            "tags": ["local favorite", "authentic", "hidden gem"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Bar+do+Arnesto+São+Paulo",
                "instagram": "https://instagram.com/bardoarnesto",
                "website": None,
                "airbnb": None
            }
        },
        {
            "city_id": city_ids[0],
            "name": "Mocotó",
            "description_pt": "Restaurante nordestino famoso pela comida regional de alto nível",
            "description_en": "Northeastern restaurant famous for high-end regional cuisine",
            "category": "eat",
            "tags": ["local favorite", "traditional", "must-visit"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Mocotó+São+Paulo",
                "instagram": "https://instagram.com/restaurantemocoto",
                "website": "https://www.mocoto.com.br",
                "airbnb": None
            }
        },
        {
            "city_id": city_ids[0],
            "name": "Beco do Batman",
            "description_pt": "Galeria de arte de rua a céu aberto no bairro da Vila Madalena",
            "description_en": "Open-air street art gallery in Vila Madalena neighborhood",
            "category": "activity",
            "tags": ["instagram-worthy", "art", "tourist-friendly"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Beco+do+Batman+São+Paulo",
                "instagram": "https://instagram.com/explore/tags/becodobatman",
                "website": None,
                "airbnb": None
            }
        }
    ]
    
    await db.places.insert_many(places_sp)
    
    # Sample accommodations
    accommodations_sp = [
        {
            "city_id": city_ids[0],
            "name": "Airbnb Loft Vila Madalena",
            "description_pt": "Loft charmoso no coração da Vila Madalena, perto de bares e galerias",
            "description_en": "Charming loft in the heart of Vila Madalena, close to bars and galleries",
            "tags": ["local experience", "central", "trendy"],
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Vila+Madalena+São+Paulo",
                "instagram": None,
                "website": None,
                "airbnb": "https://www.airbnb.com/s/Vila-Madalena--São-Paulo"
            }
        }
    ]
    
    await db.accommodations.insert_many(accommodations_sp)
    
    # Sample itineraries
    itineraries_sp = [
        {
            "city_id": city_ids[0],
            "name_pt": "SP Aventureiro",
            "name_en": "SP Adventurer",
            "type": "aventureiro",
            "description_pt": "Explore o lado radical de São Paulo: escalada urbana, bike tours e parques",
            "description_en": "Explore São Paulo's radical side: urban climbing, bike tours and parks",
            "items": [
                {"name": "Parque Ibirapuera", "description": "Cicloturismo no maior parque da cidade", "type": "activity"},
                {"name": "Escalada no CEU", "description": "Parede de escalada urbana", "type": "activity"},
                {"name": "Mercado Municipal", "description": "Explore a gastronomia local", "type": "place"}
            ],
            "image_base64": None
        },
        {
            "city_id": city_ids[0],
            "name_pt": "SP Cultural",
            "name_en": "SP Cultural",
            "type": "cultural",
            "description_pt": "Mergulhe na cena cultural: museus, teatros e arte de rua",
            "description_en": "Dive into the cultural scene: museums, theaters and street art",
            "items": [
                {"name": "MASP", "description": "Museu de Arte de São Paulo", "type": "activity"},
                {"name": "Beco do Batman", "description": "Arte de rua na Vila Madalena", "type": "activity"},
                {"name": "Theatro Municipal", "description": "Arquitetura histórica", "type": "activity"}
            ],
            "image_base64": None
        },
        {
            "city_id": city_ids[0],
            "name_pt": "SP Chilling",
            "name_en": "SP Chilling",
            "type": "chilling",
            "description_pt": "Relaxe em cafés charmosos, parques tranquilos e bares descontraídos",
            "description_en": "Relax in charming cafes, peaceful parks and laid-back bars",
            "items": [
                {"name": "Café Floresta", "description": "Café aconchegante com wifi", "type": "place"},
                {"name": "Parque Buenos Aires", "description": "Parque tranquilo para relaxar", "type": "activity"},
                {"name": "Bar do Arnesto", "description": "Boteco tradicional", "type": "place"}
            ],
            "image_base64": None
        }
    ]
    
    await db.itineraries.insert_many(itineraries_sp)
    
    return {"message": "Database seeded successfully", "cities_created": len(city_ids)}


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

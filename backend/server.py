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
app = FastAPI(title="Premium Local Guide API")
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
    travel_style: Optional[str] = None
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
    country: str
    description_pt: str
    description_en: str
    vibe_pt: str  # "Cosmopolita e vibrante"
    vibe_en: str  # "Cosmopolitan and vibrant"
    lifestyle_pt: str  # Description of local lifestyle
    lifestyle_en: str
    best_times: str  # "Mar-Mai, Set-Nov"
    image_base64: Optional[str] = None


class City(CityBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class NeighborhoodBase(BaseModel):
    city_id: str
    name: str
    slug: str
    personality_pt: str  # "Boêmio e artístico"
    personality_en: str  # "Bohemian and artistic"
    description_pt: str
    description_en: str


class Neighborhood(NeighborhoodBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class ExternalLinks(BaseModel):
    google_maps: Optional[str] = None
    instagram: Optional[str] = None
    website: Optional[str] = None


class ExperienceBase(BaseModel):
    city_id: str
    neighborhood_id: Optional[str] = None
    title_pt: str
    title_en: str
    story_pt: str  # Storytelling description
    story_en: str
    categories: List[str] = []  # food, culture, nature, nightlife, walking, hidden_gems
    vibes: List[str] = []  # chill, romantic, local, artistic, vibrant, calm
    best_time: str  # "Manhã" / "Morning", "Final de tarde" / "Late afternoon"
    price_range: str  # $ / $$ / $$$
    local_tip_pt: str  # Informal, human tone
    local_tip_en: str
    image_base64: Optional[str] = None
    external_links: ExternalLinks = ExternalLinks()


class Experience(ExperienceBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class FavoriteCreate(BaseModel):
    item_type: str  # experience
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
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "name": user_data.name,
        "preferred_language": user_data.preferred_language,
        "travel_style": user_data.travel_style,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    access_token = create_access_token(data={"sub": user_dict["_id"]})
    
    user_response = User(
        _id=user_dict["_id"],
        email=user_dict["email"],
        name=user_dict["name"],
        preferred_language=user_dict["preferred_language"],
        travel_style=user_dict.get("travel_style"),
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
        travel_style=user.get("travel_style"),
        created_at=user["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_response)


@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@api_router.patch("/auth/me")
async def update_me(travel_style: Optional[str] = None, current_user: User = Depends(get_current_user)):
    update_data = {}
    if travel_style:
        update_data["travel_style"] = travel_style
    
    if update_data:
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
    
    return {"message": "Profile updated"}


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


# ==================== Neighborhoods Routes ====================

@api_router.get("/neighborhoods", response_model=List[Neighborhood])
async def get_neighborhoods(city_id: Optional[str] = None):
    query = {"city_id": city_id} if city_id else {}
    neighborhoods = await db.neighborhoods.find(query).to_list(100)
    return [Neighborhood(_id=str(n["_id"]), **{k: v for k, v in n.items() if k != "_id"}) for n in neighborhoods]


@api_router.get("/neighborhoods/{neighborhood_id}", response_model=Neighborhood)
async def get_neighborhood(neighborhood_id: str):
    neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(neighborhood_id)})
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    return Neighborhood(_id=str(neighborhood["_id"]), **{k: v for k, v in neighborhood.items() if k != "_id"})


# ==================== Experiences Routes ====================

@api_router.get("/experiences", response_model=List[Experience])
async def get_experiences(
    city_id: Optional[str] = None,
    neighborhood_id: Optional[str] = None,
    category: Optional[str] = None,
    vibe: Optional[str] = None,
    price_range: Optional[str] = None
):
    query = {}
    if city_id:
        query["city_id"] = city_id
    if neighborhood_id:
        query["neighborhood_id"] = neighborhood_id
    if category:
        query["categories"] = category
    if vibe:
        query["vibes"] = vibe
    if price_range:
        query["price_range"] = price_range
    
    experiences = await db.experiences.find(query).to_list(200)
    return [Experience(_id=str(exp["_id"]), **{k: v for k, v in exp.items() if k != "_id"}) for exp in experiences]


@api_router.get("/experiences/{experience_id}", response_model=Experience)
async def get_experience(experience_id: str):
    experience = await db.experiences.find_one({"_id": ObjectId(experience_id)})
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return Experience(_id=str(experience["_id"]), **{k: v for k, v in experience.items() if k != "_id"})


# ==================== Favorites Routes ====================

@api_router.post("/favorites", response_model=Favorite)
async def create_favorite(favorite_data: FavoriteCreate, current_user: User = Depends(get_current_user)):
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


# ==================== Seed Premium Data Route ====================

@api_router.post("/seed-premium")
async def seed_premium_data():
    """Seed database with premium curated experiences"""
    
    # Clear existing data
    await db.cities.delete_many({})
    await db.neighborhoods.delete_many({})
    await db.experiences.delete_many({})
    
    # ===== SÃO PAULO =====
    sp_city = {
        "name": "São Paulo",
        "slug": "sao-paulo",
        "country": "Brazil",
        "description_pt": "A maior metrópole da América Latina",
        "description_en": "Latin America's largest metropolis",
        "vibe_pt": "Cosmopolita, vibrante e cultural",
        "vibe_en": "Cosmopolitan, vibrant and cultural",
        "lifestyle_pt": "Paulistanos vivem intensamente: trabalham muito, mas sabem aproveitar. A cidade nunca para, há sempre algo novo acontecendo.",
        "lifestyle_en": "Paulistanos live intensely: they work hard but know how to enjoy life. The city never stops, there's always something new happening.",
        "best_times": "Mar-Mai, Set-Nov",
        "image_base64": None
    }
    sp_result = await db.cities.insert_one(sp_city)
    sp_id = str(sp_result.inserted_id)
    
    # SP Neighborhoods
    vila_madalena = {
        "city_id": sp_id,
        "name": "Vila Madalena",
        "slug": "vila-madalena",
        "personality_pt": "Boêmio, artístico e descolado",
        "personality_en": "Bohemian, artistic and cool",
        "description_pt": "O coração cultural alternativo de SP, com galerias de arte de rua, bares charmosos e uma vibe jovem e criativa.",
        "description_en": "SP's alternative cultural heart, with street art galleries, charming bars and a young, creative vibe."
    }
    vm_result = await db.neighborhoods.insert_one(vila_madalena)
    vm_id = str(vm_result.inserted_id)
    
    pinheiros = {
        "city_id": sp_id,
        "name": "Pinheiros",
        "slug": "pinheiros",
        "personality_pt": "Gastronômico e vibrante",
        "personality_en": "Gastronomic and vibrant",
        "description_pt": "Reduto gastronômico paulistano, onde chefs inovam e a vida noturna ferve.",
        "description_en": "São Paulo's gastronomic stronghold, where chefs innovate and nightlife thrives."
    }
    pin_result = await db.neighborhoods.insert_one(pinheiros)
    pin_id = str(pin_result.inserted_id)
    
    # SP Premium Experiences
    experiences_sp = [
        {
            "city_id": sp_id,
            "neighborhood_id": vm_id,
            "title_pt": "Café da manhã no Estadão",
            "title_en": "Breakfast at Estadão",
            "story_pt": "Um ritual paulistano: o pão francês quentinho às 6h da manhã. Aqui você entende porque o paulistano acorda cedo. A padaria abre 24h e vive cheia de moradores do bairro.",
            "story_en": "A São Paulo ritual: warm french bread at 6am. Here you understand why paulistanos wake up early. The bakery opens 24/7 and is always full of locals.",
            "categories": ["food", "local"],
            "vibes": ["local", "authentic", "calm"],
            "best_time": "Manhã cedo (6h-9h) / Early morning (6am-9am)",
            "price_range": "$",
            "local_tip_pt": "Peça o pão na chapa com manteiga. É simples, mas é São Paulo no seu melhor.",
            "local_tip_en": "Order the 'pão na chapa' with butter. It's simple, but it's São Paulo at its best.",
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Padaria+Estadão+Vila+Madalena",
                "instagram": "https://instagram.com/explore/tags/padariaestadao",
                "website": None
            }
        },
        {
            "city_id": sp_id,
            "neighborhood_id": vm_id,
            "title_pt": "Arte de rua no Beco do Batman",
            "title_en": "Street art at Beco do Batman",
            "story_pt": "Não é só pra foto. É um museu vivo onde a arte muda a cada semana. Artistas locais e internacionais deixam suas marcas nessas paredes. Melhor ir num final de tarde, quando a luz fica perfeita.",
            "story_en": "It's not just for photos. It's a living museum where art changes every week. Local and international artists leave their marks on these walls. Best to go in the late afternoon when the light is perfect.",
            "categories": ["culture", "walking", "hidden_gems"],
            "vibes": ["artistic", "vibrant", "local"],
            "best_time": "Final de tarde / Late afternoon",
            "price_range": "$",
            "local_tip_pt": "Depois, tome uma cerveja no Bar do Ló, bem ao lado. Os locais estão sempre lá.",
            "local_tip_en": "Afterwards, grab a beer at Bar do Ló, right next door. The locals are always there.",
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Beco+do+Batman+São+Paulo",
                "instagram": "https://instagram.com/explore/tags/becodobatman",
                "website": None
            }
        },
        {
            "city_id": sp_id,
            "neighborhood_id": pin_id,
            "title_pt": "Jantar no Bar da Dona Onça",
            "title_en": "Dinner at Bar da Dona Onça",
            "story_pt": "A chef Helena Rizzo reimagina a comida brasileira com técnica e afeto. O ambiente lembra a casa da avó, mas com drinks sofisticados e pratos que contam histórias.",
            "story_en": "Chef Helena Rizzo reimagines Brazilian food with technique and affection. The atmosphere reminds you of grandma's house, but with sophisticated drinks and dishes that tell stories.",
            "categories": ["food", "nightlife"],
            "vibes": ["romantic", "vibrant", "local"],
            "best_time": "Jantar (19h-22h) / Dinner (7pm-10pm)",
            "price_range": "$$$",
            "local_tip_pt": "Reserve com antecedência. E peça a barriga de porco - é imperdível.",
            "local_tip_en": "Book in advance. And order the pork belly - it's unmissable.",
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Bar+da+Dona+Onça+São+Paulo",
                "instagram": "https://instagram.com/bardonaonca",
                "website": "https://www.bardonaonca.com.br"
            }
        },
        {
            "city_id": sp_id,
            "neighborhood_id": None,
            "title_pt": "Caminhar no Parque Ibirapuera ao amanhecer",
            "title_en": "Walk in Ibirapuera Park at sunrise",
            "story_pt": "O pulmão verde de São Paulo ganha vida antes do caos urbano começar. Corredores, ciclistas e yogues dividem espaço em harmonia. É quando a cidade respira.",
            "story_en": "São Paulo's green lung comes alive before urban chaos begins. Runners, cyclists and yogis share space in harmony. It's when the city breathes.",
            "categories": ["nature", "walking"],
            "vibes": ["calm", "local"],
            "best_time": "Amanhecer (6h-8h) / Sunrise (6am-8am)",
            "price_range": "$",
            "local_tip_pt": "Leve um mate gelado e sente perto do lago. Observe os paulistanos no seu momento zen.",
            "local_tip_en": "Bring a cold mate and sit by the lake. Watch paulistanos in their zen moment.",
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Parque+Ibirapuera+São+Paulo",
                "instagram": "https://instagram.com/explore/tags/parqueibirapuera",
                "website": None
            }
        },
        {
            "city_id": sp_id,
            "neighborhood_id": vm_id,
            "title_pt": "Cerveja artesanal no Cervejaria Nacional",
            "title_en": "Craft beer at Cervejaria Nacional",
            "story_pt": "Não é só mais uma cervejaria. É onde cervejeiros experimentam receitas doidas e o público é convidado a provar. O clima é de boteco refinado - todo mundo se conhece.",
            "story_en": "It's not just another brewery. It's where brewers experiment with crazy recipes and the public is invited to taste. The atmosphere is refined pub style - everyone knows each other.",
            "categories": ["nightlife", "local"],
            "vibes": ["chill", "local", "vibrant"],
            "best_time": "Fim de tarde / Late afternoon",
            "price_range": "$$",
            "local_tip_pt": "Vai às quintas-feiras quando tem música ao vivo. E prova a IPA da casa.",
            "local_tip_en": "Go on Thursdays when there's live music. And try the house IPA.",
            "image_base64": None,
            "external_links": {
                "google_maps": "https://maps.google.com/?q=Cervejaria+Nacional+Vila+Madalena",
                "instagram": "https://instagram.com/cervejarianacional",
                "website": None
            }
        }
    ]
    
    await db.experiences.insert_many(experiences_sp)
    
    return {
        "message": "Premium data seeded successfully",
        "cities": 1,
        "neighborhoods": 2,
        "experiences": len(experiences_sp)
    }


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

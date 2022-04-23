from config import (
    api_key,
    api_secret,
    FAUNA_KEY
)
import cloudinary
from faunadb.client import FaunaClient


# configure cloudinary
cloudinary.config(
    cloud_name="curiouspaul",
    api_key=api_key,
    api_secret=api_secret
)

# fauna client config
client = FaunaClient(secret=FAUNA_KEY)

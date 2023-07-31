from datetime import datetime
from typing import Optional

from bson.objectid import ObjectId
from pymongo.database import Database

from ..utils.security import hash_password


class AuthRepository:
    def __init__(self, database: Database):
        self.database = database

    #USER========================================
    def create_user(self, user: dict):
        payload = {
            "email": user["email"],
            "password": hash_password(user["password"]),
            "created_at": datetime.utcnow(),
            'favorites' : list(),
        }

        self.database["users"].insert_one(payload)

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        user = self.database["users"].find_one(
            {
                "_id": ObjectId(user_id),
            }
        )
        return user

    def get_user_by_email(self, email: str) -> Optional[dict]:
        user = self.database["users"].find_one(
            {
                "email": email,
            }
        )
        return user

    def update_user(self, user_id: str, data: dict):
        self.database["users"].update_one(
            filter={"_id": ObjectId(user_id)},
            update={
                "$set": {
                    "phone": data["phone"],
                    "name": data["name"],
                    "city": data["city"],
                }
            },
        )
    
    #FAVORITES===========================================
    def add_shanyrak_to_favorites(self, shanyrak_id : str, user_id : str):
        favorites = self.get_favorites_by_user_id(user_id)
        
        if shanyrak_id not in favorites:
            favorites.append(shanyrak_id)

        return self.database['users'].update_one(
            filter={'_id' : ObjectId(user_id)},
            update={'$set' : {'favorites' : favorites}}
        )

    def get_favorites_by_user_id(self, user_id : str):
        user = self.database['users'].find_one({'_id' : ObjectId(user_id)})
        return user['favorites'] if 'favorites' in user else []
    
    def get_shanyraks_by_ids(self, user_id : str) -> list:
        shanyraks_ids =  self.get_favorites_by_user_id(user_id)
        shanyraks_id = [ObjectId(id) for id in shanyraks_ids]

        shanyraks =  self.database['shanyraks'].find({'_id' : {'$in' : shanyraks_id}})

        return [shanyrak for shanyrak in shanyraks]

    def delete_favorite_shanyrak_by_id(self, user_id, shanyrak_id):
        favorites = self.get_favorites_by_user_id(user_id)

        if shanyrak_id in favorites:
            favorites.remove(shanyrak_id)
        
        update = self.database['users'].update_one(
            filter={'_id' : ObjectId(user_id)},
            update={'$set' : {'favorites' : favorites}}
            )

        return update
    

    #AVATAR====================================
    def upload_avatar(self, user_id : str, avatar):
        upload = self.database["users"].update_one(
            filter={"_id": ObjectId(user_id)},
            update={"$set": {'avatar_url' : avatar}},
        )
    
        return upload
    
    def get_avatar_url(self, user_id : str):
        return self.database['users'].find_one({'_id' : ObjectId(user_id)})['avatar_url']

    def delete_avatar(self, user_id : str):
        return self.database["users"].update_one(
            filter={"_id": ObjectId(user_id)},
            update={"$set": {'avatar_url' : ''}},
        )
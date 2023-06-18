from datetime import datetime
from typing import List, Optional, Any

from bson.objectid import ObjectId
from fastapi import HTTPException
from pymongo.database import Database

from ..utils.security import hash_password
from pymongo.results import DeleteResult, UpdateResult

class AuthRepository:
    def __init__(self, database: Database):
        self.database = database

    def create_shanyrak(self, user_id, info: dict):
        info['user_id'] = ObjectId(user_id)
        return self.database['shanyraks'].insert_one(info)

    def get_shanyrak_by_id(self, shanyrak_id: str) -> Optional[dict]:
        shanyrak = self.database["shanyraks"].find_one(
            {
                "_id": ObjectId(shanyrak_id),
            }
        )
        return shanyrak

    def update_shanyrak(self, shanyrak_id: str, user_id: str, data: dict[str, Any]) -> UpdateResult:
        return self.database["shanyraks"].update_one(
            filter={"_id": ObjectId(shanyrak_id), "user_id": ObjectId(user_id)},
            update={
                "$set": data,
            },
        )
    
    def delete_shanyrak(self, shanyrak_id, user_id):
        return self.database['shanyraks'].delete_one(
            filter={'_id' : ObjectId(shanyrak_id), 'user_id' : ObjectId(user_id)},
        )
    
    def upload_files(self, shanyrak_id : str, user_id : str, files):
        upload = self.database["shanyraks"].update_one(
            filter={"_id": ObjectId(shanyrak_id), "user_id": ObjectId(user_id)},
            update={"$push": {'media' : files}},
        )
    
        return upload

    def delete_files(self, shanyrak_id : str, user_id : str):

        return self.database["shanyraks"].update_one(
            filter={"_id": ObjectId(shanyrak_id), "user_id": ObjectId(user_id)},
            update={"$set": {'media' : []}},
        )

    def get_shanyraks_by_filter(self, latitude, longitude, radius, limit, offset, type, rooms_count, price_from, price_until):
        if price_until == 0:
            price_until = float('infinity')

        types = [type]
        if type == '':
            types = ['rent', 'sale']
        
        rad = radius / 111.12

        if rooms_count == 0:
            cursor = self.database['shanyraks'].find(
                {
                    'price' : {'$gte' : price_from, '$lte' : price_until},
                    'type' : {'$in' : types},
                    'location' : {
                        '$geoWithin' : {
                            '$center': [[latitude, longitude], rad]
                        },
                    }
                },
            ).limit(limit).skip(offset).sort('created_at', -1)
        else:
            cursor = self.database['shanyraks'].find(
                {
                    'price' : {'$gte' : price_from, '$lte' : price_until},
                    'type' : {'$in' : types},
                    'rooms_count' : rooms_count,
                    'location' : {
                        '$geoWithin' : {
                            '$center': [[latitude, longitude], rad]
                        },
                    }
                },
            ).limit(limit).skip(offset).sort('created_at', -1)

        result = []
        for item in cursor:
            result.append(item)

        return {
            'total' : len(result),
            'objects' : result
        }
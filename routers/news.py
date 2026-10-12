from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_database
from crud import news_cache

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100 , db : AsyncSession = Depends(get_database)):
    cate = await news_cache.get_categories(db , skip , limit)
    return {
        "code" : 200,
        "message" : "ok",
        "data" : cate
    }

@router.get("/list")
async def get_news_list(
        category_id: int = Query(...,alias="categoryId"),
        page: int = 1 ,
        page_size: int = Query(10 ,alias="pageSize",le = 100),
        db : AsyncSession = Depends(get_database)
):
    offset = (page-1) * page_size
    news_list = await news_cache.get_news_list(db , category_id , offset , page_size)
    total = await news_cache.get_news_count(db , category_id)
    hasmore = (offset+len(news_list))<total
    return {
        "code" : 200,
        "message" : "ok",
        "data":{
            "list" : news_list,
            "total" : total,
            "hasMore": hasmore
        }
    }

@router.get("/detail")
async def get_news_detail(
        news_id : int = Query(...,alias="id"),
        db : AsyncSession = Depends(get_database)
):
    news_detail = await news_cache.get_news_detail(db , news_id)
    if not news_detail:#查不到的话报错
        raise HTTPException(status_code=404 , detail="新闻不存在")

    views_res = await news_cache.increase_news_views(db , news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404 , detail= "新闻不存在")

    related_news = await news_cache.get_related_news(db , news_detail.id , news_detail.category_id)
    return {
      "code": 200,
      "message": "success",
      "data": {
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
        "relatedNews": related_news
      }
    }
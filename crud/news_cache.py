from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    get_cached_news_detail, cache_news_detail, get_cached_related_news, cache_related_news
from models.news import Category, News
from schemas.base import NewsItemBase
from schemas.news import RelatedNewsResponse, NewsDetailResponse


async def get_categories(db : AsyncSession, skip: int = 0, limit: int = 100) :
    #先从缓存中查    有直接返回    没有就写入缓存
    cached_categories =  await get_cached_categories()
    if cached_categories:
        return cached_categories

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()  #orm

    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    return categories

async def get_news_list(db : AsyncSession, category_id, skip: int = 0, limit: int = 100) :
    # 查询指定分类下的所有新闻
    page =  skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)  #JSON
    if cached_list:
        #return cached_list  #要的是ORM
        return [News(**item) for item in cached_list]

    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()
    #写入缓存
    if news_list:
        # news_list = jsonable_encoder(news_list) #先把ORM转化为 字典类型
        #另一种方法  先ORM->Pydantic --> 字典
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list


async def get_news_count(db : AsyncSession, category_id) :
    #查询指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  #只能有一个结果

async def get_news_detail(db : AsyncSession, news_id : int) :
    # 先尝试从缓存获取
    cached_news = await get_cached_news_detail(news_id)
    if cached_news:
        # 缓存数据可能包含 related_news，需要过滤掉（News 模型没有这个字段）
        # filtered_data = {k: v for k, v in cached_news.items() if k != 'related_news'}
        # return News(**filtered_data)
        return News(**cached_news)

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    # 如果查询到数据，存入缓存（不使用别名，保持数据库字段名）
    if news:
        # 构造新闻详情数据用于缓存（包含 content 字段）
        # news_dict = {k: v for k, v in news.__dict__.items() if not k.startswith('_')}
        news_dict = NewsDetailResponse.model_validate(news).model_dump(
            by_alias=False, mode="json", exclude={'related_news'}
        )
        await cache_news_detail(news_id, news_dict)

    return news

async def increase_news_views(db : AsyncSession, news_id : int) :
    temet = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(temet)
    await db.commit()
    return result.rowcount > 0

async def get_related_news(db : AsyncSession, news_id : int , category_id : int , limit: int = 5) :
    cached_related = await get_cached_related_news(news_id, category_id)
    if cached_related:
        # 缓存数据是字典列表，直接返回
        return cached_related
    # order_by 排序 → 浏览量和发布时间
    stmt = select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),  # 默认是升序，desc 表示降序
        News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()

    # 转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        related_data = [
            RelatedNewsResponse.model_validate(news).model_dump(by_alias=False, mode="json")
            for news in related_news
        ]
        await cache_related_news(news_id, category_id, related_data)
        return related_data

    # 没有相关新闻，返回空列表
    return []
    # 列表推导式 推导出新闻的核心数据，然后再 return
    # return [{
    #     "id": news_detail.id,
    #     "title": news_detail.title,
    #     "content": news_detail.content,
    #     "image": news_detail.image,
    #     "author": news_detail.author,
    #     "publishTime": news_detail.publish_time,
    #     "categoryId": news_detail.category_id,
    #     "views": news_detail.views
    # } for news_detail in related_news]


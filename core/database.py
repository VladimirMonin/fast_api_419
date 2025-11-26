# core/database.py
import logging
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings
from typing import AsyncGenerator, Optional

# Импортируем модели для регистрации в Base.metadata
from models.base import Base  # Импортируем Base из пакета models
from models.product import Product as ProductORM, Category as CategoryORM, Tag as TagORM
from schemas.product import (
    CategoryCreate,
    Category,
    TagCreate,
    Tag,
    ProductCreate,
    ProductUpdate,
    Product,
)

logger = logging.getLogger(__name__)

# URL для подключения к асинхронной SQLite
DATABASE_URL = settings.DATABASE_URL

logger.info(f"📊 Инициализация подключения к БД: {DATABASE_URL}")

# Cоздание асинхронного движка базы данных
#  echo=True — включает логирование SQL-запросов в консоль
engine = create_async_engine(DATABASE_URL, echo=True)
logger.info("✅ Асинхронный движок базы данных создан")

# Создание фабрики асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    # bind - это движок, с которым будут работать сессии
    # expire_on_commit=False - отключает автоматическое обновление объектов после коммита
    # если его не отключить, то после каждого коммита надо будет повторно загружать объекты из базы
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,  # Используем асинхронную сессию
)

logger.info("✅ Фабрика асинхронных сессий создана")

# AsyncSession - тип для аннотаций

# Все синхронные запросы в бд станут асинхронными
"""
- `session.execute(stmt)` -> `await session.execute(stmt)`
- `session.get(Model, id)` -> `await session.get(Model, id)`
- `session.scalars(stmt).all()` -> `(await session.execute(stmt)).scalars().all()`
- `session.flush()` -> `await session.flush()`
- `session.refresh(obj)` -> `await session.refresh(obj)`
- `session.delete(obj)` -> `await session.delete(obj)`
- __Важно:__ `session.add(obj)` и `session.add_all([..])` __не требуют__ `await`, так как они просто регистрируют объекты в сессии, не делая I/O запроса."""


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция-зависимость FastAPI для получения асинхронной сессии базы данных.

    Каждый запрос будет получать свою сессию, которая будет автоматически закрыта
    после завершения запроса (или при возникновении ошибки).

    Когда fastAPI видит что зависимость является асинхронным генератором, активирует механизм. Код до yield выполняется при входе в зависимость, а код после yield - при выходе из зависимости.
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("🔌 Открыта новая сессия БД")
            yield session
            await session.commit()
            logger.debug("✅ Сессия БД закоммичена и закрыта")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Ошибка в сессии БД, выполнен rollback: {e}")
            raise


######################## Create операции ########################


async def tag_create(session: AsyncSession, tag_data: TagCreate) -> Tag:
    """
    Создание нового тега.

    :param session: Асинхронная сессия SQLAlchemy
    :param tag_data: Данные для создания тега
    :return: Tag с id и name тега
    """
    logger.info(f"📝 Попытка создания тега: {tag_data.name}")

    # Проверка на уникальность имени
    existing = await session.scalar(select(TagORM).where(TagORM.name == tag_data.name))

    if existing:
        logger.warning(
            f"⚠️ Тег '{tag_data.name}' уже существует, возвращаем существующий"
        )
        return Tag.model_validate(existing)

    # Создаём новый тег
    new_tag = TagORM(name=tag_data.name)

    session.add(new_tag)
    await session.flush()
    await session.refresh(new_tag)

    result = Tag.model_validate(new_tag)
    logger.info(f"✅ Тег создан: ID={result.id}, Name={result.name}")
    return result


async def category_create(
    session: AsyncSession, category_data: CategoryCreate
) -> Category:
    """
    Создание новой категории.

    :param session: Асинхронная сессия SQLAlchemy
    :param category_data: Данные для создания категории
    :return: Category с id и name категории
    """
    logger.info(f"📝 Попытка создания категории: {category_data.name}")

    # Проверка на уникальность имени
    existing = await session.scalar(
        select(CategoryORM).where(CategoryORM.name == category_data.name)
    )

    if existing:
        logger.warning(
            f"⚠️ Категория '{category_data.name}' уже существует, возвращаем существующую"
        )
        return Category.model_validate(existing)

    # Создаём новую категорию
    new_category = CategoryORM(name=category_data.name)

    session.add(new_category)
    await session.flush()
    await session.refresh(new_category)

    result = Category.model_validate(new_category)
    logger.info(f"✅ Категория создана: ID={result.id}, Name={result.name}")
    return result


async def product_create(session: AsyncSession, product_data: ProductCreate) -> Product:
    """
    Создание нового продукта.

    :param session: Асинхронная сессия SQLAlchemy
    :param product_data: Данные для создания продукта
    :return: Product с id, name, description, category и tags продукта
    """
    logger.info(f"📝 Попытка создания продукта: {product_data.name}")

    # Базовый продукт без связей
    product_dict = product_data.model_dump(exclude={"category_id", "tag_ids"})
    new_product = ProductORM(**product_dict)

    # Связываем категорию, если указана
    if product_data.category_id is not None:
        category = await session.get(CategoryORM, product_data.category_id)
        if category:
            new_product.category = category
            logger.debug(
                f"🔗 Продукт связан с категорией ID={product_data.category_id}"
            )
        else:
            logger.error(f"❌ Категория с ID={product_data.category_id} не найдена")
            raise ValueError(f"Категория с ID={product_data.category_id} не найдена")

    # Связываем теги, если указаны
    if product_data.tag_ids:
        # Загружаем все теги одним запросом
        tags_stmt = select(TagORM).where(TagORM.id.in_(product_data.tag_ids))
        # ASK - А в чем разница между синх и асинх вариантом? У меня раньше было tags_stmt = select(TagORM).where(TagORM.id.in_(product_data.tag_ids)) tags_orm = session.execute(tags_stmt).scalars().all()
        tags_orm = await session.scalars(tags_stmt)
        tags_list = tags_orm.all()

        # Проверяем, что все теги найдены
        found_ids = {tag.id for tag in tags_list}
        missing_ids = set(product_data.tag_ids) - found_ids

        if missing_ids:
            logger.error(f"❌ Теги с ID={missing_ids} не найдены")
            raise ValueError(f"Теги с ID={missing_ids} не найдены")

        # Связываем теги с продуктом
        new_product.tags = list(tags_list)
        logger.debug(f"🔗 Продукт связан с тегами: {[tag.name for tag in tags_list]}")

    # Сохраняем продукт в базе
    session.add(new_product)
    await session.flush()

    # Мы не обойдемся refresh - так как он отрабатывает ТОЛЬКО одну таблицу. Нам нужна явная загрузка связей
    stmt = (
        select(ProductORM)
        .where(ProductORM.id == new_product.id)
        .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
    )

    # Выполняем запрос и получаем один полностью загруженный объект
    refreshed_product_with_relations = await session.scalar(stmt)

    # Валидируем и пакуем в Pydantic модель
    result = Product.model_validate(refreshed_product_with_relations)
    logger.info(f"✅ Продукт создан: ID={result.id}, Name={result.name}")
    return result


######################## Delete операции ########################


async def category_delete(session: AsyncSession, category_id: int) -> None:
    """
    Удаление категории по ID.

    :param session: Асинхронная сессия SQLAlchemy
    :param category_id: ID категории для удаления
    """
    logger.info(f"🗑️ Попытка удаления категории ID={category_id}")

    category = await session.get(CategoryORM, category_id)
    if not category:
        logger.error(f"❌ Категория с ID={category_id} не найдена")
        raise ValueError(f"Категория с ID={category_id} не найдена")

    await session.delete(category)
    logger.info(f"✅ Категория с ID={category_id} удалена")


async def tag_delete(session: AsyncSession, tag_id: int) -> None:
    """
    Удаление тега по ID.

    :param session: Асинхронная сессия SQLAlchemy
    :param tag_id: ID тега для удаления
    """
    logger.info(f"🗑️ Попытка удаления тега ID={tag_id}")

    tag = await session.get(TagORM, tag_id)
    if not tag:
        logger.error(f"❌ Тег с ID={tag_id} не найден")
        raise ValueError(f"Тег с ID={tag_id} не найден")

    await session.delete(tag)
    logger.info(f"✅ Тег с ID={tag_id} удалён")


async def product_delete(session: AsyncSession, product_id: int) -> None:
    """
    Удаление продукта по ID.

    :param session: Асинхронная сессия SQLAlchemy
    :param product_id: ID продукта для удаления
    """
    logger.info(f"🗑️ Попытка удаления продукта ID={product_id}")

    product = await session.get(ProductORM, product_id)
    if not product:
        logger.error(f"❌ Продукт с ID={product_id} не найден")
        raise ValueError(f"Продукт с ID={product_id} не найден")

    await session.delete(product)
    logger.info(f"✅ Продукт с ID={product_id} удалён")


######################## Read операции ########################
# Категория, тег, продукт по ID
# Все категории, теги, продукты
# Продукт like name


async def category_get_by_id(session: AsyncSession, category_id: int) -> Category:
    """
    Получение категории по ID.
    :param session: Асинхронная сессия SQLAlchemy
    :param category_id: ID категории для получения
    :return: Category с id и name категории
    """
    category = await session.get(CategoryORM, category_id)
    if not category:
        raise ValueError(f"Категория с ID={category_id} не найдена")
    return Category.model_validate(category)


async def tag_get_by_id(session: AsyncSession, tag_id: int) -> Tag:
    """
    Получение тега по ID.
    :param session: Асинхронная сессия SQLAlchemy
    :param tag_id: ID тега для получения
    :return: Tag с id и name тега
    """
    tag = await session.get(TagORM, tag_id)
    if not tag:
        raise ValueError(f"Тег с ID={tag_id} не найден")
    return Tag.model_validate(tag)


async def product_get_by_id(session: AsyncSession, product_id: int) -> Product:
    """
    Получение продукта по ID.
    :param session: Асинхронная сессия SQLAlchemy
    :param product_id: ID продукта для получения
    :return: Product с id, name, description, category и tags продукта
    """
    stmt = (
        select(ProductORM)
        .where(ProductORM.id == product_id)
        .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
    )
    product = await session.scalar(stmt)
    if not product:
        raise ValueError(f"Продукт с ID={product_id} не найден")
    return Product.model_validate(product)


async def categories_get_all(session: AsyncSession) -> list[Category]:
    """
    Получение всех категорий.
    :param session: Асинхронная сессия SQLAlchemy
    :return: Список всех категорий
    """
    stmt = select(CategoryORM)
    categories = await session.scalars(stmt)
    return [Category.model_validate(cat) for cat in categories]


async def category_has_products(session: AsyncSession, category_id: int) -> bool:
    """
    Проверка наличия продуктов, связанных с категорией.
    :param session: Асинхронная сессия SQLAlchemy
    :param category_id: ID категории для проверки
    :return: True если есть связанные продукты, False если нет
    """
    stmt = select(ProductORM).where(ProductORM.category_id == category_id).limit(1)
    result = await session.scalar(stmt)
    return result is not None


async def tags_get_all(session: AsyncSession) -> list[Tag]:
    """
    Получение всех тегов.
    :param session: Асинхронная сессия SQLAlchemy
    :return: Список всех тегов
    """
    stmt = select(TagORM)
    tags = await session.scalars(stmt)
    return [Tag.model_validate(tag) for tag in tags]


async def products_get_all(session: AsyncSession) -> list[Product]:
    """
    Получение всех продуктов и связанных данных.
    :param session: Асинхронная сессия SQLAlchemy
    :return: Список всех продуктов с категориями и тегами
    """
    stmt = select(ProductORM).options(
        selectinload(ProductORM.category), selectinload(ProductORM.tags)
    )
    products = await session.scalars(stmt)
    return [Product.model_validate(prod) for prod in products]


async def products_get_like_name(
    session: AsyncSession, name_substring: str
) -> list[Product]:
    """
    Расширенный поиск продуктов по названию, категории или тегам.
    :param session: Асинхронная сессия SQLAlchemy
    :param name_substring: Подстрока для поиска вхождения в имя продукта или в имя категории/тега
    """
    stmt = (
        select(ProductORM)
        .outerjoin(ProductORM.category)
        .outerjoin(ProductORM.tags)
        .where(
            or_(
                ProductORM.name.ilike(f"%{name_substring}%"),
                CategoryORM.name.ilike(f"%{name_substring}%"),
                TagORM.name.ilike(f"%{name_substring}%"),
            )
        )
        # Важно явно использовать options для загрузки связей
        # Потому что join \ outerjoin - для where, а options - для загрузки связей
    ).options(selectinload(ProductORM.category), selectinload(ProductORM.tags))

    products = await session.scalars(stmt)
    return [Product.model_validate(prod) for prod in products]


async def products_get_with_filters(
    session: AsyncSession,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    has_image: bool = False,
) -> list[Product]:
    """
    Получение продуктов с фильтрацией и сортировкой.

    :param session: Асинхронная сессия SQLAlchemy
    :param search: Поиск по названию, категории или тегам
    :param sort: Сортировка по цене в формате "currency_direction" (например, "shmeckles_asc", "flurbos_desc")
    :param has_image: Если True, возвращаются только товары с изображениями
    :return: Список продуктов с примененными фильтрами и сортировкой
    """
    # Базовый запрос с загрузкой связей
    stmt = select(ProductORM).options(
        selectinload(ProductORM.category), selectinload(ProductORM.tags)
    )

    # Применяем поиск, если указан
    if search:
        stmt = (
            stmt.outerjoin(ProductORM.category)
            .outerjoin(ProductORM.tags)
            .where(
                or_(
                    ProductORM.name.ilike(f"%{search}%"),
                    CategoryORM.name.ilike(f"%{search}%"),
                    TagORM.name.ilike(f"%{search}%"),
                )
            )
            .distinct()  # Убираем дубликаты из-за M2M связи с tags
        )

    # Выполняем запрос
    products_result = await session.scalars(stmt)
    products = [Product.model_validate(prod) for prod in products_result]

    # Применяем фильтр по изображениям
    if has_image:
        products = [product for product in products if product.image_url]

    # Применяем сортировку, если указана
    if sort:
        try:
            currency, direction = sort.split("_")
            reverse = direction == "desc"

            if currency == "shmeckles":
                products.sort(
                    key=lambda item: item.price_shmeckles
                    if item.price_shmeckles is not None
                    else float("inf"),
                    reverse=reverse,
                )
            elif currency == "flurbos":
                products.sort(
                    key=lambda item: item.price_flurbos
                    if item.price_flurbos is not None
                    else float("inf"),
                    reverse=reverse,
                )
            else:
                raise ValueError(
                    "Неверная валюта для сортировки. Используйте 'shmeckles' или 'flurbos'."
                )
        except ValueError as e:
            raise ValueError(f"Неверный формат параметра sort: {e}")

    return products


######################## Update операции ########################


async def category_update(session: AsyncSession, category_data: Category) -> Category:
    """
    Обновление категории по ID.
    :param session: Асинхронная сессия SQLAlchemy
    :param category_id: ID категории для обновления
    :param category_data: Данные для обновления категории
    :return: Обновлённая категория
    """
    category = await session.get(CategoryORM, category_data.id)
    if not category:
        raise ValueError(f"Категория с ID={category_data.id} не найдена")

    for field, value in category_data.model_dump().items():
        setattr(category, field, value)

    return Category.model_validate(category)


async def tag_update(session: AsyncSession, tag_data: Tag) -> Tag:
    """
    Обновление тега по ID.
    :param session: Асинхронная сессия SQLAlchemy
    :param tag_id: ID тега для обновления
    :param tag_data: Данные для обновления тега
    :return: Обновлённый тег
    """
    tag = await session.get(TagORM, tag_data.id)
    if not tag:
        raise ValueError(f"Тег с ID={tag_data.id} не найден")

    for field, value in tag_data.model_dump().items():
        setattr(tag, field, value)

    return Tag.model_validate(tag)


async def product_update(session: AsyncSession, product_data: ProductUpdate) -> Product:
    """
    Обновление продукта по ID включая связи.
    :param session: Асинхронная сессия SQLAlchemy
    :param product_data: Данные для обновления продукта
    :return: Обновлённый продукт
    """
    # Получаем существующий продукт
    product = await session.get(ProductORM, product_data.id)
    if not product:
        raise ValueError(f"Продукт с ID={product_data.id} не найден")

    # Обновляем поля продукта через распаковку DTO
    product_dict = product_data.model_dump(exclude={"category_id", "tag_ids"})
    for key, value in product_dict.items():
        setattr(product, key, value)

    # Обновляем категорию, если указана
    if product_data.category_id is not None:
        category = await session.get(CategoryORM, product_data.category_id)
        if category:
            product.category = category
        else:
            raise ValueError(f"Категория с ID={product_data.category_id} не найдена")

    else:
        # Если category_id не указан, отвязываем категорию
        product.category = None

    # Обновляем теги, если указаны
    if product_data.tag_ids is not None:
        # Загружаем все теги одним запросом
        tags_stmt = select(TagORM).where(TagORM.id.in_(product_data.tag_ids))
        tags_orm = await session.scalars(tags_stmt)
        tags_list = tags_orm.all()

        # Проверяем, что все теги найдены
        found_ids = {tag.id for tag in tags_list}
        missing_ids = set(product_data.tag_ids) - found_ids

        if missing_ids:
            raise ValueError(f"Теги с ID={missing_ids} не найдены")

        # Связываем теги с продуктом
        product.tags = list(tags_list)
    else:
        # Если передан пустой список, отвязываем все теги
        product.tags = []

    # Сохраняем без закрытия сессии
    await session.flush()

    # Загружаем обновлённый продукт с связями жадной загрузкой
    stmt = (
        select(ProductORM)
        .where(ProductORM.id == product.id)
        .options(selectinload(ProductORM.category), selectinload(ProductORM.tags))
    )

    result = await session.scalars(stmt)
    updated_product = result.one()
    return Product.model_validate(updated_product)

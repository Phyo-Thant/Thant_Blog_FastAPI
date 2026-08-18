from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate

from pathlib import Path
import uuid
import shutil
from fastapi import File, Form, UploadFile

router = APIRouter()


@app.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
    )
    posts = result.scalars().all()
    return posts


UPLOAD_DIR = Path("static/post_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    title: Annotated[str, Form(min_length=1, max_length=100)],
    content: Annotated[str, Form(min_length=1)],
    user_id: Annotated[int, Form()],
    image: Annotated[UploadFile | None, File()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_filename = None
    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        image_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = UPLOAD_DIR / image_filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    new_post = models.Post(
        title=title,
        content=content,
        user_id=user_id,
        image_file=image_filename,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])  # Ensure author relationship is loaded
    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


def _save_post_image(image: UploadFile) -> str:
    ext = Path(image.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return filename


def _delete_post_image(filename: str | None) -> None:
    if filename:
        old_path = UPLOAD_DIR / filename
        if old_path.exists():
            old_path.unlink()


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int,
    title: Annotated[str, Form(min_length=1, max_length=100)],
    content: Annotated[str, Form(min_length=1)],
    user_id: Annotated[int, Form()],
    image: Annotated[UploadFile | None, File()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if user_id != post.user_id:
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="User not found")

    post.title = title
    post.content = content
    post.user_id = user_id

    if image and image.filename:
        _delete_post_image(post.image_file)
        post.image_file = _save_post_image(image)

    await db.commit()
    await db.refresh(post)
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    title: Annotated[str | None, Form(min_length=1, max_length=100)] = None,
    content: Annotated[str | None, Form(min_length=1)] = None,
    image: Annotated[UploadFile | None, File()] = None,
    clear_image: Annotated[bool, Form()] = False,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content

    if clear_image:
        _delete_post_image(post.image_file)
        post.image_file = None
    elif image and image.filename:
        _delete_post_image(post.image_file)
        post.image_file = _save_post_image(image)

    await db.commit()
    await db.refresh(post)
    return post


router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # Optional: also delete the image file
    _delete_post_image(post.image_file)

    await db.delete(post)
    await db.commit()

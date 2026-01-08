from fastapi import APIRouter, Depends, status, HTTPException
from models import Blogs, Users
from schemas import BlogCreate, BlogUpdateRequest
from database import db_dependency
from security import get_current_user

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("/all_blogs", status_code=status.HTTP_200_OK)
def get_all_blogs(db: db_dependency, current_user: Users = Depends(get_current_user)):
    blogs = db.query(Blogs).filter(Blogs.author_id == current_user.id).order_by(Blogs.created_date.desc()).all()

    return [
        {
            "id": b.id,
            "title": b.title,
            "description": b.description,
            "created_date": b.created_date,
            "edit_date": b.edit_date,
            "author_id": b.author_id,
        }
        for b in blogs
    ]


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_blog_post(create_data: BlogCreate, db: db_dependency,current_user: Users = Depends(get_current_user)):
    title = (create_data.title or "").strip()
    description = (create_data.description or "").strip()

    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    if not description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    exist_blog = db.query(Blogs).filter(Blogs.author_id == current_user.id, Blogs.title == title).first()

    if exist_blog:
        raise HTTPException(status_code=400, detail="This blog title exists")

    new_blog = Blogs(
        title=title,
        description=description,
        author_id=current_user.id,
    )

    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return {
        "message": "Blog created",
        "blog": {
            "id": new_blog.id,
            "title": new_blog.title,
            "description": new_blog.description,
            "author_id": new_blog.author_id,
            "created_date": new_blog.created_date,
            "edit_date": new_blog.edit_date,
        },
    }


@router.patch("/edit/{blog_id}", status_code=status.HTTP_200_OK)
def update_blog(blog_id: int, payload: BlogUpdateRequest,db: db_dependency, current_user: Users = Depends(get_current_user)):

    blog = db.query(Blogs).filter(Blogs.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit this blog",
        )

    if payload.title is None and payload.description is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    if payload.title is not None:
        new_title = payload.title.strip()
        if not new_title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        exists = db.query(Blogs).filter(Blogs.author_id == current_user.id, Blogs.title == new_title, Blogs.id != blog_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="This blog title exists")

        blog.title = new_title

    if payload.description is not None:
        new_desc = payload.description.strip()
        if not new_desc:
            raise HTTPException(status_code=400, detail="Description cannot be empty")
        blog.description = new_desc

    db.commit()
    db.refresh(blog)

    return {
        "message": "Blog updated successfully",
        "blog": {
            "id": blog.id,
            "title": blog.title,
            "description": blog.description,
            "author_id": blog.author_id,
            "created_date": blog.created_date,
            "edit_date": blog.edit_date,
        },
    }

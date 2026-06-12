"""分类标签接口"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.infrastructure.database import get_db
from src.models.user import User
from src.models.permissions import Category, Tag, DocumentCategory, DocumentTag
from src.api.deps import get_current_user

router = APIRouter(prefix="/kbs/{kb_id}", tags=["分类标签"])


# === Categories ===

@router.get("/categories")
async def list_categories(kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.kb_id == kb_id))
    cats = result.scalars().all()
    tree = _build_tree(cats)
    return tree


@router.post("/categories")
async def create_category(kb_id: str, name: str, parent_id: str | None = None,
                           user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cat = Category(kb_id=kb_id, name=name, parent_id=parent_id)
    db.add(cat)
    await db.commit()
    return {"id": cat.id, "name": cat.name, "parent_id": cat.parent_id}


@router.delete("/categories/{cat_id}")
async def delete_category(kb_id: str, cat_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Category).where(Category.id == cat_id, Category.kb_id == kb_id))
    await db.commit()
    return {"ok": True}


# === Tags ===

@router.get("/tags")
async def list_tags(kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.kb_id == kb_id))
    return [{"id": t.id, "name": t.name} for t in result.scalars().all()]


@router.post("/tags")
async def create_tag(kb_id: str, name: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tag = Tag(kb_id=kb_id, name=name)
    db.add(tag)
    await db.commit()
    return {"id": tag.id, "name": tag.name}


@router.delete("/tags/{tag_id}")
async def delete_tag(kb_id: str, tag_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Tag).where(Tag.id == tag_id, Tag.kb_id == kb_id))
    await db.commit()
    return {"ok": True}


# === Document-Category & Document-Tag ===

@router.post("/documents/{doc_id}/categories")
async def set_doc_categories(kb_id: str, doc_id: str, category_ids: list[str],
                              user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(DocumentCategory).where(DocumentCategory.document_id == doc_id))
    for cid in category_ids:
        db.add(DocumentCategory(document_id=doc_id, category_id=cid))
    await db.commit()
    return {"ok": True}


@router.post("/documents/{doc_id}/tags")
async def set_doc_tags(kb_id: str, doc_id: str, tag_ids: list[str],
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(DocumentTag).where(DocumentTag.document_id == doc_id))
    for tid in tag_ids:
        db.add(DocumentTag(document_id=doc_id, tag_id=tid))
    await db.commit()
    return {"ok": True}


def _build_tree(cats: list[Category]) -> list[dict]:
    cat_map = {c.id: {"id": c.id, "name": c.name, "children": []} for c in cats}
    roots = []
    for c in cats:
        if c.parent_id and c.parent_id in cat_map:
            cat_map[c.parent_id]["children"].append(cat_map[c.id])
        else:
            roots.append(cat_map[c.id])
    return roots

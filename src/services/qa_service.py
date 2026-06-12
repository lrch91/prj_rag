"""Q&A 服务：混合检索 + LLM 生成 + 引用溯源 + 多轮对话 + 流式"""

import json, re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from src.retrieval.hybrid_retriever import hybrid_search
from src.llm_gateway.base import LLMRequest
from src.llm_gateway.registry import registry
from src.models.conversation import Conversation, Message, MessageCitation
from src.config import settings
from src.models.document import Document, DocumentChunk
from src.models.knowledge_base import KnowledgeBase


async def ask_question(
    question: str,
    kb_ids: list[str],
    model_name: str,
    conversation_id: str | None,
    user_id: str,
    db: AsyncSession,
    stream: bool = False,
) -> dict:
    # 1. 获取或创建对话
    conv = None
    history: list[dict] = []
    if conversation_id:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = result.scalar_one_or_none()
        if conv and conv.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        if conv:
            # 加载最近 10 轮历史
            msg_result = await db.execute(
                select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).limit(20)
            )
            history = [{"role": m.role, "content": m.content} for m in reversed(msg_result.scalars().all())]

    if conv is None:
        conv = Conversation(user_id=user_id, kb_id=kb_ids[0] if kb_ids else None, model_name=model_name)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # 2. Query Rewriter（有历史时改写为独立查询）
    standalone_question = question
    if history:
        standalone_question = await _rewrite_query(question, history, model_name)

    # 3. 查询缓存（跳过检索的加速）
    cached = None
    if not history and not stream:
        from src.retrieval.query_cache import get_cached, set_cache
        cached = get_cached(standalone_question, kb_ids or [])
    if cached:
        cached["conversation_id"] = conv.id
        return cached

    # 4. 混合检索（含 ACL 过滤 + Reranker 精排）
    search_results = await hybrid_search(standalone_question, user_id=user_id, kb_ids=kb_ids if kb_ids else None, top_k=5, use_reranker=settings.reranker_enabled)

    # 4a. 补全引用元数据：文档标题、KB名称、页码
    doc_ids = list({r["document_id"] for r in search_results})
    kb_ids_set = list({r["kb_id"] for r in search_results})

    doc_map: dict[str, tuple[str, int | None]] = {}  # doc_id -> (title, page_count)
    kb_map: dict[str, str] = {}
    if doc_ids:
        doc_rows = (await db.execute(select(Document.id, Document.title, Document.page_count).where(Document.id.in_(doc_ids)))).all()
        doc_map = {row[0]: (row[1], row[2]) for row in doc_rows}
    if kb_ids_set:
        kb_rows = (await db.execute(select(KnowledgeBase.id, KnowledgeBase.name).where(KnowledgeBase.id.in_(kb_ids_set)))).all()
        kb_map = {row[0]: row[1] for row in kb_rows}

    # chunk_id 格式为 {document_id}_{chunk_index}，批量查询元数据
    chunk_meta_map: dict[str, dict] = {}  # chunk_id -> {page, section_path, content_type}
    chunk_indexes: list[tuple[str, str, int]] = []
    for r in search_results:
        cid = r.get("chunk_id", "")
        did = r["document_id"]
        if "_" in cid and cid.startswith(did):
            try:
                chunk_indexes.append((cid, did, int(cid.split("_")[-1])))
            except ValueError:
                from loguru import logger
                logger.debug(f"chunk_id 格式异常，跳过: {cid}")

    if chunk_indexes:
        doc_ids_in = list({did for _, did, _ in chunk_indexes})
        all_chunks = (await db.execute(
            select(DocumentChunk.document_id, DocumentChunk.chunk_index,
                   DocumentChunk.page_start, DocumentChunk.section_path, DocumentChunk.content_type).where(
                DocumentChunk.document_id.in_(doc_ids_in)
            )
        )).all()
        lookup: dict[tuple[str, int], tuple] = {}
        for row in all_chunks:
            lookup[(row[0], row[1])] = (row[2], row[3], row[4])
        for cid, did, idx in chunk_indexes:
            meta = lookup.get((did, idx)) or lookup.get((did, idx + 1))
            if meta is not None:
                chunk_meta_map[cid] = {"page": meta[0], "section_path": meta[1], "content_type": meta[2]}

    # 4b. 上下文扩展：每个命中 chunk 附带前后各 1 个相邻 chunk
    adjacent_texts: dict[str, dict[str, str]] = {}  # chunk_id -> {prev, next}
    if chunk_indexes:
        for cid, did, idx in chunk_indexes:
            for offset, key in [(-1, "prev"), (1, "next")]:
                adj_text = (await db.execute(
                    select(DocumentChunk.chunk_text).where(
                        DocumentChunk.document_id == did,
                        DocumentChunk.chunk_index == idx + offset,
                    )
                )).scalar_one_or_none()
                if adj_text:
                    adjacent_texts.setdefault(cid, {})[key] = adj_text

    # 4c. 构建上下文 + 引用
    context_parts: list[str] = []
    citations: list[dict] = []
    chunk_ids_for_db: list[str] = []

    for i, r in enumerate(search_results, start=1):
        cid = r.get("chunk_id", "")
        # 拼接相邻 chunk 扩展上下文
        adj = adjacent_texts.get(cid, {})
        parts = []
        if adj.get("prev"):
            parts.append(adj["prev"])
        parts.append(r["text"])
        if adj.get("next"):
            parts.append(adj["next"])
        context_parts.append(f"[来源{i}] {'\n'.join(parts)}")
        did = r["document_id"]
        doc_info = doc_map.get(did, ("", None))
        meta = chunk_meta_map.get(cid, {})
        citations.append({
            "source_index": i,
            "document_id": did,
            "document_title": doc_info[0],
            "kb_name": kb_map.get(r.get("kb_id", ""), ""),
            "page": meta.get("page"),
            "section_path": meta.get("section_path"),
            "content_type": meta.get("content_type", "prose"),
            # 从 snippet 中移除章节路径前缀，章节信息由 section_path 字段单独展示
            "snippet": _strip_section_prefix(r["text"])[:300],
            "relevance_score": r["score"],
        })
        chunk_ids_for_db.append(cid)

    # 保存用户消息
    user_msg = Message(conversation_id=conv.id, role="user", content=question, token_count=len(question))
    db.add(user_msg)
    await db.commit()

    context_text = "\n\n".join(context_parts) if context_parts else "知识库中未找到相关信息"

    # 5. LLM 生成
    provider = registry.get_provider(model_name)
    system_prompt, user_prompt = _build_prompt(context_text, history, standalone_question)
    req = LLMRequest(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model_name,
        temperature=0.3,
        max_tokens=2048,
    )

    if stream:
        return {
            "conversation_id": conv.id,
            "stream_generator": _stream_response(provider, req, conv.id, user_msg.id, citations, chunk_ids_for_db, db, question),
        }

    resp = await provider.chat(req)

    # 未找到相关信息时清空引用
    no_result_markers = ["知识库中未找到相关信息", "未找到相关信息", "无法从文档中找到", "no relevant information found"]
    has_sources = "[来源" in resp.content or "[source" in resp.content.lower()
    if any(m in resp.content for m in no_result_markers) and not has_sources:
        citations.clear()
        chunk_ids_for_db.clear()

    # 保存助手消息 + 引用
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=resp.content,
        token_count=resp.output_tokens,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    # 保存引用关系
    for i, cit in enumerate(citations):
        db.add(MessageCitation(
            message_id=assistant_msg.id,
            chunk_id=chunk_ids_for_db[i] if i < len(chunk_ids_for_db) else "",
            document_id=cit["document_id"],
            relevance_score=cit["relevance_score"],
            snippet=cit["snippet"],
            page_number=cit.get("page"),
        ))
    await db.commit()

    # 更新对话标题（取第一个问题前 30 字）
    if not conv.title and len(question) > 0:
        conv.title = question[:50] + ("..." if len(question) > 50 else "")
        await db.commit()

    result = {
        "answer": resp.content,
        "conversation_id": conv.id,
        "message_id": assistant_msg.id,
        "model": resp.model,
        "tokens": {"input": resp.input_tokens, "output": resp.output_tokens},
        "citations": citations,
    }
    # 写入缓存
    if not history and not stream:
        from src.retrieval.query_cache import set_cache
        set_cache(standalone_question, kb_ids or [], result)
    return result


async def _rewrite_query(question: str, history: list[dict], model_name: str) -> str:
    """LLM 判断是否关联历史，有上下文依赖时改写为独立查询"""
    if not settings.query_rewrite_enabled:
        return question

    user_msgs = [m for m in history if m["role"] == "user"]
    if not user_msgs:
        return question

    # 取最近 3 轮对话
    recent = history[-6:]
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    prompt = f"""判断当前问题是否依赖对话历史。如果依赖，改写为完全独立的查询（补全省略主语/替换代词）。如果独立，原样返回。

## 对话历史
{history_text}

## 当前问题
{question}

## 输出规则
- 不依赖历史 → 直接输出原问题
- 依赖历史 → 输出改写后的问题（补充省略信息）
- 只输出最终结果，不要解释"""

    try:
        provider = registry.get_provider(settings.query_rewrite_model)
        resp = await provider.chat(LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            model=settings.query_rewrite_model,
            temperature=0.1,
            max_tokens=200,
        ))
        rewritten = resp.content.strip()
        if not rewritten or len(rewritten) < 2:
            return question
        return rewritten
    except Exception:
        from loguru import logger
        logger.warning("查询改写 LLM 调用失败，回退为原问题")
        return question


async def _stream_response(provider, req, conv_id, user_msg_id, citations, chunk_ids, db, question):
    """SSE 流式生成器"""
    full_content = ""
    async for token in provider.chat_stream(req):
        full_content += token
        yield f"data: {json.dumps({'token': token})}\n\n"

    # 流结束后保存消息和引用
    async with db as session:
        assistant_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=full_content,
        )
        session.add(assistant_msg)
        await session.commit()
        await session.refresh(assistant_msg)

        # 未找到相关信息时跳过引用存储
        no_result_markers = ["知识库中未找到相关信息", "未找到相关信息", "无法从文档中找到", "no relevant information found"]
        has_sources = "[来源" in full_content or "[source" in full_content.lower()
        if not (any(m in full_content for m in no_result_markers) and not has_sources):
            for i, cit in enumerate(citations):
                session.add(MessageCitation(
                    message_id=assistant_msg.id,
                    chunk_id=chunk_ids[i] if i < len(chunk_ids) else "",
                    document_id=cit["document_id"],
                    relevance_score=cit["relevance_score"],
                    snippet=cit["snippet"],
                    page_number=cit.get("page"),
                ))
        await session.commit()

        # 更新对话标题
        conv_row = await session.get(Conversation, conv_id)
        if conv_row and not conv_row.title:
            conv_row.title = question[:50] + ("..." if len(question) > 50 else "")
            await session.commit()

    final_citations = [] if any(m in full_content for m in no_result_markers) else citations
    yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id, 'message_id': assistant_msg.id, 'citations': final_citations})}\n\n"


def _strip_section_prefix(text: str) -> str:
    """移除文本开头的【章节路径】标记，章节信息由元数据字段单独展示"""
    return re.sub(r"^【.+?】\s*\n?", "", text)


def _build_prompt(context: str, history: list[dict], question: str) -> tuple[str, str]:
    """构建 system prompt 和 user prompt，返回 (system, user)"""
    history_text = ""
    if history:
        recent = history[-6:]
        history_text = "## 对话历史\n" + "\n".join(
            f"{m['role']}: {m['content']}" for m in recent
        ) + "\n\n"

    system = """## 角色
你是专业的企业知识库问答助手，服务于内部员工查阅公司制度、产品文档、项目资料等。你的回答直接影响业务决策，请保持专业、准确、友善。

## 回答原则
1. **严格基于文档**：仅使用下述"相关文档"中的内容作答，不得引入外部知识或主观猜测
2. **区分确定性**：信息明确时直接给出答案；信息不完整时说明缺失部分，而非编造
3. **多源冲突**：如果不同文档片段之间存在矛盾，如实指出并列出各自的说法
4. **结构化输出**：优先用分点、表格等方式呈现复杂信息，提高可读性
5. **引用规范**：引用时使用方括号标注来源编号，如 [1]、[2]

## 回答格式
- 先给出一句核心结论或摘要
- 展开详细说明（如有多个要点请分点列出）
- 最后列出引用的来源编号及对应的文档名称/页码（如已知）

## 无法回答时
如果以下文档中确实找不到相关信息，请回复：
"知识库中未找到该问题的相关信息。建议您：
- 检查问题中的关键词是否准确
- 补充更多上下文以便精准检索
- 联系对应文档的负责人确认是否有相关资料"
不得编造信息，不得回答不在文档范围内的问题。"""

    user = f"""{history_text}## 相关文档
{context}

## 用户问题
{question}"""
    return system, user

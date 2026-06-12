"""文档分块 — 三策略路由 + 按 doc_type 分参数

决策树（参考分块.md 2.2 节）：
  有章节结构 → ② 结构分块
  无结构长文 → ③ 语义分块
  其他        → ① 递归字符分块（兜底）

参数 per file_type（分块.md 2.3 节）：
  PDF(文本型/扫描件): 500 字符 / 60 overlap
  DOCX(有标题结构):   500 字符 / 60 overlap → 结构分块优先
  MD(有#标题):        800 字符 / 120 overlap → 结构分块优先
  TXT(无结构):        500 字符 / 60 overlap
"""

import re, math
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    text: str
    page_start: int | None = None
    page_end: int | None = None
    token_count: int | None = None
    section_path: str | None = None
    content_type: str = "prose"


# ── 参数 ─────────────────────────────────────────

_SEMANTIC_MIN_CHARS = 2048

_DEFAULT_PARAMS = {
    "application/pdf":     {"chunk_size": 500, "overlap": 60},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {"chunk_size": 500, "overlap": 60},
    "text/markdown":       {"chunk_size": 800, "overlap": 120},
    "text/plain":          {"chunk_size": 500, "overlap": 60},
    "text/txt":            {"chunk_size": 500, "overlap": 60},
}


# ── 入口 ────────────────────────────────────────

def chunk_text(
    text: str,
    page_number: int | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 60,
    file_type: str | None = None,
) -> list[Chunk]:
    if not text.strip():
        return []

    # file_type → 默认参数（KB 级别配置可覆盖）
    if file_type and file_type in _DEFAULT_PARAMS:
        p = _DEFAULT_PARAMS[file_type]
        if chunk_size == 500 and chunk_overlap == 60:
            chunk_size, chunk_overlap = p["chunk_size"], p["overlap"]

    # 表格/列表原子保护
    text = _protect_atomic(text)

    # ③ 结构分块：有章节标记的文档
    if _has_structure(text):
        return _section_chunk(text, page_number, chunk_size, chunk_overlap)

    # ② 语义分块：无结构长文
    if len(text) > _SEMANTIC_MIN_CHARS:
        sents = _split_sentences(text)
        if len(sents) >= 10:
            return _semantic_chunk(sents, page_number, chunk_size, chunk_overlap)

    # ① 递归字符分块：兜底
    return _recursive_chunk(text, page_number, chunk_size, chunk_overlap)


# ── 策略 ①：递归字符分块 ──────────────────────────

def _recursive_chunk(text: str, page: int | None, cs: int, co: int) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cs, chunk_overlap=co,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
    )
    return [Chunk(text=s, page_start=page, page_end=page, token_count=len(s))
            for s in splitter.split_text(text)]


# ── 策略 ②：结构分块 ─────────────────────────────

def _has_structure(text: str) -> bool:
    return bool(re.search(r"【|^#{1,6}\s|^第[一二三四五六七八九十百千\d]+[章节条]", text, re.MULTILINE))


def _section_chunk(text: str, page: int | None, cs: int, co: int) -> list[Chunk]:
    sections = re.split(r"\n(?=【|#{1,6}\s|第[一二三四五六七八九十百千\d]+[章节条])", text)
    chunks: list[Chunk] = []
    for sec in sections:
        sec = sec.strip()
        if not sec: continue

        m = re.match(r"【(.+?)】", sec)
        path = m.group(1) if m else None
        ct = "clause" if re.search(r"第[一二三四五六七八九十百千\d]+条", sec) else "prose"

        if len(sec) <= cs:
            chunks.append(Chunk(text=sec, page_start=page, page_end=page, token_count=len(sec),
                                section_path=path, content_type=ct))
        else:
            for sub in _recursive_chunk(sec, page, cs, co):
                sub.section_path = path; sub.content_type = ct
                chunks.append(sub)
    return chunks


# ── 策略 ③：语义分块 ──────────────────────────────

def _semantic_chunk(sentences: list[str], page: int | None, cs: int, co: int) -> list[Chunk]:
    from src.ingestion.embedder import embed_texts
    try:
        embs = embed_texts(sentences)
        if len(embs) != len(sentences): raise ValueError("count mismatch")
    except Exception as e:
        from loguru import logger
        logger.warning(f"语义分块 embedding 失败，回退到递归字符分块: {e}")
        return _recursive_chunk("\n".join(sentences), page, cs, co)

    sims = [_cos(embs[i], embs[i+1]) for i in range(len(embs)-1)]
    if not sims: return _recursive_chunk("\n".join(sentences), page, cs, co)

    threshold = sorted(sims)[max(0, int(len(sims)*0.1)-1)]
    groups, cur, cur_len = [], [sentences[0]], len(sentences[0])
    for i, s in enumerate(sentences[1:], start=1):
        if sims[i-1] < threshold or cur_len + len(s) > int(cs*1.2):
            groups.append(cur)
            cur = [cur[-1]] if co > 0 else []; cur_len = sum(len(x) for x in cur)
        cur.append(s); cur_len += len(s)
    if cur: groups.append(cur)

    result: list[Chunk] = []
    for g in groups:
        t = "\n".join(g)
        if len(t) > cs*1.5: result.extend(_recursive_chunk(t, page, cs, co))
        else: result.append(Chunk(text=t, page_start=page, page_end=page, token_count=len(t)))
    return result


# ── 工具 ──────────────────────────────────────────

def _protect_atomic(text: str) -> str:
    lines = text.split("\n"); out, buf = [], []; in_table, in_list = False, False
    def flush():
        nonlocal in_table, in_list
        if buf:
            c = "\n".join(buf)
            out.append(f"\n\n{c}\n\n" if (in_table or in_list) else c)
            buf.clear()
        in_table = in_list = False
    for line in lines:
        s = line.strip()
        tbl = bool(re.match(r"^\|.+\|$", s))
        lst = bool(re.match(r"^(\s*[-*+]|\s*\d+[.)])\s", s))
        if tbl and not in_table: flush(); in_table = True
        if lst and not in_list: flush(); in_list = True
        if tbl or lst: buf.append(line)
        else:
            if in_table or in_list:
                if s and (in_list and (line.startswith(" ") or line.startswith("\t"))): buf.append(line)
                else: flush(); out.append(line)
            else: out.append(line)
    flush()
    return "\n".join(out)

def _split_sentences(text: str) -> list[str]:
    paras = re.split(r"(\n{2,})", text); sents = []
    for p in paras:
        if re.match(r"^\n+$", p): continue
        for sub in re.split(r"(?<=[。！？.!?])(?=\S)", p):
            s = sub.strip()
            if s and len(s) > 2: sents.append(s)
    return sents or [text]

def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x*y for x,y in zip(a,b))
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

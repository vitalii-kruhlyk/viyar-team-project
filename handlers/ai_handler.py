import os

import numpy as np
from google import genai
from google.genai.errors import ClientError

PRIMARY_MODEL = "gemini-3.1-flash-lite"
FALLBACK_MODEL = "gemma-4-31b"
EMBEDDING_MODEL = "gemini-embedding-2"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY in .env to enable AI features")
        _client = genai.Client(api_key=api_key)
    return _client


def _generate(prompt: str) -> str:
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt,
        )
    except ClientError as e:
        if e.code == 429:
            response = client.models.generate_content(
                model=FALLBACK_MODEL,
                contents=prompt,
            )
        elif e.code in (403, 500):
            raise ValueError(f"Gemini API error {e.code}: {e.message}") from e
        else:
            raise
    if response.text is None:
        raise ValueError("Gemini returned empty response (content may be blocked by safety filter)")
    return response.text.strip()


def _embed(text: str) -> list[float]:
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    if not response.embeddings:
        raise ValueError("Gemini returned empty embeddings")
    return response.embeddings[0].values or []


def generate_tags(content: str) -> list[str]:
    prompt = (
        f"Generate 3 to 5 short relevant tags for the following note. "
        f"Return only a comma-separated list of tags, no explanations.\n\n{content}"
    )
    result = _generate(prompt)
    return [tag.strip().lstrip("#") for tag in result.split(",") if tag.strip()]


def generate_summary(content: str) -> str:
    prompt = (
        f"Write a brief summary (1-2 sentences) of the following note. "
        f"Return only the summary, no explanations.\n\n{content}"
    )
    return _generate(prompt)


def semantic_search(query: str, notes: list[dict]) -> list[dict]:
    if not notes:
        return []
    query_embedding = np.array(_embed(query))
    query_norm = np.linalg.norm(query_embedding)
    results = []
    for note in notes:
        cached = note.get("embedding")
        if isinstance(cached, list) and len(cached) > 0:
            note_embedding = np.array(cached)
        else:
            text = f"{note.get('title', '')} {note.get('content', '')}"
            note_embedding = np.array(_embed(text))
            note["embedding"] = note_embedding.tolist()
        note_norm = np.linalg.norm(note_embedding)
        if query_norm == 0 or note_norm == 0:
            score = 0.0
        else:
            score = float(np.dot(query_embedding, note_embedding) / (query_norm * note_norm))
        results.append((score, note))
    results.sort(key=lambda x: x[0], reverse=True)
    return [note for _, note in results[:5]]

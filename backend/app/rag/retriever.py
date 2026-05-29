from app.rag.store import query


def retrieve_context(query_text: str, n: int = 5) -> str:
    results = query(query_text, n_results=n)
    if not results:
        return ""

    lines = []
    for i, doc in enumerate(results, 1):
        meta = doc.get("metadata", {})
        lines.append(
            f"{i}. [{meta.get('attack_type', 'desconocido').upper()} | {meta.get('severity', '?')}] "
            f"{doc['text'][:300]}"
        )
    return "\n".join(lines)

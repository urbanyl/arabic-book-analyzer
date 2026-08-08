import json
import re
from typing import List, Optional

import ollama

from config import OLLAMA_HOST, OLLAMA_MODEL, MAX_CONTEXT_CHUNKS
from ..models.book import Citation


class AIEngine:
    def __init__(self):
        self.model = OLLAMA_MODEL
        self.client = ollama.Client(host=OLLAMA_HOST)

    def extract_citations(
        self,
        query: str,
        search_results: dict,
    ) -> List[Citation]:
        if not search_results.get("documents") or not search_results["documents"][0]:
            return []

        documents = search_results["documents"][0]
        metadatas = search_results["metadatas"][0]

        context_parts = []
        for i, (doc, meta) in enumerate(zip(documents[:MAX_CONTEXT_CHUNKS], metadatas[:MAX_CONTEXT_CHUNKS])):
            context_parts.append(
                f"--- مقطع {i+1} (كتاب: {meta['book_title']}, "
                f"صفحة: {meta['page']}, جزء: {meta.get('tome', 'غير محدد')}) ---\n{doc}"
            )

        context_text = "\n\n".join(context_parts)

        prompt = self._build_extraction_prompt(query, context_text)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "num_predict": 4096,
                },
                stream=False,
            )
            raw_response = response.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Erreur de connexion à Ollama: {e}\nAssurez-vous qu'Ollama est démarré.")

        citations = self._parse_response(raw_response, metadatas)
        return citations

    def _build_extraction_prompt(self, query: str, context: str) -> str:
        return f"""أنت مساعد متخصص في استخراج النصوص من الكتب العربية بدقة تامة.

المهمة: ابحث في النصوص التالية عن جميع الأقوال والعبارات المتعلقة بموضوع: "{query}"

القواعد الصارمة:
1. استخرج فقط النصوص الحرفية الموجودة فعلاً في النصوص أدناه.
2. لا تختلق أو تصنع أي اقتباس غير موجود.
3. لا تلخص أو تعيد صياغة النص.
4. إذا لم تجد شيئاً متعلقاً بالموضوع، اكتب فقط: "لا يوجد".
5. يجب أن يكون كل اقتباس موجوداً حرفياً في النصوص المقدمة لك.

أخرج النتيجة بصيغة JSON صحيحة فقط كما يلي:
[
  {{"text": "النص الحرفي هنا", "book": "اسم الكتاب", "author": "اسم المؤلف", "tome": "رقم الجزء", "page": "رقم الصفحة", "reference": "المرجع الكامل"}}
]

النصوص للبحث فيها:
{context}

النتيجة (JSON فقط بدون أي نص إضافي):"""

    def _parse_response(self, raw_response: str, metadatas: list) -> List[Citation]:
        citations = []

        json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if not json_match:
            if "لا يوجد" in raw_response or "لا توجد" in raw_response:
                return []
            return []

        try:
            items = json.loads(json_match.group())
        except json.JSONDecodeError:
            items = self._extract_json_objects(raw_response)

        if not items:
            return []

        for item in items:
            text = item.get("text", "").strip()
            if not text or len(text) < 5:
                continue
            if not self._verify_text_exists(text, metadatas):
                continue
            citations.append(Citation(
                text=text,
                book_title=item.get("book", ""),
                author=item.get("author", ""),
                tome=str(item.get("tome", "")),
                page=str(item.get("page", "")),
                reference=item.get("reference", ""),
            ))

        return citations

    def _extract_json_objects(self, text: str) -> list:
        objects = []
        depth = 0
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        obj = json.loads(text[start:i + 1])
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1
        return objects

    def _verify_text_exists(self, text: str, metadatas: list) -> bool:
        normalized_input = self._normalize(text)
        for meta in metadatas:
            doc_start = self._normalize(text[:60])
            if doc_start in self._normalize(meta.get("original_doc", "")):
                return True

        search_docs = []
        for m in metadatas:
            if "original_doc" in m:
                search_docs.append(m["original_doc"])

        for doc in search_docs:
            normalized_doc = self._normalize(doc)
            if normalized_input[:80] in normalized_doc:
                return True

        words = normalized_input.split()
        if len(words) >= 4:
            phrase = " ".join(words[:4])
            for doc in search_docs:
                if phrase in self._normalize(doc):
                    return True

        return True

    def _normalize(self, text: str) -> str:
        text = text.replace("،", " ").replace("؛", " ").replace("؟", " ")
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def check_model_available(self) -> bool:
        try:
            models = self.client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            return any(self.model in name for name in model_names)
        except Exception:
            return False

    def list_available_models(self) -> list:
        try:
            models = self.client.list()
            return [m.get("name", "") for m in models.get("models", [])]
        except Exception:
            return []

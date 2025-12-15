"""
Quiz Generator for StudyRAG
Generates quizzes (multiple choice, true/false, open-ended) based on PDF content using RAG.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Literal

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from backend.config import GOOGLE_API_KEY, LLM_MODEL, TEMPERATURE, MAX_TOKENS, TOP_K_RESULTS
from backend.retrieval_service import get_retrieval_service


QuizType = Literal["multiple_choice", "true_false", "open_ended", "mixed"]
DifficultyLevel = Literal["easy", "medium", "hard"]


class QuizGenerator:
    """
    Service that generates quizzes based on the loaded PDF content.
    Supports multiple choice, true/false, and open-ended questions.
    """

    def __init__(self) -> None:
        # MOCK mode: do not call real Gemini, build quizzes locally
        self.use_mock_llm = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

        if self.use_mock_llm:
            self.model = None
            print("✓ QuizGenerator initialized in MOCK LLM mode (no Google LLM calls)")
        else:
            # Configure Gemini
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(LLM_MODEL)
            print(f"✓ QuizGenerator initialized with model: {LLM_MODEL}")

        self.retrieval_service = get_retrieval_service()
        self.generation_config = {
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_TOKENS,
        }

    def _build_mock_quiz(
        self,
        quiz_type: QuizType,
        num_questions: int,
        difficulty: DifficultyLevel,
        topic: Optional[str],
    ) -> Dict[str, Any]:
        """
        Fallback / mock quiz that does not depend on Gemini responses.
        Useful for development when LLM quota or model is unavailable.
        """
        questions: List[Dict[str, Any]] = []
        answer_key: Dict[str, str] = {}

        topic_text = topic or "ders notları"

        for i in range(num_questions):
            q_id = i + 1
            q_type = quiz_type if quiz_type != "mixed" else ["multiple_choice", "true_false", "open_ended"][i % 3]

            if q_type == "multiple_choice":
                questions.append({
                    "id": q_id,
                    "type": "multiple_choice",
                    "question": f"[MOCK] {topic_text} ile ilgili örnek soru {q_id}?",
                    "choices": [
                        f"A) Seçenek A - Örnek cevap",
                        f"B) Seçenek B - Alternatif cevap",
                        f"C) Seçenek C - Başka bir cevap",
                        f"D) Seçenek D - Son seçenek"
                    ],
                    "correct_answer": "A",
                    "explanation": f"Bu bir MOCK sorudur. Gerçek LLM kullanıldığında {topic_text} içeriğinden soru üretilecektir.",
                    "source_page": (i % 5) + 1
                })
                answer_key[str(q_id)] = "A"

            elif q_type == "true_false":
                questions.append({
                    "id": q_id,
                    "type": "true_false",
                    "question": f"[MOCK] {topic_text} konusu ile ilgili bu ifade doğrudur: Örnek ifade {q_id}.",
                    "choices": ["Doğru", "Yanlış"],
                    "correct_answer": "Doğru" if i % 2 == 0 else "Yanlış",
                    "explanation": f"Bu bir MOCK sorudur. Gerçek LLM kullanıldığında {topic_text} içeriğinden soru üretilecektir.",
                    "source_page": (i % 5) + 1
                })
                answer_key[str(q_id)] = "Doğru" if i % 2 == 0 else "Yanlış"

            else:  # open_ended
                questions.append({
                    "id": q_id,
                    "type": "open_ended",
                    "question": f"[MOCK] {topic_text} konusunda açık uçlu örnek soru {q_id}: Bu kavramı kendi cümlelerinle açıkla.",
                    "choices": None,
                    "correct_answer": f"Örnek cevap: {topic_text} ile ilgili detaylı bir açıklama beklenmektedir.",
                    "explanation": f"Bu bir MOCK sorudur. Gerçek LLM kullanıldığında {topic_text} içeriğinden soru üretilecektir.",
                    "source_page": (i % 5) + 1
                })
                answer_key[str(q_id)] = "Açık uçlu - model cevabı kontrol edecek"

        return {
            "quiz_type": quiz_type,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "topic": topic_text,
            "questions": questions,
            "answer_key": answer_key,
            "note": "Bu quiz MOCK modunda üretilmiştir."
        }

    def generate_quiz(
        self,
        quiz_type: QuizType = "multiple_choice",
        num_questions: int = 5,
        difficulty: DifficultyLevel = "medium",
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on the uploaded document.

        Args:
            quiz_type: Type of quiz - multiple_choice, true_false, open_ended, or mixed
            num_questions: Number of questions to generate (1-20)
            difficulty: Difficulty level - easy, medium, or hard
            topic: Optional specific topic to focus on

        Returns:
            Dict containing quiz questions and answer key
        """
        # Ensure we have a vector store loaded
        if self.retrieval_service.rag_pipeline.vectorstore is None:
            raise ValueError(
                "No vector store loaded. Please upload a PDF first using /upload endpoint."
            )

        # Retrieve context from notes
        query = topic or "Bu ders notlarının ana konuları ve önemli kavramları nelerdir?"
        documents = self.retrieval_service.retrieve_documents(
            query=query,
            k=TOP_K_RESULTS * 2,
        )
        context = self.retrieval_service.build_context_from_docs(documents)

        # If we are in MOCK LLM mode, skip real Gemini call entirely
        if self.use_mock_llm:
            return self._build_mock_quiz(quiz_type, num_questions, difficulty, topic)

        # Build quiz type instructions
        quiz_type_instructions = self._get_quiz_type_instructions(quiz_type)
        difficulty_instructions = self._get_difficulty_instructions(difficulty)

        prompt = f"""Sen bir eğitim uzmanı ve sınav hazırlayıcısısın.
Görevin, verilen ders notu BAĞLAMINA göre quiz soruları üretmek.

BAĞLAM (ders notlarından alınmış parçalar):
{context}

QUIZ PARAMETRELERİ:
- Quiz türü: {quiz_type}
- Soru sayısı: {num_questions}
- Zorluk seviyesi: {difficulty}
- Özel konu odağı: {topic or "belirtilmedi (tüm içerikten sor)"}

{quiz_type_instructions}

{difficulty_instructions}

TALİMATLAR:
1. Sadece verilen bağlamdaki bilgilere göre soru sor
2. Her sorunun açık ve anlaşılır olmasını sağla
3. Doğru cevabı ve kısa bir açıklama ekle
4. Kaynak sayfa numarasını belirt (context'ten)
5. Türkçe olarak yaz

SADECE AŞAĞIDAKİ JSON ŞEMASINA UYAN GEÇERLİ BİR JSON DÖNDÜR.
Açıklama veya markdown yazma, sadece JSON.

JSON ŞEMASI:
{{
  "quiz_type": "{quiz_type}",
  "difficulty": "{difficulty}",
  "num_questions": {num_questions},
  "topic": str veya null,
  "questions": [
    {{
      "id": int,                    // 1, 2, 3...
      "type": str,                  // "multiple_choice", "true_false", "open_ended"
      "question": str,              // Soru metni
      "choices": [str, ...] | null, // Şıklar (açık uçlu için null)
      "correct_answer": str,        // Doğru cevap
      "explanation": str,           // Kısa açıklama
      "source_page": int            // Kaynak sayfa numarası
    }}
  ],
  "answer_key": {{                  // Cevap anahtarı
    "1": str,
    "2": str,
    ...
  }}
}}
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
            )
            raw_text = response.text
        except google_exceptions.GoogleAPIError as exc:
            print(
                f"⚠️ QuizGenerator Gemini error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK quiz."
            )
            return self._build_mock_quiz(quiz_type, num_questions, difficulty, topic)
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"⚠️ Unexpected QuizGenerator error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK quiz."
            )
            return self._build_mock_quiz(quiz_type, num_questions, difficulty, topic)

        # Parse JSON response
        try:
            # Clean up potential markdown formatting
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            data = json.loads(clean_text.strip())
        except json.JSONDecodeError:
            # Fallback: return mock quiz with error note
            mock_data = self._build_mock_quiz(quiz_type, num_questions, difficulty, topic)
            mock_data["note"] = f"Model geçerli JSON döndüremedi. Raw response: {raw_text[:500]}"
            return mock_data

        # Ensure required fields exist
        data.setdefault("quiz_type", quiz_type)
        data.setdefault("difficulty", difficulty)
        data.setdefault("num_questions", num_questions)
        
        # Build answer key if not provided
        if "answer_key" not in data and "questions" in data:
            data["answer_key"] = {
                str(q["id"]): q.get("correct_answer", "")
                for q in data["questions"]
            }

        return data

    def _get_quiz_type_instructions(self, quiz_type: QuizType) -> str:
        """Get specific instructions for each quiz type."""
        instructions = {
            "multiple_choice": """
ÇOKTAN SEÇMELİ SORULAR İÇİN:
- Her soru için 4 şık oluştur (A, B, C, D)
- Sadece bir doğru cevap olsun
- Yanlış şıklar mantıklı ama yanlış olsun (çeldirici)
- choices: ["A) ...", "B) ...", "C) ...", "D) ..."]
- correct_answer: sadece harf (örn: "A")
""",
            "true_false": """
DOĞRU-YANLIŞ SORULARI İÇİN:
- Açık ve net ifadeler yaz
- Belirsiz ifadelerden kaçın
- choices: ["Doğru", "Yanlış"]
- correct_answer: "Doğru" veya "Yanlış"
""",
            "open_ended": """
AÇIK UÇLU SORULAR İÇİN:
- Düşünmeye ve açıklamaya teşvik eden sorular sor
- choices: null (şık yok)
- correct_answer: beklenen cevabın özeti
""",
            "mixed": """
KARMA QUIZ İÇİN:
- Farklı türlerde sorular karıştır
- Çoktan seçmeli, doğru-yanlış ve açık uçlu sorular ekle
- Her sorunun type alanını doğru belirt
"""
        }
        return instructions.get(quiz_type, instructions["multiple_choice"])

    def _get_difficulty_instructions(self, difficulty: DifficultyLevel) -> str:
        """Get specific instructions for each difficulty level."""
        instructions = {
            "easy": """
KOLAY SEVİYE:
- Temel kavram ve tanım soruları
- Doğrudan metinde geçen bilgiler
- Karmaşık hesaplama veya analiz gerektirmeyen sorular
""",
            "medium": """
ORTA SEVİYE:
- Kavramları anlama ve uygulama soruları
- Birden fazla bilgiyi birleştirmeyi gerektiren sorular
- Temel düzeyde analiz gerektiren sorular
""",
            "hard": """
ZOR SEVİYE:
- Analiz ve sentez gerektiren sorular
- Kavramlar arası ilişkileri sorgulayan sorular
- Eleştirel düşünme gerektiren sorular
- Verilen bilgiyi farklı bağlamlara uygulamayı gerektiren sorular
"""
        }
        return instructions.get(difficulty, instructions["medium"])


# Singleton instance
_quiz_generator: Optional[QuizGenerator] = None


def get_quiz_generator() -> QuizGenerator:
    """
    Get or create singleton QuizGenerator instance.
    """
    global _quiz_generator
    if _quiz_generator is None:
        _quiz_generator = QuizGenerator()
    return _quiz_generator

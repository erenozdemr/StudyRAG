"""
Study Plan Generator for StudyRAG
Uses RAG context and Google Gemini to build structured study plans.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from backend.config import GOOGLE_API_KEY, LLM_MODEL, TEMPERATURE, MAX_TOKENS, TOP_K_RESULTS
from backend.retrieval_service import get_retrieval_service


class StudyPlanGenerator:
    """
    Service that generates study plans (3 / 7+ days) based on the loaded PDF.
    """

    def __init__(self) -> None:
        # MOCK mode: do not call real Gemini, build plans locally
        self.use_mock_llm = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

        if self.use_mock_llm:
            self.model = None
            print("✓ StudyPlanGenerator initialized in MOCK LLM mode (no Google LLM calls)")
        else:
            # Configure Gemini
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(LLM_MODEL)
            print(f"✓ StudyPlanGenerator initialized with model: {LLM_MODEL}")

        self.retrieval_service = get_retrieval_service()
        self.generation_config = {
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_TOKENS,
        }

    def _build_mock_plan(
        self,
        days: int,
        daily_minutes: int,
        focus: Optional[str],
        context_preview: str,
    ) -> Dict[str, Any]:
        """
        Fallback / mock study plan that does not depend on Gemini responses.
        Useful for development when LLM quota or model is unavailable.
        """
        strategy_parts = [
            "Bu çalışma planı MOCK modunda üretildi.",
            "Amaç: temelden ileri seviyeye doğru kademeli tekrar yapmak.",
        ]
        if focus:
            strategy_parts.append(f"Öncelik verilen konu: {focus}.")

        # Basit aşamalı plan:
        # - İlk %30: Temel kavramlar (her gün farklı alt odak)
        # - Orta %40: Örnek soru çözümü ve uygulama
        # - Son %30: Karışık sorular, tekrar ve deneme
        days_list: list[Dict[str, Any]] = []
        for i in range(days):
            day_index = i + 1
            progress = day_index / days

            if progress <= 0.3:
                phase = "temel"
            elif progress <= 0.7:
                phase = "uygulama"
            else:
                phase = "tekrar"

            base_topic = focus or "konular"

            if phase == "temel":
                temel_variants = [
                    {
                        "title": f"{base_topic} için temel kavramlar",
                        "focus_topics": [
                            f"{base_topic} ile ilgili tanımlar",
                            f"{base_topic} için temel formüller",
                        ],
                        "goals": [
                            "Ders notlarındaki ilgili teorik bölümü dikkatlice oku.",
                            "Önemli tanım ve formülleri kendi cümlelerinle tekrar yaz.",
                            "Kısa bir özet çıkar (maksimum 1 sayfa).",
                        ],
                    },
                    {
                        "title": f"{base_topic} grafik ve yorumlama",
                        "focus_topics": [
                            f"{base_topic} ile ilgili grafikler",
                            "Grafikler üzerinden fiziksel/anlam yorumları",
                        ],
                        "goals": [
                            "Notlardaki grafik örneklerini incele ve kendi grafiğini çiz.",
                            "Grafik üzerinden en az 3 yorum cümlesi yaz.",
                            "Grafik-tablo ilişkisini kurmaya çalış.",
                        ],
                    },
                    {
                        "title": f"{base_topic} kurallar ve istisnalar",
                        "focus_topics": [
                            f"{base_topic} için temel kurallar",
                            f"{base_topic} ile ilgili istisnai durumlar",
                        ],
                        "goals": [
                            "Kullanılan tüm kuralları listele.",
                            "Her kural için en az bir örnek ve bir karşı-örnek bul.",
                            "Karıştırdığın kuralları yan yana yazarak karşılaştır.",
                        ],
                    },
                ]
                v = temel_variants[(day_index - 1) % len(temel_variants)]
                title = f"Gün {day_index}: {v['title']}"
                focus_topics = v["focus_topics"]
                goals = v["goals"]
            elif phase == "uygulama":
                uygulama_variants = [
                    {
                        "title": f"{base_topic} temel örnekler ve uygulama",
                        "focus_topics": [
                            f"{base_topic} için temel örnekler",
                            f"{base_topic} üzerinde adım adım çözüm",
                        ],
                        "goals": [
                            "En az 5-7 temel seviye soru çöz ve çözümleri detaylı incele.",
                            "Hata yaptığın soruları işaretle ve nedenini not al.",
                            "Gerekiyorsa teorik kısma geri dönüp eksik noktalarını tamamla.",
                        ],
                    },
                    {
                        "title": f"{base_topic} orta seviye karışık sorular",
                        "focus_topics": [
                            f"{base_topic} içeren bileşik sorular",
                            "Adım adım çözüm stratejileri",
                        ],
                        "goals": [
                            "En az 5 orta seviye karışık soru çöz.",
                            "Her soru için kullandığın stratejiyi bir cümle ile özetle.",
                            "Zorlandığın 2-3 soruyu öğretmenine/sınıf arkadaşına sorulacak şekilde not et.",
                        ],
                    },
                    {
                        "title": f"{base_topic} sözel yorum soruları",
                        "focus_topics": [
                            f"{base_topic} ile ilgili sözel yorumlar",
                            "Gerçek hayat uygulamaları",
                        ],
                        "goals": [
                            "En az 3 sözel yorum sorusu çöz.",
                            "Her soru için fiziksel / günlük hayat yorumu yaz.",
                            "Konu ile ilgili kendi örnek problemini yaz ve çözmeye çalış.",
                        ],
                    },
                ]
                v = uygulama_variants[(day_index - 1) % len(uygulama_variants)]
                title = f"Gün {day_index}: {v['title']}"
                focus_topics = v["focus_topics"]
                goals = v["goals"]
            else:  # tekrar / sınava hazırlık
                tekrar_variants = [
                    {
                        "title": f"{base_topic} genel tekrar ve sınav provası",
                        "focus_topics": [
                            f"{base_topic} için karışık seviye sorular",
                            f"{base_topic} konu özetlerinin gözden geçirilmesi",
                        ],
                        "goals": [
                            "Zaman tutarak 8-10 karışık seviye soru çöz.",
                            "Zorlandığın alt başlıkları listele ve kısa tekrar yap.",
                            "Kendi kendine mini bir sınav yapıp sonucunu değerlendir.",
                        ],
                    },
                    {
                        "title": f"{base_topic} geçmiş sınav soruları",
                        "focus_topics": [
                            f"{base_topic} içeren geçmiş yıl soruları",
                            "Sık çıkan soru tipleri",
                        ],
                        "goals": [
                            "Geçmiş yıllardan en az 5 gerçek sınav sorusu çöz.",
                            "Sık tekrar eden soru kalıplarını not al.",
                            "Sürpriz gelen soru tiplerini ayrı bir listeye yaz.",
                        ],
                    },
                ]
                v = tekrar_variants[(day_index - 1) % len(tekrar_variants)]
                title = f"Gün {day_index}: {v['title']}"
                focus_topics = v["focus_topics"]
                goals = v["goals"]

            if day_index == days:
                goals.append("Tüm konular için genel özet çıkar ve eksik gördüğün yerleri işaretle.")

            days_list.append(
                {
                    "day_index": day_index,
                    "title": title,
                    "focus_topics": focus_topics,
                    "goals": goals,
                    "estimated_minutes": daily_minutes,
                    "notes": "Bu plan geliştirme (mock) modunda oluşturulmuştur.",
                }
            )

        return {
            "total_days": days,
            "daily_minutes": daily_minutes,
            "strategy_summary": " ".join(strategy_parts),
            "days": days_list,
        }

    def generate_plan(
        self,
        days: int,
        daily_minutes: int,
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured study plan.

        Args:
            days: Total number of study days (e.g. 3 or 7)
            daily_minutes: Target minutes per day
            focus: Optional topic to prioritize

        Returns:
            Dict that matches StudyPlanResponse schema
        """
        # Ensure we have a vector store loaded
        if self.retrieval_service.rag_pipeline.vectorstore is None:
            raise ValueError(
                "No vector store loaded. Please upload a PDF first using /upload endpoint."
            )

        # Retrieve broader context from notes
        query = focus or "Bu ders notlarının ana konuları ve öğrenme sırası nedir?"
        documents = self.retrieval_service.retrieve_documents(
            query=query,
            k=TOP_K_RESULTS * 2,
        )
        context = self.retrieval_service.build_context_from_docs(documents)
        context_preview = context[:1000]

        # If we are in MOCK LLM mode, skip real Gemini call entirely
        if self.use_mock_llm:
            return self._build_mock_plan(days, daily_minutes, focus, context_preview)

        prompt = f"""
Sen bir uzman ders koçu ve eğitim planlayıcısın.
Görevin, verilen ders notu BAĞLAMI ve KULLANICI TERCİHLERİNE göre detaylı bir çalışma planı üretmek.

BAĞLAM (ders notlarından alınmış parçalar):
{context}

KULLANICI TERCİHLERİ:
- Toplam gün: {days}
- Günlük süre (dakika): {daily_minutes}
- Özel odak: {focus or "belirtilmedi"}

İSTEK:
- Konuyu mantıklı alt başlıklara böl
- Önce temeller, sonra orta seviye, en sonda zor konular gelsin
- Her gün için hedefleri ve odak konuları yaz
- Zor / önemli konulara daha fazla süre ayır

SADECE AŞAĞIDAKİ JSON ŞEMASINA UYAN GEÇERLİ BİR JSON DÖNDÜR.
Açıklama veya markdown yazma, sadece JSON.

JSON ŞEMASI:
{{
  "total_days": int,                // toplam gün sayısı
  "daily_minutes": int,             // hedef günlük süre (dakika)
  "strategy_summary": str,          // genel stratejinin kısa özeti (Türkçe)
  "days": [
    {{
      "day_index": int,             // 1..N
      "title": str,                 // gün başlığı (örn. "Temel tanımlar")
      "focus_topics": [str, ...],   // o gün çalışılacak ana alt konular
      "goals": [str, ...],          // o günün öğrenme hedefleri
      "estimated_minutes": int,     // o gün için önerilen süre
      "notes": str                  // ek tavsiyeler (kısa)
    }}
  ]
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
                f"⚠️ StudyPlanGenerator Gemini error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK plan."
            )
            return self._build_mock_plan(days, daily_minutes, focus, context_preview)
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"⚠️ Unexpected StudyPlanGenerator error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK plan."
            )
            return self._build_mock_plan(days, daily_minutes, focus, context_preview)

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback: sarmala ve ham metni notlara koy
            data = {
                "total_days": days,
                "daily_minutes": daily_minutes,
                "strategy_summary": (
                    "Model geçerli JSON döndüremedi, oluşturulan metin 'notes' alanına eklendi."
                ),
                "days": [
                    {
                        "day_index": 1,
                        "title": "Genel çalışma planı",
                        "focus_topics": [],
                        "goals": [],
                        "estimated_minutes": daily_minutes,
                        "notes": raw_text,
                    }
                ],
            }

        # Son kontroller ve varsayılanlar
        data.setdefault("total_days", days)
        data.setdefault("daily_minutes", daily_minutes)
        if "days" not in data or not isinstance(data["days"], list) or not data["days"]:
            data["days"] = [
                {
                    "day_index": 1,
                    "title": "Genel çalışma planı",
                    "focus_topics": [],
                    "goals": [],
                    "estimated_minutes": daily_minutes,
                    "notes": raw_text,
                }
            ]

        return data


_study_plan_generator: Optional[StudyPlanGenerator] = None


def get_study_plan_generator() -> StudyPlanGenerator:
    """
    Get or create singleton StudyPlanGenerator instance.
    """
    global _study_plan_generator
    if _study_plan_generator is None:
        _study_plan_generator = StudyPlanGenerator()
    return _study_plan_generator



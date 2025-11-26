"""
Alternate FastAPI entrypoint that adds a small HTML UI on top of the existing API.
Run with:
    uvicorn backend.main_ui:app --reload
"""

from backend.main import app  # reuse existing API and routes
from fastapi.responses import HTMLResponse


@app.get("/ui", response_class=HTMLResponse)
async def ui_page() -> HTMLResponse:
    """
    Simple HTML UI for uploading PDFs and asking questions.
    """
    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8" />
        <title>StudyRAG UI</title>
        <style>
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: #0f172a;
                color: #e5e7eb;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 960px;
                margin: 40px auto;
                padding: 24px;
                background: #020617;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                border: 1px solid #1e293b;
            }
            h1 {
                margin-top: 0;
                font-size: 28px;
                color: #f9fafb;
            }
            h2 {
                font-size: 20px;
                margin-top: 24px;
                color: #e5e7eb;
            }
            label {
                font-size: 14px;
                color: #9ca3af;
            }
            input[type="text"], input[type="number"], textarea {
                width: 100%;
                padding: 10px 12px;
                margin-top: 4px;
                margin-bottom: 12px;
                border-radius: 8px;
                border: 1px solid #1f2937;
                background: #020617;
                color: #e5e7eb;
                font-size: 14px;
            }
            input[type="file"] {
                margin-top: 4px;
                margin-bottom: 12px;
            }
            button {
                padding: 10px 16px;
                border-radius: 999px;
                border: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: linear-gradient(to right, #4f46e5, #6366f1);
                color: #e5e7eb;
                box-shadow: 0 10px 25px rgba(79,70,229,0.5);
            }
            button:disabled {
                opacity: 0.5;
                cursor: default;
                box-shadow: none;
            }
            .badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                font-size: 11px;
                background: #111827;
                color: #9ca3af;
                border: 1px solid #1e293b;
                margin-left: 8px;
            }
            .section {
                padding: 16px 0;
                border-top: 1px solid #111827;
                margin-top: 8px;
            }
            .output {
                margin-top: 12px;
                padding: 12px;
                background: #020617;
                border-radius: 12px;
                border: 1px solid #1e293b;
                font-size: 13px;
                white-space: pre-wrap;
            }
            .answer {
                font-size: 15px;
                line-height: 1.6;
            }
            .sources {
                margin-top: 8px;
                font-size: 12px;
                color: #9ca3af;
            }
            .chip {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 999px;
                background: #0f172a;
                border: 1px solid #1f2937;
                margin: 2px;
            }
            .status {
                font-size: 12px;
                color: #9ca3af;
                margin-top: 4px;
            }
            .row {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .row-inline {
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>StudyRAG UI <span class="badge">Beta</span></h1>
            <p style="font-size:14px;color:#9ca3af;margin-top:4px;">
                PDF yükle, vektör store oluştur, ders notlarına Türkçe sorular sor ve çalışma planı hazırla.
            </p>

            <div class="section">
                <h2>1. PDF Yükle ve Vektör Store Oluştur</h2>
                <label>PDF Dosyası</label><br />
                <input id="pdfFile" type="file" accept="application/pdf" />

                <label>Vectorstore Adı (opsiyonel)</label>
                <input id="vectorstoreName" type="text" placeholder="örn: matematik1" />

                <button id="uploadBtn">
                    <span>📤 PDF Yükle</span>
                </button>
                <div id="uploadStatus" class="status"></div>
                <div id="uploadOutput" class="output" style="display:none;"></div>
            </div>

            <div class="section">
                <h2>2. Soru Sor</h2>
                <label>Soru</label>
                <textarea id="question" rows="3" placeholder="Bu derste hangi konular işleniyor?"></textarea>

                <div class="row">
                    <div style="flex: 0 0 120px;">
                        <label>k (kaç parça kullanılsın?)</label>
                        <input id="topK" type="number" min="1" max="10" value="4" />
                    </div>
                    <div class="row-inline" style="margin-top:18px;">
                        <input id="includeSources" type="checkbox" checked />
                        <label for="includeSources">Kaynakları ekle</label>
                    </div>
                </div>

                <button id="askBtn">
                    <span>🤖 Soru Sor</span>
                </button>
                <div id="askStatus" class="status"></div>
                <div id="askOutput" class="output" style="display:none;">
                    <div id="answer" class="answer"></div>
                    <div id="sources" class="sources"></div>
                </div>
            </div>

            <div class="section">
                <h2>3. Çalışma Planı Oluştur</h2>

                <div class="row">
                    <div style="flex: 0 0 120px;">
                        <label>Gün sayısı</label>
                        <input id="planDays" type="number" min="1" max="30" value="7" />
                    </div>
                    <div style="flex: 0 0 160px;">
                        <label>Günlük dakika</label>
                        <input id="planMinutes" type="number" min="30" max="600" value="120" />
                    </div>
                </div>

                <label>Odaklanmak istediğin konu (opsiyonel)</label>
                <input id="planFocus" type="text" placeholder="örn: türev ve integral" />

                <button id="planBtn">
                    <span>📅 Çalışma Planı Üret</span>
                </button>
                <div id="planStatus" class="status"></div>
                <div id="planOutput" class="output" style="display:none;"></div>
            </div>
        </div>

        <script>
            const uploadBtn = document.getElementById("uploadBtn");
            const uploadStatus = document.getElementById("uploadStatus");
            const uploadOutput = document.getElementById("uploadOutput");
            const askBtn = document.getElementById("askBtn");
            const askStatus = document.getElementById("askStatus");
            const askOutput = document.getElementById("askOutput");
            const answerEl = document.getElementById("answer");
            const sourcesEl = document.getElementById("sources");

            const planBtn = document.getElementById("planBtn");
            const planStatus = document.getElementById("planStatus");
            const planOutput = document.getElementById("planOutput");

            uploadBtn.addEventListener("click", async () => {
                const fileInput = document.getElementById("pdfFile");
                const vectorstoreNameInput = document.getElementById("vectorstoreName");
                const file = fileInput.files[0];

                if (!file) {
                    alert("Lütfen bir PDF dosyası seç.");
                    return;
                }

                const formData = new FormData();
                formData.append("file", file);
                if (vectorstoreNameInput.value.trim() !== "") {
                    formData.append("vectorstore_name", vectorstoreNameInput.value.trim());
                } else {
                    formData.append("vectorstore_name", "default");
                }

                uploadBtn.disabled = true;
                uploadStatus.textContent = "PDF yükleniyor ve işleniyor...";
                uploadOutput.style.display = "none";

                try {
                    const res = await fetch("/upload", {
                        method: "POST",
                        body: formData
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || "Yükleme hatası");
                    }

                    uploadStatus.textContent = "Başarılı ✅";
                    uploadOutput.style.display = "block";
                    uploadOutput.textContent = JSON.stringify(data, null, 2);
                } catch (err) {
                    uploadStatus.textContent = "Hata ❌";
                    uploadOutput.style.display = "block";
                    uploadOutput.textContent = String(err);
                } finally {
                    uploadBtn.disabled = false;
                }
            });

            askBtn.addEventListener("click", async () => {
                const questionInput = document.getElementById("question");
                const topKInput = document.getElementById("topK");
                const includeSourcesInput = document.getElementById("includeSources");

                const question = questionInput.value.trim();
                if (!question) {
                    alert("Lütfen bir soru yaz.");
                    return;
                }

                const k = parseInt(topKInput.value || "4", 10);
                const includeSources = includeSourcesInput.checked;

                askBtn.disabled = true;
                askStatus.textContent = "Cevap üretiliyor...";
                askOutput.style.display = "none";
                answerEl.textContent = "";
                sourcesEl.textContent = "";

                try {
                    const res = await fetch("/ask", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            question,
                            k,
                            include_sources: includeSources
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || "Soru yanıtlama hatası");
                    }

                    askStatus.textContent = "Hazır ✅";
                    askOutput.style.display = "block";
                    answerEl.textContent = data.answer || "(cevap boş döndü)";

                    if (data.sources && Array.isArray(data.sources) && data.sources.length > 0) {
                        sourcesEl.innerHTML = "<strong>Kaynaklar:</strong><br/>";
                        data.sources.forEach((src) => {
                            const div = document.createElement("div");
                            div.className = "chip";
                            div.textContent = `Sayfa ${src.page ?? "?"} • ${String(src.source).split("/").pop()}`;
                            sourcesEl.appendChild(div);
                        });
                    } else {
                        sourcesEl.textContent = "Kaynak bilgisi yok.";
                    }
                } catch (err) {
                    askStatus.textContent = "Hata ❌";
                    askOutput.style.display = "block";
                    answerEl.textContent = String(err);
                    sourcesEl.textContent = "";
                } finally {
                    askBtn.disabled = false;
                }
            });

            planBtn.addEventListener("click", async () => {
                const daysInput = document.getElementById("planDays");
                const minutesInput = document.getElementById("planMinutes");
                const focusInput = document.getElementById("planFocus");

                const days = parseInt(daysInput.value || "7", 10);
                const dailyMinutes = parseInt(minutesInput.value || "120", 10);
                const focus = focusInput.value.trim() || null;

                planBtn.disabled = true;
                planStatus.textContent = "Çalışma planı oluşturuluyor...";
                planOutput.style.display = "none";
                planOutput.textContent = "";

                try {
                    const res = await fetch("/study-plan", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            days,
                            daily_minutes: dailyMinutes,
                            focus
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || "Çalışma planı oluşturma hatası");
                    }

                    planStatus.textContent = "Plan hazır ✅";
                    planOutput.style.display = "block";
                    planOutput.textContent = JSON.stringify(data, null, 2);
                } catch (err) {
                    planStatus.textContent = "Hata ❌";
                    planOutput.style.display = "block";
                    planOutput.textContent = String(err);
                } finally {
                    planBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)



# StudyRAG - RAG-Based Study Assistant 🎓

**Backend RAG Pipeline with Google Gemini API**

StudyRAG, Türkçe ders notlarınızı (PDF) yükleyip, yapay zeka destekli soru-cevap sistemi ile çalışmanıza yardımcı olan bir RAG (Retrieval-Augmented Generation) uygulamasıdır.

## 🎯 Özellikler

- **PDF İşleme**: Ders notlarınızı yükleyin ve otomatik olarak işleyin
- **Akıllı Chunking**: Metinleri optimal parçalara bölme
- **Google Gemini Embeddings**: Gelişmiş metin embedding'leri
- **FAISS Vector Store**: Hızlı ve etkili benzerlik araması
- **Türkçe Destekli Q&A**: Ders notlarınıza Türkçe sorular sorun
- **Kaynak Gösterimi**: Cevapların hangi sayfadan geldiğini görün

## 🏗️ Proje Yapısı

```
StudyRAG/
├── backend/
│   ├── __init__.py
│   ├── config.py              # Ayarlar ve konfigürasyon
│   ├── embedding_service.py   # Google Gemini embeddings
│   ├── rag_pipeline.py        # PDF işleme & vector store
│   ├── retrieval_service.py   # Q&A ve retrieval
│   └── main.py                # FastAPI uygulaması
├── data/
│   ├── uploads/               # Yüklenen PDF'ler
│   └── vectorstore/           # FAISS vector store'lar
├── .env                       # API anahtarları (gitignore'da)
├── .env.example               # Örnek environment dosyası
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Kurulum

### 1. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Google Gemini API Anahtarı

`.env.example` dosyasını `.env` olarak kopyalayın ve API anahtarınızı ekleyin:

```bash
# .env dosyası
GOOGLE_API_KEY=your_api_key_here
```

Google Gemini API anahtarı almak için: [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Sunucuyu Başlatın

```bash
# Proje dizininde çalıştırın
uvicorn backend.main:app --reload
```

Sunucu `http://localhost:8000` adresinde çalışacaktır.

## 📡 API Kullanımı

### Swagger UI (İnteraktif Dokümantasyon)

Tarayıcınızda açın: `http://localhost:8000/docs`

### 1. PDF Yükleme

```bash
POST /upload
Content-Type: multipart/form-data

# Form Data:
file: ders_notu.pdf
vectorstore_name: matematik_notu (opsiyonel)
```

### 2. Soru Sorma

```bash
POST /ask
Content-Type: application/json

{
  "question": "Bu dersin ana konuları nelerdir?",
  "k": 4,
  "include_sources": true
}
```

### Örnek cURL Komutları

**PDF Yükleme:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@ders_notu.pdf" \
  -F "vectorstore_name=matematik"
```

**Soru Sorma:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Türev nedir?",
    "k": 4,
    "include_sources": true
  }'
```

## 🧠 Mimari

### 1. **config.py**
- Environment variable yönetimi
- Model ve chunk ayarları
- Dizin yapılandırması

### 2. **embedding_service.py**
- Google Gemini embedding API entegrasyonu
- Document ve query embedding'leri
- Singleton pattern ile verimli kullanım

### 3. **rag_pipeline.py**
- PDF yükleme (PyPDFLoader)
- Text chunking (RecursiveCharacterTextSplitter)
- FAISS vector store oluşturma ve yönetimi
- LangChain entegrasyonu

### 4. **retrieval_service.py**
- Similarity search
- Türkçe optimize edilmiş promptlar
- Google Gemini ile cevap üretimi
- Kaynak referanslama

### 5. **main.py**
- FastAPI REST endpoints
- Request/Response validation
- Error handling
- CORS desteği

## ⚙️ Konfigürasyon

`.env` dosyasında özelleştirebileceğiniz ayarlar:

```bash
# Chunking
CHUNK_SIZE=1000          # Her chunk'ın karakter boyutu
CHUNK_OVERLAP=200        # Chunk'lar arası örtüşme

# Models
EMBEDDING_MODEL=models/embedding-001
LLM_MODEL=gemini-pro
TEMPERATURE=0.7          # Yaratıcılık seviyesi (0-1)
MAX_TOKENS=2048          # Maksimum cevap uzunluğu

# Retrieval
TOP_K_RESULTS=4          # Kaç chunk kullanılacak
```

## 🔧 Teknolojiler

- **LangChain**: RAG framework
- **Google Gemini**: Embeddings & LLM
- **FAISS**: Vector similarity search
- **FastAPI**: Modern web framework
- **PyPDF**: PDF processing
- **Pydantic**: Data validation

## 📝 Geliştirme Notları

### Türkçe Dil Desteği
Google Gemini Pro modeli Türkçe dilini mükemmel desteklemektedir. Prompt'lar özellikle Türkçe ders notları için optimize edilmiştir.

### Vector Store Yönetimi
Her PDF için farklı bir vector store oluşturabilir ve `vectorstore_name` parametresi ile yönetebilirsiniz.

### Chunking Stratejisi
RecursiveCharacterTextSplitter kullanılarak dokümanlar mantıklı parçalara ayrılır:
- Önce paragraflar (`\n\n`)
- Sonra satırlar (`\n`)
- Son olarak kelimeler (` `)

## 📄 Lisans

Bu proje eğitim amaçlıdır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'feat: Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

---

**Geliştirici:** Backend & RAG Pipeline Developer  
**Versiyon:** 1.0.0  
**Framework:** Google Gemini + LangChain + FastAPI

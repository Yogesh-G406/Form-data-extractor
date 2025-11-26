# 🚀 Quick Start Guide - Langfuse Integration Testing

## ✅ Setup Complete!

Your Langfuse credentials are configured:
- **Public Key**: `pk-lf-b09e2b78-8241-45e7-a591-a01d1502e2dd`
- **Secret Key**: `sk-lf-e25ec2f8-c0f8-4afe-aa10-1cf846143a08`
- **Host**: `https://cloud.langfuse.com`

---

## 🏃 How to Run and Test

### Option 1: Automated Test Script (Recommended)

**Backend is already running on port 8001!** ✅

Run the test script:
```powershell
cd C:\Users\Aseuro\Downloads\HandwrittenFormAI\HandwrittenFormAI\backend
.\venv312\Scripts\Activate.ps1
python test_langfuse.py
```

This will:
- ✅ Check backend health
- ✅ Upload a test image
- ✅ Trigger Langfuse event tracking
- ✅ Show you what to look for in Langfuse dashboard

---

### Option 2: Manual Testing via Frontend

#### Step 1: Start Frontend (in a new terminal)

```powershell
cd C:\Users\Aseuro\Downloads\HandwrittenFormAI\HandwrittenFormAI\frontend
npm run dev
```

#### Step 2: Open Browser

Navigate to: `http://localhost:5000`

#### Step 3: Test User Flow

1. **Upload a file** → Triggers: `file_selected`, `api_call`, `upload_success`
2. **Switch tabs** → Triggers: `navigation`
3. **Change view mode** → Triggers: `view_mode_change`
4. **Download JSON/CSV** → Triggers: `download`
5. **Copy data** → Triggers: `copy`

---

## 📊 Verify in Langfuse Dashboard

### Access Dashboard
🔗 **https://cloud.langfuse.com**

### What to Look For

#### 1. **Traces** Tab
Look for these traces:
- `handwriting_extraction` - OCR processing with nested generations
  - Contains: `ocr_extraction` generation
  - Contains: `translation` generation (if non-English)
- `api_request_POST_/upload` - File upload request
- `api_request_GET_/forms` - Form retrieval

#### 2. **Events** Tab
Look for these events:
- `file_upload` - File upload metadata
- `form_created` - Database save confirmation
- `file_selected` - Frontend file selection
- `api_call` - Frontend API calls with timing
- `navigation` - Tab changes
- `view_mode_change` - View switches
- `download` - JSON/CSV downloads
- `copy` - Copy actions

#### 3. **Generations** Tab
Look for:
- `ocr_extraction` - HuggingFace vision model calls
- `translation` - Groq translation calls

---

## 🔍 Event Details to Check

### Backend Events

**File Upload Event**:
```json
{
  "name": "file_upload",
  "metadata": {
    "filename": "img6.jpg",
    "file_type": ".jpg",
    "file_size_bytes": 123456,
    "language": "English"
  }
}
```

**Handwriting Extraction Trace**:
```json
{
  "name": "handwriting_extraction",
  "metadata": {
    "filename": "img6.jpg",
    "language": "English",
    "image_size": {"width": 800, "height": 600},
    "model": "Qwen/Qwen2.5-VL-7B-Instruct",
    "duration_seconds": 2.5,
    "fields_extracted": 10
  }
}
```

### Frontend Events

**API Call Event**:
```json
{
  "name": "api_call",
  "metadata": {
    "endpoint": "/api/upload",
    "method": "POST",
    "status": 200,
    "duration_ms": 2500,
    "filename": "img6.jpg"
  }
}
```

**Navigation Event**:
```json
{
  "name": "navigation",
  "metadata": {
    "from": "upload",
    "to": "forms",
    "action": "tab_change"
  }
}
```

---

## 🐛 Troubleshooting

### Backend Not Showing Events?

1. **Check console output** for Langfuse initialization:
   ```
   [OK] Langfuse client initialized
   ```

2. **Verify environment variables** in `backend/.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-b09e2b78-8241-45e7-a591-a01d1502e2dd
   LANGFUSE_SECRET_KEY=sk-lf-e25ec2f8-c0f8-4afe-aa10-1cf846143a08
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **Restart backend** to reload environment variables

### Frontend Not Showing Events?

1. **Check browser console** for Langfuse initialization:
   ```
   [OK] Langfuse client initialized
   ```

2. **Verify environment variables** in `frontend/.env`:
   ```bash
   VITE_LANGFUSE_PUBLIC_KEY=pk-lf-b09e2b78-8241-45e7-a591-a01d1502e2dd
   VITE_LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **Restart frontend** (Vite needs restart for env var changes)

### Events Not Appearing in Dashboard?

- **Wait 10-30 seconds** - Events are sent asynchronously
- **Check network tab** - Verify requests to `cloud.langfuse.com`
- **Verify API keys** - Ensure they're correct in Langfuse dashboard

---

## 📈 What You Can Track

### User Behavior
- Page loads and session duration
- Navigation patterns
- Feature usage (downloads, copies, view modes)
- Error rates and types

### System Performance
- API response times
- LLM processing duration
- File upload sizes and types
- Database operation success rates

### Business Metrics
- Total uploads per day
- Most common languages
- Average fields extracted
- User retention and engagement

---

## 🎯 Next Steps

1. ✅ **Run the test script** to verify integration
2. ✅ **Check Langfuse dashboard** for events
3. ✅ **Test the frontend** for user interaction tracking
4. 📊 **Set up dashboards** in Langfuse for your metrics
5. 🔔 **Configure alerts** for errors or performance issues
6. 📈 **Analyze data** to optimize your application

---

## 📝 Quick Commands Reference

```powershell
# Start Backend (already running on port 8001)
cd backend
.\venv312\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start Frontend
cd frontend
npm run dev

# Run Test Script
cd backend
.\venv312\Scripts\Activate.ps1
python test_langfuse.py

# Run Playwright Tests
cd ..
pytest backend/test_example.py -v
```

---

## 🎉 Success Indicators

You'll know it's working when you see:

✅ Console shows `[OK] Langfuse client initialized`  
✅ Events appear in Langfuse dashboard within 30 seconds  
✅ Traces show nested generations for LLM calls  
✅ Metadata is populated with relevant information  
✅ No errors in console or network tab  

---

**Happy Tracking! 🚀**

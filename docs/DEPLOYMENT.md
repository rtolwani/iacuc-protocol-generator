# Deployment Guide

This guide covers deploying the IACUC Protocol Generator to production.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Vercel      │     │  Railway/Render │     │   ChromaDB      │
│   (Frontend)    │────▶│   (Backend)     │────▶│  (Vector DB)    │
│   Next.js App   │     │  FastAPI + AI   │     │  Embedded       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Anthropic API  │
                        │  OpenAI API     │
                        └─────────────────┘
```

---

## Step 1: Deploy Backend (Railway - Recommended)

### Option A: Railway (Recommended)

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Initialize in project root
   cd /path/to/iacuc-protocol-generator
   railway init
   ```

3. **Configure Environment Variables**
   
   In Railway dashboard, add these environment variables:
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   ENVIRONMENT=production
   ```

4. **Deploy**
   ```bash
   railway up
   ```

5. **Get Your Backend URL**
   - Railway will provide a URL like: `https://iacuc-api-production.up.railway.app`
   - Test it: `https://YOUR_URL/health`

### Option B: Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your repository
   - Render will auto-detect settings from `render.yaml`

3. **Configure Environment Variables**
   ```
   ANTHROPIC_API_KEY=your_key
   OPENAI_API_KEY=your_key
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

---

## Step 2: Deploy Frontend (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy Frontend**
   ```bash
   cd frontend
   vercel
   ```

4. **Configure Environment Variable**
   
   When prompted, or in Vercel dashboard:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app/api/v1
   ```

5. **Production Deployment**
   ```bash
   vercel --prod
   ```

---

## Step 3: Configure CORS

Update your backend to allow your Vercel domain.

In `src/api/app.py`, the CORS is already configured to allow all origins in development. For production, update:

```python
# In src/api/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://your-custom-domain.com",  # If using custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Environment Variables Reference

### Backend (Railway/Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `OPENAI_API_KEY` | Yes | Your OpenAI API key (for embeddings) |
| `ENVIRONMENT` | No | Set to `production` |
| `PORT` | Auto | Provided by platform |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL (with `/api/v1`) |

---

## Knowledge Base Considerations

The RAG knowledge base (ChromaDB) is currently stored locally. For production:

### Option 1: Embedded with Backend (Simple)
- Include PDFs in deployment
- ChromaDB persists in the container
- **Limitation**: Data resets on redeploy

### Option 2: Persistent Storage (Recommended)
- Use Railway's volume feature
- Or use a hosted ChromaDB service
- Data persists across deploys

### Option 3: Pre-built Index
- Build ChromaDB index locally
- Upload to cloud storage (S3, GCS)
- Download on backend startup

---

## Deployment Checklist

### Before Deploying

- [ ] All tests passing (`pytest`)
- [ ] Environment variables documented
- [ ] CORS configured for production domains
- [ ] API keys are set (not committed to repo)
- [ ] Knowledge base PDFs ready

### Backend Deployment

- [ ] Railway/Render project created
- [ ] Environment variables set
- [ ] Deployed successfully
- [ ] Health check passing (`/health`)
- [ ] API docs accessible (`/docs`)

### Frontend Deployment

- [ ] Vercel project created
- [ ] `NEXT_PUBLIC_API_URL` set to backend URL
- [ ] Deployed to Vercel
- [ ] Can reach home page
- [ ] API calls working

### Post-Deployment

- [ ] Test protocol creation flow
- [ ] Test review dashboard
- [ ] Monitor for errors
- [ ] Set up alerts (optional)

---

## Troubleshooting

### "Connection Refused" on Frontend

- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is running (`/health` endpoint)
- Check CORS allows your frontend domain

### Backend Deployment Fails

- Check logs in Railway/Render dashboard
- Verify all dependencies are in `pyproject.toml`
- Ensure Python version is 3.11+

### API Keys Not Working

- Verify keys are set in deployment environment
- Keys should NOT have quotes around them
- Check API key permissions/limits

### ChromaDB Issues

- Ensure sufficient memory (min 512MB)
- Check disk space for vector storage
- Consider using persistent volumes

---

## Estimated Costs

| Service | Free Tier | Paid |
|---------|-----------|------|
| Vercel | Yes (hobby) | $20/mo (pro) |
| Railway | $5 credit/mo | ~$5-20/mo |
| Render | Yes (limited) | $7/mo |
| Anthropic API | Pay per use | ~$0.003/1K tokens |
| OpenAI API | Pay per use | ~$0.0001/1K tokens |

---

## Quick Deploy Commands

```bash
# Backend to Railway
cd /path/to/iacuc-protocol-generator
railway up

# Frontend to Vercel
cd frontend
vercel --prod

# View logs
railway logs
vercel logs
```

---

## Support

If you encounter issues:
1. Check the logs on Railway/Render/Vercel dashboards
2. Verify environment variables are set
3. Test the backend `/health` endpoint directly
4. Check browser console for frontend errors

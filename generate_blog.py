#!/usr/bin/env python3
from __future__ import annotations

"""
Saif Modan — Automated Daily Blog Publisher
Generates daily technical articles on AI, Python, FastAPI, Automation, and Engineering
using Gemini Flash, DashScope Qwen-Image, and Pollinations.ai fallback.
"""

import os
import sys
import json
import re
import random
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Union
import requests
import markdown

try:
    import dashscope  # type: ignore
    from dashscope import ImageSynthesis  # type: ignore
except Exception:
    dashscope = None
    ImageSynthesis = None

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SITE_URL = "https://saif-portfolio-seven-sigma.vercel.app"
AUTHOR_NAME = "Saif Modan"
AUTHOR_EMAIL = "saifmodan000@gmail.com"
AUTHOR_ROLE = "AI Developer & Python Engineer"
AUTHOR_IMAGE = "assets/og-image.png"

# Root and subdirectories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(BASE_DIR, "blog")
ASSETS_BLOG_DIR = os.path.join(BASE_DIR, "assets", "blog")
POSTS_JSON_PATH = os.path.join(BLOG_DIR, "posts.json")
SITEMAP_PATH = os.path.join(BASE_DIR, "sitemap.xml")
BLOG_INDEX_PATH = os.path.join(BASE_DIR, "blog.html")


def ensure_directories():
    """Ensure necessary output folders exist."""
    os.makedirs(BLOG_DIR, exist_ok=True)
    os.makedirs(ASSETS_BLOG_DIR, exist_ok=True)


def calculate_reading_time(text: str) -> int:
    """Calculate approximate reading time in minutes (200 WPM)."""
    words = len(re.findall(r'\w+', text))
    return max(1, round(words / 200))


def load_existing_posts():
    """Load existing posts from posts.json manifest."""
    if os.path.exists(POSTS_JSON_PATH):
        try:
            with open(POSTS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Error reading {POSTS_JSON_PATH}: {e}")
            return []
    return []


def save_posts_manifest(posts):
    """Save posts array to posts.json manifest."""
    with open(POSTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


import time

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest",
]


def call_gemini_api(api_key: str, niche: str, past_titles: list) -> dict:
    """Generate article payload using Gemini API with resilient model fallback and retry."""
    print("[INFO] Calling Gemini API for blog generation...", flush=True)
    
    past_topics_summary = ", ".join(past_titles[-15:]) if past_titles else "None yet"
    
    prompt = f"""You are Saif Modan, an expert AI Developer, Python Engineer, and Data Analytics specialist based in Ahmedabad, India.
Write an in-depth, authoritative, practical technical blog post for your engineering portfolio.

Target Domain / Niche: {niche}
Previously covered topics (DO NOT repeat these topics or concepts directly):
{past_topics_summary}

Requirements:
1. Title: Engaging, clear, technical, professional (e.g., "Building High-Throughput Async Pipelines with FastAPI and Redis", "Optimizing Vision Transformers for Edge Deployment").
2. Slug: URL-safe kebab-case string (lowercase, letters, numbers, hyphens only, no symbols, max 60 chars).
3. Meta Description: Compelling SEO meta description under 155 characters.
4. Tags: Array of 3-5 relevant technical tags (e.g., ["Python", "FastAPI", "AI Engineering", "Performance"]).
5. Content: In-depth technical article in Markdown format. Minimum 650+ words.
   - Start directly with a strong introductory section explaining the problem and real-world relevance.
   - Use '##' and '###' headings to structure key sections.
   - Include realistic code examples with syntax formatting (e.g. ```python ... ```).
   - Provide architectural insights, performance trade-offs, practical tips, and a thoughtful conclusion.
   - Tone: Pragmatic, professional, insightful, developer-focused.
6. Image Prompt: A concrete, high-detail visual description (15-25 words) depicting real physical tech, servers, microchips, data conduits, or hardware specific to the topic (e.g., "photorealistic 3d render of distributed high performance server racks, fiber optic conduits, futuristic hardware microchips, dark cinematic lighting"). Strictly avoid generic abstract glowing spheres, blobs, bowls, or floating crystals. IMPORTANT: Strictly NO text, NO typography, NO letters, NO words in the image.

Output ONLY valid JSON matching this schema:
{{
  "title": "string",
  "slug": "string",
  "metaDescription": "string",
  "tags": ["string"],
  "content": "string",
  "imagePrompt": "string"
}}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
            "topP": 0.95
        }
    }

    headers = {"Content-Type": "application/json"}
    last_error = None

    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        print(f"[INFO] Attempting generation with model '{model_name}'...", flush=True)
        for attempt in range(1, 4):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    res_data = response.json()
                    candidates = res_data.get("candidates", [])
                    if not candidates:
                        raise ValueError(f"No candidates returned in response: {res_data}")
                    raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                    data = json.loads(raw_text)
                    
                    # Sanitize slug
                    slug = re.sub(r'[^a-z0-9\-]', '', data.get("slug", "").lower().replace(" ", "-")).strip('-')
                    if not slug:
                        slug = re.sub(r'[^a-z0-9\-]', '', data.get("title", "").lower().replace(" ", "-")).strip('-')
                    data["slug"] = slug
                    
                    # Validate essential fields
                    for field in ["title", "slug", "metaDescription", "tags", "content"]:
                        if not data.get(field):
                            raise ValueError(f"Missing required field in Gemini response: {field}")
                    
                    print(f"[SUCCESS] Article successfully generated using '{model_name}'.", flush=True)
                    return data
                elif response.status_code in [429, 500, 503]:
                    backoff = attempt * 3
                    print(f"[WARN] Model '{model_name}' returned HTTP {response.status_code} (attempt {attempt}/3). Retrying in {backoff}s...", flush=True)
                    last_error = response.text
                    time.sleep(backoff)
                else:
                    err_snippet = response.text[:160].replace("\n", " ")
                    print(f"[WARN] Model '{model_name}' returned HTTP {response.status_code}: {err_snippet}", flush=True)
                    last_error = response.text
                    break
            except Exception as e:
                print(f"[WARN] Attempt {attempt} error with model '{model_name}': {e}", flush=True)
                last_error = str(e)
                time.sleep(2)
            
    print(f"[ERROR] All candidate Gemini models failed. Last error: {last_error}", file=sys.stderr, flush=True)
    sys.exit(1)


def generate_cover_image_gemini(prompt: str, slug: str, api_key: str) -> Optional[str]:
    """Generate cover image using Google Gemini Image generation models via GEMINI_API_KEY."""
    if not api_key:
        return None

    output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}-cover.png")
    jpg_output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}.jpg")
    relative_path = f"assets/blog/{slug}-cover.png"

    clean_prompt = prompt if prompt else "photorealistic 3d render of distributed high performance server racks, fiber optic conduits, futuristic hardware microchips, dark cinematic lighting"
    full_prompt = (
        f"{clean_prompt}. 16:9 widescreen aspect ratio, highly detailed photorealistic render of technology, "
        f"microchips, server infrastructure, clean cinematic lighting, no text, no watermark, 8k resolution."
    )

    candidate_image_models = [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3-pro-image",
    ]

    print(f"[INFO] Generating cover image via Gemini Image API for '{slug}'...", flush=True)

    for model_name in candidate_image_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }

        try:
            print(f"[INFO] Attempting Gemini Image model '{model_name}'...", flush=True)
            resp = requests.post(url, json=payload, timeout=35, headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        inline_data = part.get("inlineData", {})
                        b64_data = inline_data.get("data")
                        if b64_data:
                            import base64
                            img_bytes = base64.b64decode(b64_data)
                            with open(output_path, "wb") as f:
                                f.write(img_bytes)
                            try:
                                with open(jpg_output_path, "wb") as f_jpg:
                                    f_jpg.write(img_bytes)
                            except Exception:
                                pass
                            print(f"[SUCCESS] Gemini cover image saved to {output_path} ({len(img_bytes)} bytes)", flush=True)
                            return relative_path
                print(f"[WARN] Gemini Image '{model_name}' response did not contain image data.", flush=True)
            else:
                err_text = resp.text[:180].replace("\n", " ")
                print(f"[WARN] Gemini Image model '{model_name}' returned HTTP {resp.status_code}: {err_text}", flush=True)
        except Exception as e:
            print(f"[WARN] Error with Gemini Image model '{model_name}': {e}", flush=True)

    return None


def generate_cover_image_qwen(prompt: str, slug: str) -> Optional[str]:
    """Generate cover image using Alibaba DashScope Qwen-Image model (qwen-image-plus)."""
    if dashscope is None or ImageSynthesis is None:
        return None

    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        return None

    dashscope.api_key = api_key
    workspace_id = os.environ.get("DASHSCOPE_WORKSPACE_ID", "").strip()
    if workspace_id:
        dashscope.base_http_api_url = f"https://{workspace_id}.ap-southeast-1.maas.aliyuncs.com/api/v1"
    else:
        dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

    output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}-cover.png")
    jpg_output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}.jpg")
    relative_path = f"assets/blog/{slug}-cover.png"

    clean_prompt = prompt if prompt else "photorealistic 3d render of distributed high performance server racks, fiber optic conduits, futuristic hardware microchips, dark cinematic lighting"
    print(f"[INFO] Generating cover image via DashScope Qwen-Image for '{slug}'...", flush=True)

    for attempt in range(1, 3):
        try:
            print(f"[INFO] Qwen-Image generation attempt {attempt}/2...", flush=True)
            response = ImageSynthesis.call(
                model="qwen-image-plus",
                prompt=clean_prompt,
                negative_prompt="low resolution, blurry, distorted text, watermark, logo, abstract glowing sphere",
                n=1,
                size="1664*928",
                prompt_extend=True,
                watermark=False
            )

            status_code = getattr(response, "status_code", None)
            if status_code == 200:
                output = getattr(response, "output", None)
                results = getattr(output, "results", None)
                if results is None and isinstance(output, dict):
                    results = output.get("results")

                if results and len(results) > 0:
                    first_res = results[0]
                    image_url = getattr(first_res, "url", None) or (first_res.get("url") if isinstance(first_res, dict) else None)
                    if image_url:
                        print(f"[INFO] Qwen-Image generated URL successfully. Downloading immediately...", flush=True)
                        img_resp = requests.get(image_url, timeout=30)
                        if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            try:
                                with open(jpg_output_path, "wb") as f_jpg:
                                    f_jpg.write(img_resp.content)
                            except Exception:
                                pass
                            print(f"[SUCCESS] Qwen cover image saved to {output_path} ({len(img_resp.content)} bytes)", flush=True)
                            return relative_path
                        else:
                            print(f"[WARN] Failed to download image from Qwen URL (HTTP {img_resp.status_code})", flush=True)
                else:
                    print(f"[WARN] Qwen response did not contain image results: {output}", flush=True)
            else:
                msg = getattr(response, "message", str(response))
                print(f"[WARN] Qwen-Image returned HTTP status {status_code}: {msg}", flush=True)
                if attempt < 2:
                    time.sleep(2)
        except Exception as e:
            print(f"[WARN] Attempt {attempt} error during Qwen image generation: {e}", flush=True)
            if attempt < 2:
                time.sleep(2)

    return None


def download_cover_image(image_prompt: str, slug: str) -> str:
    """Download cover image from Pollinations.ai with graceful fallback."""
    print(f"[INFO] Generating cover image for '{slug}' via Pollinations.ai fallback...", flush=True)
    
    clean_prompt = image_prompt if image_prompt else "photorealistic 3d render of distributed high performance server racks, fiber optic conduits, futuristic hardware microchips, dark cinematic lighting"
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = random.randint(10000, 999999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&seed={seed}&nologo=true"
    
    output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}-cover.png")
    jpg_output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}.jpg")
    relative_path = f"assets/blog/{slug}-cover.png"
    
    # Try up to 2 times with 15s timeout
    for attempt in range(1, 3):
        try:
            print(f"[INFO] Pollinations download attempt {attempt}/2...", flush=True)
            resp = requests.get(image_url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200 and len(resp.content) > 2000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                try:
                    with open(jpg_output_path, "wb") as f_jpg:
                        f_jpg.write(resp.content)
                except Exception:
                    pass
                print(f"[SUCCESS] Cover image saved to {output_path} ({len(resp.content)} bytes)", flush=True)
                return relative_path
            else:
                print(f"[WARN] Pollinations attempt {attempt} returned status {resp.status_code}", flush=True)
        except Exception as e:
            print(f"[WARN] Pollinations attempt {attempt} failed: {e}", flush=True)
            
    # Fallback to og-image banner
    print("[WARN] Pollinations.ai image download timed out/failed. Using fallback banner.", flush=True)
    fallback_source = os.path.join(BASE_DIR, "assets", "og-image.png")
    if os.path.exists(fallback_source):
        with open(fallback_source, "rb") as src:
            banner_data = src.read()
        with open(output_path, "wb") as dst:
            dst.write(banner_data)
        try:
            with open(jpg_output_path, "wb") as dst_jpg:
                dst_jpg.write(banner_data)
        except Exception:
            pass
        print(f"[SUCCESS] Fallback cover image created at {output_path}", flush=True)
    return relative_path


def generate_cover_image(image_prompt: str, slug: str, gemini_api_key: Optional[str] = None) -> str:
    """Generate cover image: try Gemini Image first, then Qwen-Image, then Pollinations.ai, then fallback banner."""
    api_key = (gemini_api_key or os.environ.get("GEMINI_API_KEY", "")).strip()

    # 1. Primary: Try Gemini Image Generation via GEMINI_API_KEY
    if api_key:
        try:
            gemini_img = generate_cover_image_gemini(image_prompt, slug, api_key)
            if gemini_img:
                return gemini_img
        except Exception as e:
            print(f"[WARN] Error during Gemini Image generation: {e}", flush=True)

    # 2. Secondary: Try Qwen-Image via DashScope if key is configured
    try:
        qwen_img = generate_cover_image_qwen(image_prompt, slug)
        if qwen_img:
            return qwen_img
    except Exception as e:
        print(f"[WARN] Error during Qwen-Image generation: {e}", flush=True)

    # 3. Tertiary: Fall back to Pollinations.ai
    print("[INFO] Falling back to Pollinations.ai for cover image...", flush=True)
    try:
        pollinations_img = download_cover_image(image_prompt, slug)
        if pollinations_img:
            return pollinations_img
    except Exception as e:
        print(f"[WARN] Error during Pollinations.ai generation: {e}", flush=True)

    # 4. Last-resort fallback to default banner
    print("[WARN] All cover image generators failed. Using default banner.", flush=True)
    fallback_source = os.path.join(BASE_DIR, "assets", "og-image.png")
    output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}-cover.png")
    jpg_output_path = os.path.join(ASSETS_BLOG_DIR, f"{slug}.jpg")
    relative_path = f"assets/blog/{slug}-cover.png"
    if os.path.exists(fallback_source):
        with open(fallback_source, "rb") as src:
            banner_data = src.read()
        with open(output_path, "wb") as dst:
            dst.write(banner_data)
        try:
            with open(jpg_output_path, "wb") as dst_jpg:
                dst_jpg.write(banner_data)
        except Exception:
            pass
        return relative_path
    return "assets/og-image.png"


def render_post_html(post: dict, html_content: str) -> str:
    """Generate standalone HTML for an individual blog post."""
    slug = post["slug"]
    title = post["title"]
    description = post["metaDescription"]
    tags = post.get("tags", ["AI", "Python"])
    date_str = post["date"]
    reading_time = post.get("readingTime", "5 min read")
    image_rel = f"../{post['image']}"
    og_image_url = f"{SITE_URL}/{post['image']}"
    canonical_url = f"{SITE_URL}/blog/{slug}.html"
    
    tags_html = "".join([f'<span class="blog-tag-pill">{t}</span>' for t in tags])
    tags_json = json.dumps(tags)
    
    # JSON-LD BlogPosting schema
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "image": [og_image_url],
        "datePublished": date_str,
        "dateModified": date_str,
        "author": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": SITE_URL,
            "jobTitle": AUTHOR_ROLE
        },
        "publisher": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": SITE_URL
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url
        },
        "keywords": ", ".join(tags)
    }, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <title>{title} | Saif Modan</title>
  <meta name="description" content="{description}">
  <meta name="keywords" content="{', '.join(tags)}, Saif Modan, AI Developer, Python Engineer">
  <meta name="author" content="{AUTHOR_NAME}">
  <meta name="application-name" content="{AUTHOR_NAME}">
  <meta name="apple-mobile-web-app-title" content="{AUTHOR_NAME}">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
  <link rel="canonical" href="{canonical_url}">
  <link rel="manifest" href="../manifest.webmanifest">
  <meta name="theme-color" content="#09090b">

  <!-- Open Graph / Social -->
  <meta property="og:title" content="{title} | Saif Modan">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:site_name" content="Saif Modan">
  <meta property="og:image" content="{og_image_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{title}">
  <meta property="article:published_time" content="{date_str}">
  <meta property="article:author" content="{AUTHOR_NAME}">

  <!-- Twitter / X Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@modan_saif55342">
  <meta name="twitter:creator" content="@modan_saif55342">
  <meta name="twitter:title" content="{title} | Saif Modan">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image_url}">

  <!-- Schema.org BlogPosting Structured Data -->
  <script type="application/ld+json">
{schema_json}
  </script>

  <!-- Vercel Web Analytics & Speed Insights -->
  <script defer src="/_vercel/insights/script.js"></script>
  <script defer src="/_vercel/speed-insights/script.js"></script>

  <!-- Favicons -->
  <link rel="icon" type="image/x-icon" href="../favicon.ico">
  <link rel="icon" type="image/png" sizes="48x48" href="../assets/icon-48.png">
  <link rel="icon" type="image/png" sizes="96x96" href="../assets/icon-96.png">
  <link rel="icon" type="image/png" sizes="192x192" href="../assets/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/apple-touch-icon.png">
  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">

  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/blog.css">
</head>

<body class="blog-post-page-body">

  <!-- Scroll Progress Bar -->
  <div class="scroll-progress-bar" id="scroll-progress"></div>

  <!-- Global Header Navigation -->
  <header class="site-header" id="site-header">
    <div class="container-xl">
      <nav class="header-nav">

        <!-- Brand Logo / Name -->
        <a href="../index.html" class="brand-logo" aria-label="Saif Modan Home">
          <span style="font-size: 0.88rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;">SAIF MODAN</span>
        </a>

        <!-- Right Header Actions -->
        <div class="header-actions">
          <!-- Live Time & Date Header Clock Widget -->
          <div class="header-clock-widget" id="header-clock" title="Current Local Time (IST)">
            <svg class="clock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span id="clock-time">--:--:-- --</span>
            <span class="clock-divider">|</span>
            <span id="clock-date">--- --, ----</span>
          </div>

          <!-- Ask AI Modal Trigger Button -->
          <button id="open-ai-modal" class="btn-ask-ai" aria-label="Ask AI Assistant">
            <span class="btn-ask-ai-text">ASK AI</span>
            <svg class="btn-ask-ai-sparkle" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-3.01L12 0z" />
            </svg>
          </button>

          <!-- Hamburger Menu Button -->
          <button id="open-menu-drawer" class="btn-menu" aria-label="Open navigation menu">
            <span class="menu-label">MENU</span>
            <div class="hamburger-icon">
              <div class="bar bar-1"></div>
              <div class="bar bar-2"></div>
            </div>
          </button>
        </div>

      </nav>
    </div>
  </header>

  <!-- Main Article Container -->
  <main class="blog-post-main">
    <div class="container-xl">
      <article class="blog-article-wrapper">

        <!-- Back Link Navigation -->
        <div class="blog-back-nav">
          <a href="../blog.html" class="blog-back-link">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            <span>All Articles</span>
          </a>
        </div>

        <!-- Article Header -->
        <header class="blog-article-header">
          <div class="blog-article-tags">
            {tags_html}
          </div>
          <h1 class="blog-article-title">{title}</h1>

          <div class="blog-article-meta-bar">
            <div class="blog-author-mini">
              <div class="author-info-text">
                <span class="author-name-title">{AUTHOR_NAME}</span>
                <span class="author-role-sub">{AUTHOR_ROLE}</span>
              </div>
            </div>
            <div class="blog-article-stats">
              <span>{date_str}</span>
              <span>•</span>
              <span>{reading_time}</span>
            </div>
          </div>
        </header>

        <!-- Featured Cover Image -->
        <div class="blog-article-cover-wrap">
          <img src="{image_rel}" alt="{title}" class="blog-article-cover-img" loading="eager">
        </div>

        <!-- Article Body Content -->
        <div class="blog-article-content">
          {html_content}
        </div>

        <!-- Author Bio Card at Bottom -->
        <div class="blog-post-author-box">
          <div class="author-box-details">
            <span class="author-box-kicker">WRITTEN BY</span>
            <h3 class="author-box-name">{AUTHOR_NAME}</h3>
            <p class="author-box-bio">
              AI Developer and Python Engineer specializing in Generative AI, Video Diffusion, FastAPI microservices, and Data Analytics. Based in Ahmedabad, India.
            </p>
            <div class="author-box-links">
              <a href="../contact.html">Get in Touch →</a>
              <a href="https://github.com/saifmodan2006" target="_blank" rel="noopener noreferrer">GitHub</a>
              <a href="https://www.linkedin.com/in/saif-modan" target="_blank" rel="noopener noreferrer">LinkedIn</a>
              <a href="https://x.com/modan_saif55342" target="_blank" rel="noopener noreferrer">X (Twitter)</a>
            </div>
          </div>
        </div>

        <!-- Bottom Navigation -->
        <div class="blog-bottom-nav">
          <a href="../blog.html" class="blog-back-link">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            <span>Back to All Articles</span>
          </a>
          <a href="../contact.html" class="blog-back-link">
            <span>Discuss This Topic with Saif →</span>
          </a>
        </div>

      </article>
    </div>
  </main>

  <!-- Site Footer -->
  <footer class="site-footer" id="contact">
    <div class="container-xl">
      <div class="footer-cta-block">
        <h2 class="footer-cta-title">
          Let’s build something extraordinary together.
        </h2>
        <div class="footer-email-row">
          <a href="mailto:{AUTHOR_EMAIL}" class="btn-large-email">
            <span>{AUTHOR_EMAIL}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="7" y1="17" x2="17" y2="7"></line>
              <polyline points="7 7 17 7 17 17"></polyline>
            </svg>
          </a>
          <a href="tel:+919824785082" class="btn-large-phone" title="Call Saif Modan">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            <span>+91 98247 85082</span>
          </a>
        </div>
      </div>

      <div class="footer-bottom-bar">
        <div>
          <span>Saif Modan © 2026</span>
          <span style="margin: 0 0.5rem;">•</span>
          <span>Ahmedabad, India (IST)</span>
        </div>
        <div class="footer-social-links">
          <a href="https://github.com/saifmodan2006" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/saif-modan" target="_blank" rel="noopener noreferrer">LinkedIn</a>
          <a href="https://x.com/modan_saif55342" target="_blank" rel="noopener noreferrer">X (Twitter)</a>
          <a href="mailto:{AUTHOR_EMAIL}">Email</a>
          <a href="tel:+919824785082" style="color: var(--text-main); font-weight: 700;">+91 98247 85082</a>
        </div>
      </div>
    </div>
  </footer>

  <!-- Navigation Menu Drawer -->
  <div id="menu-drawer" class="menu-drawer-overlay" role="dialog" aria-modal="true">
    <div class="menu-drawer-card">
      <div>
        <div class="drawer-header">
          <span style="font-weight: 800; font-size: 1.1rem;">NAVIGATION</span>
          <button id="close-menu-drawer" class="btn-close-modal" aria-label="Close menu">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <ul class="drawer-nav-list">
          <li><a href="../index.html#hero" class="drawer-nav-link menu-link"><span>01</span><span>Home</span></a></li>
          <li><a href="../blog.html" class="drawer-nav-link menu-link" style="color: var(--text-main); font-weight: 800;"><span>02</span><span>Blog</span></a></li>
          <li><a href="../index.html#work" class="drawer-nav-link menu-link"><span>03</span><span>Selected Work</span></a></li>
          <li><a href="../assets/Saif_Modan_Resume.pdf" target="_blank" rel="noopener noreferrer" class="drawer-nav-link" style="color: var(--text-main); font-weight: 800;"><span>04</span><span>My Resume ↗</span></a></li>
          <li><a href="../index.html#experience" class="drawer-nav-link menu-link"><span>05</span><span>Experience</span></a></li>
          <li><a href="../index.html#toolbox" class="drawer-nav-link menu-link"><span>06</span><span>Tech Stack</span></a></li>
          <li><a href="../index.html#credentials" class="drawer-nav-link menu-link"><span>07</span><span>Education</span></a></li>
          <li><a href="../contact.html" class="drawer-nav-link menu-link"><span>08</span><span>Contact</span></a></li>
        </ul>
      </div>

      <div class="drawer-footer-actions">
        <a href="tel:+919824785082" class="drawer-btn" style="text-decoration: none;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          </svg>
          <span>Call: +91 98247 85082</span>
        </a>
      </div>
    </div>
  </div>

  <!-- Interactive "Ask Saif AI" Assistant Modal -->
  <div id="ai-modal" class="ai-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ai-modal-title">
    <div class="ai-modal-card">
      <div class="ai-modal-header">
        <div class="ai-modal-title" id="ai-modal-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10a9.96 9.96 0 0 1-4.78-1.22L2 22l1.22-5.22A9.96 9.96 0 0 1 2 12C2 6.477 6.477 2 12 2z" />
          </svg>
          <span>Ask Saif AI</span>
        </div>
        <button id="close-ai-modal" class="btn-close-modal" aria-label="Close AI Assistant">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="ai-chat-body" id="ai-chat-body">
        <div class="chat-bubble assistant">
          Hello! I’m Saif's AI portfolio assistant. Ask me anything about this blog post, Saif’s projects, technical skills in Python/AI, work experience, or availability!
        </div>
      </div>

      <form class="ai-input-form" id="ai-input-form">
        <input type="text" id="ai-input-field" class="ai-input-field" placeholder="Ask a question about Saif..." autocomplete="off" required>
        <button type="submit" class="ai-send-btn" aria-label="Send message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  </div>

  <script src="../js/app.js"></script>
</body>

</html>
"""


def generate_blog_index_html(posts: list) -> str:
    """Generate the blog.html listing page."""
    cards_html = []
    
    for p in posts:
        slug = p["slug"]
        title = p["title"]
        desc = p["metaDescription"]
        date_str = p.get("date", "")
        reading_time = p.get("readingTime", "5 min read")
        tags = p.get("tags", ["AI"])
        primary_tag = tags[0] if tags else "AI"
        image_path = p.get("image", "assets/og-image.png")
        
        cards_html.append(f"""
        <article class="blog-card" data-reveal>
          <a href="blog/{slug}.html" class="blog-card-thumbnail-wrap" aria-label="{title}">
            <img src="{image_path}" alt="{title}" class="blog-card-thumbnail" loading="lazy">
            <span class="blog-card-tag-badge">{primary_tag}</span>
          </a>
          <div class="blog-card-body">
            <div class="blog-card-meta">
              <span>{date_str}</span>
              <span class="meta-dot">•</span>
              <span>{reading_time}</span>
            </div>
            <h2 class="blog-card-title">
              <a href="blog/{slug}.html">{title}</a>
            </h2>
            <p class="blog-card-desc">{desc}</p>
            <a href="blog/{slug}.html" class="blog-card-footer">
              <span>Read Article</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </a>
          </div>
        </article>""")

    grid_content = "\n".join(cards_html) if cards_html else "<p>No articles published yet. Check back tomorrow!</p>"
    
    # Schema.org CollectionPage / Blog
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Engineering Blog | Saif Modan",
        "url": f"{SITE_URL}/blog.html",
        "description": "Daily engineering articles, architectural deep dives, and tutorials on AI, Python, FastAPI, and Automation by Saif Modan.",
        "publisher": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "url": SITE_URL
        }
    }, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <title>Engineering Blog & Insights | Saif Modan — AI Developer</title>
  <meta name="description" content="Explore daily engineering deep dives, architecture patterns, and tutorials on AI, Python, FastAPI, Video Diffusion, and Automation by Saif Modan.">
  <meta name="keywords" content="Saif Modan Blog, AI Blog, Python Tutorials, FastAPI Architecture, AI Engineering India, Machine Learning Blog">
  <meta name="author" content="{AUTHOR_NAME}">
  <meta name="application-name" content="{AUTHOR_NAME}">
  <meta name="apple-mobile-web-app-title" content="{AUTHOR_NAME}">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
  <link rel="canonical" href="{SITE_URL}/blog.html">
  <link rel="manifest" href="manifest.webmanifest">
  <meta name="theme-color" content="#09090b">

  <!-- Open Graph / Social -->
  <meta property="og:title" content="Engineering Blog & Insights | Saif Modan">
  <meta property="og:description" content="Explore daily engineering deep dives, architecture patterns, and tutorials on AI, Python, FastAPI, and Automation by Saif Modan.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/blog.html">
  <meta property="og:site_name" content="Saif Modan">
  <meta property="og:image" content="{SITE_URL}/assets/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Engineering Blog | Saif Modan">

  <!-- Twitter / X Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@modan_saif55342">
  <meta name="twitter:creator" content="@modan_saif55342">
  <meta name="twitter:title" content="Engineering Blog & Insights | Saif Modan">
  <meta name="twitter:description" content="Daily technical deep dives on AI, Python, FastAPI, and Automation.">
  <meta name="twitter:image" content="{SITE_URL}/assets/og-image.png">

  <!-- Schema.org CollectionPage Structured Data -->
  <script type="application/ld+json">
{schema_json}
  </script>

  <!-- Vercel Web Analytics & Speed Insights -->
  <script defer src="/_vercel/insights/script.js"></script>
  <script defer src="/_vercel/speed-insights/script.js"></script>

  <!-- Favicons -->
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="icon" type="image/png" sizes="48x48" href="assets/icon-48.png">
  <link rel="icon" type="image/png" sizes="96x96" href="assets/icon-96.png">
  <link rel="icon" type="image/png" sizes="192x192" href="assets/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">

  <link rel="stylesheet" href="css/style.css">
  <link rel="stylesheet" href="css/blog.css">
</head>

<body class="blog-page-body">

  <!-- Scroll Progress Bar -->
  <div class="scroll-progress-bar" id="scroll-progress"></div>

  <!-- Global Header Navigation -->
  <header class="site-header" id="site-header">
    <div class="container-xl">
      <nav class="header-nav">

        <!-- Brand Logo / Name -->
        <a href="index.html" class="brand-logo" aria-label="Saif Modan Home">
          <span style="font-size: 0.88rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;">SAIF MODAN</span>
        </a>

        <!-- Right Header Actions -->
        <div class="header-actions">
          <!-- Live Time & Date Header Clock Widget -->
          <div class="header-clock-widget" id="header-clock" title="Current Local Time (IST)">
            <svg class="clock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span id="clock-time">--:--:-- --</span>
            <span class="clock-divider">|</span>
            <span id="clock-date">--- --, ----</span>
          </div>

          <!-- Ask AI Modal Trigger Button -->
          <button id="open-ai-modal" class="btn-ask-ai" aria-label="Ask AI Assistant">
            <span class="btn-ask-ai-text">ASK AI</span>
            <svg class="btn-ask-ai-sparkle" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-3.01L12 0z" />
            </svg>
          </button>

          <!-- Hamburger Menu Button -->
          <button id="open-menu-drawer" class="btn-menu" aria-label="Open navigation menu">
            <span class="menu-label">MENU</span>
            <div class="hamburger-icon">
              <div class="bar bar-1"></div>
              <div class="bar bar-2"></div>
            </div>
          </button>
        </div>

      </nav>
    </div>
  </header>

  <main class="blog-main-content">
    <div class="container-xl">

      <!-- Page Head Title Block -->
      <div class="blog-page-header" data-reveal>
        <div class="blog-header-left">
          <span class="blog-top-kicker">ENGINEERING JOURNAL</span>
          <h1 class="blog-hero-title">Blog & Insights.</h1>
        </div>
        <div class="blog-header-right">
          <p class="blog-header-serif">
            <em>Daily technical deep dives, architectural breakdowns, and practical guides on AI, Python, and scalable software systems.</em>
          </p>
        </div>
      </div>

      <!-- Articles Grid -->
      <div class="blog-grid">
        {grid_content}
      </div>

    </div>
  </main>

  <!-- Dark Footer CTA Banner -->
  <section class="footer-cta-banner" data-reveal>
    <div class="container-xl">
      <div class="cta-banner-card">
        <div class="cta-banner-text">
          <span class="cta-banner-kicker">LET'S WORK TOGETHER</span>
          <h2 class="cta-banner-title">Have a project in mind?</h2>
          <p class="cta-banner-sub">Let's create something extraordinary.</p>
        </div>
        <a href="contact.html" class="btn-get-in-touch" title="Open Contact Page">
          <span>GET IN TOUCH</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="7" y1="17" x2="17" y2="7"></line>
            <polyline points="7 7 17 7 17 17"></polyline>
          </svg>
        </a>
      </div>
    </div>
  </section>

  <!-- Site Footer -->
  <footer class="site-footer" id="contact">
    <div class="container-xl">
      <div class="footer-cta-block">
        <h2 class="footer-cta-title">
          Let’s build something extraordinary together.
        </h2>
        <div class="footer-email-row">
          <a href="mailto:{AUTHOR_EMAIL}" class="btn-large-email">
            <span>{AUTHOR_EMAIL}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="7" y1="17" x2="17" y2="7"></line>
              <polyline points="7 7 17 7 17 17"></polyline>
            </svg>
          </a>
          <a href="tel:+919824785082" class="btn-large-phone" title="Call Saif Modan">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            <span>+91 98247 85082</span>
          </a>
        </div>
      </div>

      <div class="footer-bottom-bar">
        <div>
          <span>Saif Modan © 2026</span>
          <span style="margin: 0 0.5rem;">•</span>
          <span>Ahmedabad, India (IST)</span>
        </div>
        <div class="footer-social-links">
          <a href="https://github.com/saifmodan2006" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/saif-modan" target="_blank" rel="noopener noreferrer">LinkedIn</a>
          <a href="https://x.com/modan_saif55342" target="_blank" rel="noopener noreferrer">X (Twitter)</a>
          <a href="mailto:{AUTHOR_EMAIL}">Email</a>
          <a href="tel:+919824785082" style="color: var(--text-main); font-weight: 700;">+91 98247 85082</a>
        </div>
      </div>
    </div>
  </footer>

  <!-- Navigation Menu Drawer -->
  <div id="menu-drawer" class="menu-drawer-overlay" role="dialog" aria-modal="true">
    <div class="menu-drawer-card">
      <div>
        <div class="drawer-header">
          <span style="font-weight: 800; font-size: 1.1rem;">NAVIGATION</span>
          <button id="close-menu-drawer" class="btn-close-modal" aria-label="Close menu">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <ul class="drawer-nav-list">
          <li><a href="index.html#hero" class="drawer-nav-link menu-link"><span>01</span><span>Home</span></a></li>
          <li><a href="blog.html" class="drawer-nav-link menu-link" style="color: var(--text-main); font-weight: 800;"><span>02</span><span>Blog</span></a></li>
          <li><a href="index.html#work" class="drawer-nav-link menu-link"><span>03</span><span>Selected Work</span></a></li>
          <li><a href="assets/Saif_Modan_Resume.pdf" target="_blank" rel="noopener noreferrer" class="drawer-nav-link" style="color: var(--text-main); font-weight: 800;"><span>04</span><span>My Resume ↗</span></a></li>
          <li><a href="index.html#experience" class="drawer-nav-link menu-link"><span>05</span><span>Experience</span></a></li>
          <li><a href="index.html#toolbox" class="drawer-nav-link menu-link"><span>06</span><span>Tech Stack</span></a></li>
          <li><a href="index.html#credentials" class="drawer-nav-link menu-link"><span>07</span><span>Education</span></a></li>
          <li><a href="contact.html" class="drawer-nav-link menu-link"><span>08</span><span>Contact</span></a></li>
        </ul>
      </div>

      <div class="drawer-footer-actions">
        <a href="tel:+919824785082" class="drawer-btn" style="text-decoration: none;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          </svg>
          <span>Call: +91 98247 85082</span>
        </a>
      </div>
    </div>
  </div>

  <!-- Interactive "Ask Saif AI" Assistant Modal -->
  <div id="ai-modal" class="ai-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ai-modal-title">
    <div class="ai-modal-card">
      <div class="ai-modal-header">
        <div class="ai-modal-title" id="ai-modal-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10a9.96 9.96 0 0 1-4.78-1.22L2 22l1.22-5.22A9.96 9.96 0 0 1 2 12C2 6.477 6.477 2 12 2z" />
          </svg>
          <span>Ask Saif AI</span>
        </div>
        <button id="close-ai-modal" class="btn-close-modal" aria-label="Close AI Assistant">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="ai-chat-body" id="ai-chat-body">
        <div class="chat-bubble assistant">
          Hello! I’m Saif's AI portfolio assistant. Ask me anything about Saif’s articles, technical skills in Python/AI, work experience, or availability!
        </div>
      </div>

      <form class="ai-input-form" id="ai-input-form">
        <input type="text" id="ai-input-field" class="ai-input-field" placeholder="Ask a question about Saif..." autocomplete="off" required>
        <button type="submit" class="ai-send-btn" aria-label="Send message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  </div>

  <script src="js/app.js"></script>
</body>

</html>
"""


def update_sitemap(new_slug: str, today_str: str):
    """Update sitemap.xml with the blog listing and new blog post entry."""
    print("[INFO] Updating sitemap.xml...")
    
    if not os.path.exists(SITEMAP_PATH):
        print(f"[WARN] {SITEMAP_PATH} not found. Skipping sitemap update.")
        return

    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    existing_locs = set()
    for url_elem in root.findall('ns:url', ns):
        loc = url_elem.find('ns:loc', ns)
        if loc is not None and loc.text:
            existing_locs.add(loc.text.strip())

    # Ensure blog.html is in sitemap
    blog_index_url = f"{SITE_URL}/blog.html"
    if blog_index_url not in existing_locs:
        url_el = ET.SubElement(root, 'url')
        loc_el = ET.SubElement(url_el, 'loc')
        loc_el.text = blog_index_url
        lastmod_el = ET.SubElement(url_el, 'lastmod')
        lastmod_el.text = today_str
        freq_el = ET.SubElement(url_el, 'changefreq')
        freq_el.text = 'daily'
        priority_el = ET.SubElement(url_el, 'priority')
        priority_el.text = '0.8'
        existing_locs.add(blog_index_url)

    # Add new post URL
    post_url = f"{SITE_URL}/blog/{new_slug}.html"
    if post_url not in existing_locs:
        url_el = ET.SubElement(root, 'url')
        loc_el = ET.SubElement(url_el, 'loc')
        loc_el.text = post_url
        lastmod_el = ET.SubElement(url_el, 'lastmod')
        lastmod_el.text = today_str
        freq_el = ET.SubElement(url_el, 'changefreq')
        freq_el.text = 'monthly'
        priority_el = ET.SubElement(url_el, 'priority')
        priority_el.text = '0.7'
        existing_locs.add(post_url)
        print(f"[SUCCESS] Added {post_url} to sitemap.xml")

    # Format cleanly
    if hasattr(ET, 'indent'):
        ET.indent(tree, space="  ", level=0)
        
    tree.write(SITEMAP_PATH, encoding="UTF-8", xml_declaration=True)


def main():
    print("==================================================")
    print("🚀 Saif Modan Daily Blog Automation")
    print("==================================================")
    
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is missing or empty.", file=sys.stderr)
        print("[ERROR] Please set GEMINI_API_KEY in your environment or GitHub Actions secrets.", file=sys.stderr)
        sys.exit(1)

    niche = os.environ.get(
        "BLOG_NICHE", 
        "AI Engineering, Python Automation, FastAPI Microservices, Video Diffusion Models, Computer Vision, and Data Analytics"
    ).strip()
    
    ensure_directories()
    
    # 1. Load existing posts
    posts = load_existing_posts()
    past_titles = [p.get("title", "") for p in posts]
    existing_slugs = {p.get("slug", "") for p in posts}
    
    today_str = datetime.date.today().isoformat()
    
    # 2. Call Gemini API
    data = call_gemini_api(api_key, niche, past_titles)
    
    slug = data["slug"]
    title = data["title"]
    meta_desc = data["metaDescription"]
    tags = data.get("tags", ["AI", "Python"])
    content_md = data["content"]
    image_prompt = data.get("imagePrompt", "")
    
    print(f"[INFO] Generated Article: '{title}' (slug: {slug})")
    
    # 3. Check for idempotency
    if slug in existing_slugs:
        print(f"[WARN] Post with slug '{slug}' already exists in posts.json. Updating content idempotently...")
    
    # 4. Generate cover image (Gemini Image with Qwen-Image & Pollinations.ai fallback)
    image_rel_path = generate_cover_image(image_prompt, slug, gemini_api_key=api_key)
    
    # 5. Convert Markdown to HTML
    html_content = markdown.markdown(
        content_md,
        extensions=[
            'fenced_code',
            'tables',
            'sane_lists',
            'nl2br'
        ]
    )
    
    reading_time = f"{calculate_reading_time(content_md)} min read"
    
    post_meta = {
        "slug": slug,
        "title": title,
        "metaDescription": meta_desc,
        "tags": tags,
        "date": today_str,
        "readingTime": reading_time,
        "image": image_rel_path
    }
    
    # 6. Render and write individual blog post HTML
    post_html = render_post_html(post_meta, html_content)
    post_file_path = os.path.join(BLOG_DIR, f"{slug}.html")
    with open(post_file_path, "w", encoding="utf-8") as f:
        f.write(post_html)
    print(f"[SUCCESS] Wrote article HTML to {post_file_path}")
    
    # 7. Update posts.json manifest
    # Remove existing entry if updating, then prepend
    posts = [p for p in posts if p.get("slug") != slug]
    posts.insert(0, post_meta)
    save_posts_manifest(posts)
    print(f"[SUCCESS] Updated {POSTS_JSON_PATH} (Total posts: {len(posts)})")
    
    # 8. Generate and write blog.html listing page
    blog_index_html = generate_blog_index_html(posts)
    with open(BLOG_INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(blog_index_html)
    print(f"[SUCCESS] Regenerated {BLOG_INDEX_PATH}")
    
    # 9. Update sitemap.xml
    update_sitemap(slug, today_str)
    
    print("==================================================")
    print(f"🎉 Blog generation completed successfully!")
    print(f"📄 View post: blog/{slug}.html")
    print(f"📚 View listing: blog.html")
    print("==================================================")


if __name__ == "__main__":
    main()

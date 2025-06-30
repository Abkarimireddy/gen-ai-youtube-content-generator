import streamlit as st
import google.generativeai as genai
import os
import re
import json
from datetime import datetime
import time

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="YouTube Content Generator",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .section-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
    }
    
    .generated-content {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #f8f9fa;
    }
    
    .stTextInput > div > div > input {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Gemini API Setup
# -------------------------------
@st.cache_resource
def initialize_gemini():
    """Initialize Gemini API with caching"""
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("Gemini API key not found. Please add it to .streamlit/secrets.toml or as an environment variable.")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

model = initialize_gemini()

# -------------------------------
# Enhanced Prompt Templates
# -------------------------------
def create_title_prompt(content, video_type, target_audience, keywords, tone, style_preferences):
    return f"""As a YouTube SEO expert, generate 8 compelling, click-worthy titles for a {video_type} video targeting {target_audience}.

Content Summary: {content}

Requirements:
- Primary Keywords: {keywords}
- Tone: {tone}
- Style Preferences: {style_preferences}
- Character count: 40-70 characters
- Include power words and emotional triggers
- Ensure SEO optimization
- Avoid clickbait but maintain curiosity
- Include numbers where relevant
- Consider trending formats

Provide exactly 8 titles, numbered 1-8, with brief explanations of why each title works.
"""

def create_description_prompt(content, video_type, target_audience, keywords, channel_info, video_length):
    return f"""As a YouTube SEO specialist, write a comprehensive, SEO-optimized description for a {video_type} video targeting {target_audience}.

Video Summary: {content}
Channel Information: {channel_info}
Target Keywords: {keywords}
Estimated Video Length: {video_length}

Structure the description with:
1. Hook (first 125 characters - crucial for search results)
2. Detailed video overview (200-300 words)
3. Key timestamps (create realistic placeholders)
4. Call-to-action section
5. Social media links placeholder
6. 5-8 relevant hashtags
7. Additional resources/links section

Focus on:
- SEO keyword integration
- Engaging first paragraph
- Clear value proposition
- Community engagement elements
- Accessibility considerations
"""

def create_tags_prompt(content, video_type, keywords, competitor_analysis):
    return f"""Generate 20 strategic YouTube tags for a {video_type} video to maximize discoverability.

Video Content: {content}
Primary Keywords: {keywords}
Competitor Insights: {competitor_analysis}

Provide tags in three categories:
1. Primary tags (5-7): Main topic keywords
2. Secondary tags (8-10): Related and long-tail keywords  
3. Trending tags (5-7): Current trending topics in the niche

Format: Return as comma-separated list with category labels.
"""

def create_thumbnail_prompt(content, video_type, target_audience):
    return f"""Suggest 5 effective thumbnail concepts for a {video_type} video targeting {target_audience}.

Video Content: {content}

For each thumbnail concept, provide:
1. Visual elements description
2. Text overlay suggestions (max 6 words)
3. Color scheme recommendations
4. Emotional appeal strategy
5. A/B testing variations

Focus on:
- High contrast and readability
- Emotional expressions if featuring people
- Clear visual hierarchy
- Mobile optimization
- Brand consistency
"""

# -------------------------------
# Enhanced Content Generation
# -------------------------------
def call_gemini_with_retry(prompt, max_retries=3):
    """Call Gemini API with retry logic and error handling"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Error: Unable to generate content after {max_retries} attempts. {str(e)}"
            time.sleep(1)  # Wait before retry

# -------------------------------
# Content Processing Functions
# -------------------------------
def extract_titles(response):
    """Extract titles from AI response with improved parsing"""
    lines = response.split('\n')
    titles = []
    for line in lines:
        # Match numbered lines (1., 2., etc.)
        match = re.match(r'^\d+\.\s*(.+)', line.strip())
        if match:
            title = match.group(1).strip()
            # Remove any explanation text in parentheses
            title = re.sub(r'\s*\([^)]*\)$', '', title)
            titles.append(title)
    return titles[:8]

def extract_tags(response):
    """Extract and categorize tags from AI response"""
    # Try to parse categorized response first
    if "Primary tags:" in response or "Secondary tags:" in response:
        primary = []
        secondary = []
        trending = []
        
        current_section = None
        for line in response.split('\n'):
            if "Primary tags:" in line.lower():
                current_section = "primary"
            elif "Secondary tags:" in line.lower():
                current_section = "secondary"
            elif "Trending tags:" in line.lower():
                current_section = "trending"
            elif current_section and line.strip():
                tags = [tag.strip() for tag in re.split(r'[,;|]+', line) if tag.strip()]
                if current_section == "primary":
                    primary.extend(tags)
                elif current_section == "secondary":
                    secondary.extend(tags)
                elif current_section == "trending":
                    trending.extend(tags)
        
        return {
            "primary": primary[:7],
            "secondary": secondary[:10],
            "trending": trending[:7],
            "all": (primary + secondary + trending)[:20]
        }
    else:
        # Fallback to simple parsing
        all_tags = [tag.strip() for tag in re.split(r'[,;|]+', response) if 2 < len(tag.strip()) < 30]
        return {"all": all_tags[:20]}

def analyze_content_metrics(content):
    """Analyze content and provide metrics"""
    word_count = len(content.split())
    char_count = len(content)
    estimated_reading_time = max(1, word_count // 200)  # Assuming 200 words per minute
    
    # Simple keyword density analysis
    words = content.lower().split()
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Only consider words longer than 3 characters
            word_freq[word] = word_freq.get(word, 0) + 1
    
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "reading_time": estimated_reading_time,
        "top_keywords": top_keywords
    }

# -------------------------------
# Session State Management
# -------------------------------
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'titles': [],
        'description': "",
        'tags': {},
        'thumbnail_concepts': "",
        'generation_history': [],
        'content_metrics': {},
        'selected_title': "",
        'custom_tags': [],
        'export_data': {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

initialize_session_state()

# -------------------------------
# Sidebar Configuration
# -------------------------------
with st.sidebar:
    st.markdown("### Configuration")
    
    # API Status
    if model:
        st.success("Gemini API Connected")
    else:
        st.error("Gemini API Not Connected")
    
    st.markdown("---")
    
    # Advanced Settings
    st.markdown("### Advanced Settings")
    
    max_titles = st.slider("Number of titles to generate", 3, 10, 8)
    include_analytics = st.checkbox("Include content analytics", True)
    generate_thumbnails = st.checkbox("Generate thumbnail concepts", True)
    save_history = st.checkbox("Save generation history", True)
    
    st.markdown("---")
    
    # Export Options
    st.markdown("### Export Options")
    export_format = st.selectbox("Export format", ["JSON", "CSV", "TXT"])
    
    if st.button("Export Current Results"):
        if st.session_state.titles or st.session_state.description:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "titles": st.session_state.titles,
                "description": st.session_state.description,
                "tags": st.session_state.tags,
                "metrics": st.session_state.content_metrics
            }
            
            if export_format == "JSON":
                st.download_button(
                    "Download JSON",
                    json.dumps(export_data, indent=2),
                    f"youtube_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
        else:
            st.warning("No content to export")

# -------------------------------
# Main UI Layout
# -------------------------------
st.markdown('<div class="main-header"><h1>YouTube Content Generator</h1><p>Create optimized titles, descriptions, and tags for your YouTube videos</p></div>', unsafe_allow_html=True)

# Input Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-header"><h3>Content Input</h3></div>', unsafe_allow_html=True)
    
    # Video Script/Summary
    video_script = st.text_area(
        "Video Script or Summary",
        height=200,
        help="Provide a detailed summary or script of your video content"
    )
    
    # Additional Content Details
    video_length = st.selectbox(
        "Estimated Video Length",
        ["Under 5 minutes", "5-10 minutes", "10-20 minutes", "20-30 minutes", "30+ minutes"]
    )

with col2:
    st.markdown('<div class="section-header"><h3>Video Details</h3></div>', unsafe_allow_html=True)
    
    video_type = st.selectbox(
        "Video Type",
        ["Tutorial", "Review", "Entertainment", "Educational", "Gaming", "Vlog", "How-to", "Unboxing", "Reaction", "Other"]
    )
    
    target_audience = st.selectbox(
        "Target Audience",
        ["General", "Beginners", "Intermediate", "Advanced", "Professionals", "Students", "Kids", "Teens", "Adults"]
    )
    
    tone = st.selectbox(
        "Content Tone",
        ["Professional", "Casual", "Energetic", "Educational", "Funny", "Serious", "Inspirational", "Conversational"]
    )

# Keywords and Channel Info
col3, col4 = st.columns(2)

with col3:
    keywords = st.text_input(
        "Primary Keywords (comma-separated)",
        help="Enter main keywords you want to rank for"
    )
    
    style_preferences = st.text_input(
        "Style Preferences",
        help="E.g., 'Use numbers', 'Include questions', 'Avoid caps'"
    )

with col4:
    channel_info = st.text_area(
        "Channel Information",
        height=80,
        help="Brief description of your channel and typical content"
    )
    
    competitor_analysis = st.text_input(
        "Competitor Keywords (optional)",
        help="Keywords your competitors are using"
    )

# Generation Options
st.markdown('<div class="section-header"><h3>Generation Options</h3></div>', unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)

with col5:
    generate_titles = st.checkbox("Generate Titles", True)
with col6:
    generate_desc = st.checkbox("Generate Description", True)
with col7:
    generate_tags = st.checkbox("Generate Tags", True)
with col8:
    generate_thumb = st.checkbox("Thumbnail Concepts", generate_thumbnails)

# Generate Button
if st.button("Generate Content", type="primary", use_container_width=True):
    if not video_script.strip():
        st.error("Please provide the video script or summary.")
    else:
        # Content Analysis
        if include_analytics:
            st.session_state.content_metrics = analyze_content_metrics(video_script)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_tasks = sum([generate_titles, generate_desc, generate_tags, generate_thumb])
        current_task = 0
        
        try:
            # Generate Titles
            if generate_titles:
                status_text.text("Generating titles...")
                prompt = create_title_prompt(video_script, video_type, target_audience, keywords, tone, style_preferences)
                response = call_gemini_with_retry(prompt)
                st.session_state.titles = extract_titles(response)
                current_task += 1
                progress_bar.progress(current_task / total_tasks)
            
            # Generate Description
            if generate_desc:
                status_text.text("Generating description...")
                prompt = create_description_prompt(video_script, video_type, target_audience, keywords, channel_info, video_length)
                st.session_state.description = call_gemini_with_retry(prompt)
                current_task += 1
                progress_bar.progress(current_task / total_tasks)
            
            # Generate Tags
            if generate_tags:
                status_text.text("Generating tags...")
                prompt = create_tags_prompt(video_script, video_type, keywords, competitor_analysis)
                response = call_gemini_with_retry(prompt)
                st.session_state.tags = extract_tags(response)
                current_task += 1
                progress_bar.progress(current_task / total_tasks)
            
            # Generate Thumbnail Concepts
            if generate_thumb:
                status_text.text("Generating thumbnail concepts...")
                prompt = create_thumbnail_prompt(video_script, video_type, target_audience)
                st.session_state.thumbnail_concepts = call_gemini_with_retry(prompt)
                current_task += 1
                progress_bar.progress(current_task / total_tasks)
            
            # Save to history
            if save_history:
                history_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "video_type": video_type,
                    "keywords": keywords,
                    "generated_content": {
                        "titles": len(st.session_state.titles),
                        "description": bool(st.session_state.description),
                        "tags": len(st.session_state.tags.get('all', [])),
                        "thumbnails": bool(st.session_state.thumbnail_concepts)
                    }
                }
                st.session_state.generation_history.append(history_entry)
            
            status_text.text("Generation complete!")
            progress_bar.progress(1.0)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            st.markdown('<div class="success-message">Content generated successfully!</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f'<div class="error-message">Error during generation: {str(e)}</div>', unsafe_allow_html=True)

# -------------------------------
# Results Display
# -------------------------------
if any([st.session_state.titles, st.session_state.description, st.session_state.tags, st.session_state.thumbnail_concepts]):
    st.markdown("---")
    st.markdown('<div class="section-header"><h2>Generated Content</h2></div>', unsafe_allow_html=True)

# Content Metrics
if include_analytics and st.session_state.content_metrics:
    st.markdown("### Content Analysis")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("Word Count", st.session_state.content_metrics['word_count'])
    with col_m2:
        st.metric("Character Count", st.session_state.content_metrics['char_count'])
    with col_m3:
        st.metric("Reading Time", f"{st.session_state.content_metrics['reading_time']} min")
    with col_m4:
        st.metric("Top Keywords", len(st.session_state.content_metrics['top_keywords']))

# Titles Display
if st.session_state.titles:
    st.markdown("### Generated Titles")
    
    for i, title in enumerate(st.session_state.titles, 1):
        col_title, col_select = st.columns([4, 1])
        
        with col_title:
            st.markdown(f'<div class="generated-content"><strong>{i}.</strong> {title}</div>', unsafe_allow_html=True)
        
        with col_select:
            if st.button(f"Select", key=f"select_title_{i}", help="Select this title"):
                st.session_state.selected_title = title
                st.success(f"Selected: {title}")

# Description Display
if st.session_state.description:
    st.markdown("### Generated Description")
    st.markdown('<div class="generated-content">', unsafe_allow_html=True)
    st.text_area("", st.session_state.description, height=300, key="desc_display")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Copy button simulation
    if st.button("Copy Description"):
        st.info("Description copied to clipboard! (Use Ctrl+C to copy the text above)")

# Tags Display
if st.session_state.tags:
    st.markdown("### Generated Tags")
    
    if isinstance(st.session_state.tags, dict) and 'primary' in st.session_state.tags:
        # Categorized tags
        tab1, tab2, tab3, tab4 = st.tabs(["All Tags", "Primary", "Secondary", "Trending"])
        
        with tab1:
            all_tags = st.session_state.tags.get('all', [])
            st.markdown(f'<div class="generated-content">{", ".join(all_tags)}</div>', unsafe_allow_html=True)
        
        with tab2:
            primary_tags = st.session_state.tags.get('primary', [])
            st.markdown(f'<div class="generated-content">{", ".join(primary_tags)}</div>', unsafe_allow_html=True)
        
        with tab3:
            secondary_tags = st.session_state.tags.get('secondary', [])
            st.markdown(f'<div class="generated-content">{", ".join(secondary_tags)}</div>', unsafe_allow_html=True)
        
        with tab4:
            trending_tags = st.session_state.tags.get('trending', [])
            st.markdown(f'<div class="generated-content">{", ".join(trending_tags)}</div>', unsafe_allow_html=True)
    else:
        # Simple tags list
        all_tags = st.session_state.tags.get('all', [])
        st.markdown(f'<div class="generated-content">{", ".join(all_tags)}</div>', unsafe_allow_html=True)

# Thumbnail Concepts
if st.session_state.thumbnail_concepts:
    st.markdown("### Thumbnail Concepts")
    st.markdown('<div class="generated-content">', unsafe_allow_html=True)
    st.text_area("", st.session_state.thumbnail_concepts, height=200, key="thumb_display")
    st.markdown('</div>', unsafe_allow_html=True)

# Generation History
if save_history and st.session_state.generation_history:
    with st.expander("Generation History"):
        for i, entry in enumerate(reversed(st.session_state.generation_history[-10:]), 1):
            st.markdown(f"**{i}.** {entry['timestamp']} - {entry['video_type']} - Keywords: {entry['keywords']}")

# Footer
st.markdown("---")
st.markdown("### Tips for Better Results")
st.info("""
- Provide detailed video summaries for better title generation
- Include specific keywords relevant to your niche
- Use competitor analysis to identify trending tags
- Test different tones and styles for your audience
- Consider A/B testing generated titles
- Keep descriptions between 200-500 words for optimal SEO
""")

# Clear Results Button
if st.button("Clear All Results", type="secondary"):
    for key in ['titles', 'description', 'tags', 'thumbnail_concepts', 'content_metrics', 'selected_title']:
        st.session_state[key] = [] if key in ['titles'] else {} if key in ['tags', 'content_metrics'] else ""
    st.rerun()
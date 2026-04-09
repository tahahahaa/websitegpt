import subprocess
import sys
import os

# Install Playwright browsers on Streamlit Cloud
if not os.path.exists('/home/appuser/.cache/ms-playwright'):
    subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], 
                   check=False)
    subprocess.run([sys.executable, '-m', 'playwright', 'install-deps', 'chromium'],
                   check=False)
import streamlit as st
from scraper import scrape_url
from rag_engine import build_vectorstore_from_docs, get_qa_chain

st.set_page_config(
    page_title='WebsiteGPT',
    page_icon='🌐',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🌐 WebsiteGPT')
st.caption('Chat with any website — JS-rendered content, dropdowns, FAQs, tables, iframes and more')

defaults = {
    'messages': [],
    'chain': None,
    'current_url': None,
    'site_loaded': False,
    'scrape_stats': None,
    'load_message': None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

with st.sidebar:
    st.header('⚙️ Load a Website')
    url_input = st.text_input('Website URL', placeholder='https://example.com')
    max_pages = st.slider('Max pages to scrape', 1, 20, 5,
                          help='Priority pages scraped first. Increase for larger sites.')
    load_btn = st.button('🚀 Load Website', use_container_width=True, type='primary')

    st.divider()
    if st.button('🔄 Reset', use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if st.session_state.scrape_stats:
        st.divider()
        st.markdown('**📊 Scrape Stats**')
        s = st.session_state.scrape_stats
        st.metric('Pages scraped', s['pages'])
        st.metric('Chunks indexed', s['chunks'])

if load_btn and url_input:
    if not url_input.startswith('http'):
        st.error('⚠️ Enter a full URL starting with https://')
    else:
        st.session_state.messages = []
        st.session_state.chain = None
        st.session_state.site_loaded = False
        st.session_state.scrape_stats = None
        st.session_state.load_message = None

        with st.spinner(f'Scraping {url_input} — may take up to 60s for JS-heavy sites...'):
            try:
                docs = scrape_url(url_input, max_pages)
                if not docs:
                    st.session_state.load_message = ('error',
                        '❌ No content scraped. Site may block bots. Try max_pages=1 or a different URL.')
                else:
                    vs, chunk_count = build_vectorstore_from_docs(docs)
                    st.session_state.chain = get_qa_chain(vs)
                    st.session_state.site_loaded = True
                    st.session_state.current_url = url_input
                    st.session_state.scrape_stats = {
                        'pages': len(docs),
                        'chunks': chunk_count
                    }
                    st.session_state.load_message = ('success',
                        f'✅ Loaded {len(docs)} page(s) → {chunk_count} chunks indexed. Ask away!')
            except Exception as e:
                st.session_state.load_message = ('error',
                    f'❌ Failed: {str(e)}\n\nTip: try max_pages=1 first.')

if st.session_state.load_message:
    kind, text = st.session_state.load_message
    if kind == 'success':
        st.success(text)
    else:
        st.error(text)

if st.session_state.site_loaded:
    st.info(f'💬 Chatting with: **{st.session_state.current_url}**')

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        if msg.get('sources'):
            with st.expander('📄 Sources', expanded=False):
                for src in msg['sources']:
                    st.markdown(f'- [{src}]({src})')

placeholder = (
    'Ask anything about this website...'
    if st.session_state.site_loaded
    else 'Load a website first using the sidebar →'
)

if prompt := st.chat_input(placeholder):
    if not st.session_state.chain:
        st.warning('⚠️ Please load a website first.')
    else:
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.markdown(prompt)

        with st.chat_message('assistant'):
            with st.spinner('Searching...'):
                try:
                    res = st.session_state.chain({'question': prompt})
                    answer = res.get('answer', 'No answer generated.')
                    source_docs = res.get('source_documents', [])

                    st.markdown(answer)

                    sources = list({
                        d.metadata['source']
                        for d in source_docs[:5]
                        if d.metadata.get('source', '').strip()
                    })

                    if sources:
                        with st.expander('📄 Sources', expanded=True):
                            for src in sources:
                                st.markdown(f'- [{src}]({src})')

                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': answer,
                        'sources': sources
                    })

                except Exception as e:
                    st.error(f'❌ Error: {str(e)}')
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': f'Error: {str(e)}',
                        'sources': []
                    })
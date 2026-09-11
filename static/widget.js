(function () {
  // Prevent multiple injections
  if (window.__VyapaarOSWidgetLoaded) return;
  window.__VyapaarOSWidgetLoaded = true;

  // Retrieve configuration from current script tag
  const currentScript = document.currentScript || document.querySelector('script[data-api-key]');
  const apiKey = currentScript ? currentScript.getAttribute('data-api-key') : null;
  const backendBaseUrl = currentScript ? (new URL(currentScript.src)).origin : 'http://127.0.0.1:8000';

  if (!apiKey) {
    console.error('VyapaarOS AI Bot: "data-api-key" attribute is missing on the script tag.');
    return;
  }

  // Create Host Container
  const host = document.createElement('div');
  host.id = 'vyapaaros-chat-widget-root';
  document.body.appendChild(host);

  // Attach Shadow DOM for 100% CSS isolation
  const shadow = host.attachShadow({ mode: 'open' });

  // Widget State
  let config = {
    client_name: 'Store Support',
    bot_name: 'AI Sales Executive',
    brand_color: '#0d9488',
    welcome_message: 'Hi! How can I assist you with our products and services today?',
    owner_whatsapp: '',
    suggestions: ['What do you sell?', 'Pricing & Catalog', 'Contact Team'],
    session_id: 'vyapaar_sess_' + Math.random().toString(36).substring(2, 12)
  };

  let isOpen = false;
  let chatHistory = [];
  let isSending = false;

  // Bug Fix #23: Use sessionStorage (tab-scoped) instead of localStorage
  // to prevent two users on the same device sharing the same conversation.
  const storedSession = sessionStorage.getItem('vyapaar_session_id');
  if (storedSession) {
    config.session_id = storedSession;
  } else {
    sessionStorage.setItem('vyapaar_session_id', config.session_id);
  }

  // CSS Styles inside Shadow DOM
  const style = document.createElement('style');
  style.textContent = `
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }

    .widget-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      pointer-events: none;
    }

    /* Floating Launcher Button */
    .launcher-btn {
      pointer-events: auto;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: var(--brand-color, #F2541B);
      color: #ffffff;
      border: none;
      outline: none;
      cursor: pointer;
      box-shadow: 0 10px 25px -5px rgba(242, 84, 27, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      position: relative;
    }

    .launcher-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 15px 30px -5px rgba(242, 84, 27, 0.5);
    }

    .launcher-btn svg {
      width: 28px;
      height: 28px;
      fill: currentColor;
      transition: transform 0.3s ease;
    }

    .launcher-badge {
      position: absolute;
      top: -2px;
      right: -2px;
      width: 14px;
      height: 14px;
      background: #22c55e;
      border: 2.5px solid #ffffff;
      border-radius: 50%;
    }

    /* Chat Window Card */
    .chat-card {
      width: 380px;
      height: 570px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 110px);
      background: #ffffff;
      border-radius: 22px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      margin-bottom: 16px;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1), height 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease, transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      border: 1px solid rgba(226, 232, 240, 0.9);
    }

    .chat-card.open {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* Maximized 2X Size State */
    .chat-card.maximized {
      width: 760px;
      height: 720px;
      max-width: calc(100vw - 40px);
      max-height: calc(100vh - 100px);
    }

    /* Header */
    .chat-header {
      background: var(--brand-color, #F2541B);
      color: #ffffff;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    }

    .header-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-avatar {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.25);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 19px;
      border: 2px solid rgba(255, 255, 255, 0.4);
    }

    .header-text h3 {
      font-size: 14.5px;
      font-weight: 700;
      line-height: 1.2;
    }

    .header-text p {
      font-size: 11.5px;
      opacity: 0.9;
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 2px;
    }

    .status-dot {
      width: 7px;
      height: 7px;
      background: #4ade80;
      border-radius: 50%;
      display: inline-block;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* Claude-style Circular Context Meter */
    .context-meter-wrapper {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(0, 0, 0, 0.2);
      padding: 4px 8px;
      border-radius: 14px;
      cursor: pointer;
      transition: background 0.2s;
      position: relative;
    }

    .context-meter-wrapper:hover {
      background: rgba(0, 0, 0, 0.35);
    }

    .context-pie-svg {
      width: 22px;
      height: 22px;
      transform: rotate(-90deg);
    }

    .context-pie-bg {
      fill: none;
      stroke: rgba(255, 255, 255, 0.25);
      stroke-width: 3.5;
    }

    .context-pie-fill {
      fill: none;
      stroke: #4ade80;
      stroke-width: 3.5;
      stroke-dasharray: 100 100;
      stroke-dashoffset: 95;
      transition: stroke-dashoffset 0.5s ease, stroke 0.3s;
      stroke-linecap: round;
    }

    .context-percent-text {
      font-size: 11px;
      font-weight: 700;
      color: #ffffff;
    }

    /* Tooltip */
    .context-tooltip {
      position: absolute;
      top: 36px;
      right: 0;
      background: #0f172a;
      color: #f8fafc;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 11.5px;
      width: 170px;
      box-shadow: 0 10px 20px rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.15);
      display: none;
      z-index: 10;
      line-height: 1.4;
    }

    .context-meter-wrapper:hover .context-tooltip {
      display: block;
    }

    .close-btn {
      background: transparent;
      border: none;
      color: #ffffff;
      cursor: pointer;
      padding: 4px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0.85;
      transition: background 0.2s, opacity 0.2s;
    }

    .close-btn:hover {
      opacity: 1;
      background: rgba(255, 255, 255, 0.2);
    }

    /* Messages Body */
    .messages-container {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      background: #f8fafc;
      scroll-behavior: smooth;
    }

    .msg-row {
      display: flex;
      flex-direction: column;
      max-width: 84%;
    }

    .msg-row.bot {
      align-self: flex-start;
    }

    .msg-row.user {
      align-self: flex-end;
    }

    .msg-bubble {
      padding: 11px 15px;
      font-size: 13.5px;
      line-height: 1.5;
      word-wrap: break-word;
      word-break: break-word;
    }
    
    .msg-bubble strong {
      font-weight: 700;
      color: inherit;
    }
    
    .msg-bubble em {
      font-style: italic;
    }

    .msg-bubble a {
      color: inherit;
      text-decoration: underline;
      font-weight: 600;
    }

    .msg-bubble .bullet-item {
      margin: 4px 0 4px 16px;
      list-style-type: disc;
    }

    .msg-row.bot .msg-bubble {
      position: relative;
      background: #ffffff;
      color: #1e293b;
      border-radius: 16px 16px 16px 4px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
      border: 1px solid #e2e8f0;
    }

    .msg-row.bot .msg-bubble.has-wa {
      margin-bottom: 6px;
      padding-bottom: 13px;
      padding-right: 18px;
    }

    .msg-row.user .msg-bubble {
      background: var(--brand-color, #F2541B);
      color: #ffffff;
      border-radius: 16px 16px 4px 16px;
      box-shadow: 0 2px 8px rgba(242, 84, 27, 0.2);
    }

    .msg-time {
      font-size: 10px;
      color: #94a3b8;
      margin-top: 4px;
      align-self: flex-start;
    }

    .msg-row.user .msg-time {
      align-self: flex-end;
    }

    /* Suggestions / Quick Actions */
    .quick-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }

    .chip-btn {
      background: #ffffff;
      color: var(--brand-color, #F2541B);
      border: 1px solid var(--brand-color, #F2541B);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .chip-btn:hover {
      background: var(--brand-color, #F2541B);
      color: #ffffff;
    }

    /* Pulsing WhatsApp Action Icon on Bottom-Right of Message Bubble */
    .msg-bubble a.bubble-wa-btn,
    .bubble-wa-btn {
      position: absolute;
      bottom: -7px;
      right: -7px;
      width: 28px;
      height: 28px;
      background: #25D366;
      color: #ffffff !important;
      fill: #ffffff !important;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      text-decoration: none !important;
      box-shadow: 0 2px 8px rgba(37, 211, 102, 0.4);
      animation: waBubblePulse 2s infinite ease-in-out;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      z-index: 10;
      border: 2px solid #ffffff;
    }

    .msg-bubble a.bubble-wa-btn:hover,
    .bubble-wa-btn:hover {
      transform: scale(1.18);
      animation: none;
      box-shadow: 0 4px 14px rgba(37, 211, 102, 0.65);
    }

    .bubble-wa-svg,
    .bubble-wa-btn svg,
    .bubble-wa-btn path {
      width: 15px;
      height: 15px;
      fill: #ffffff !important;
      color: #ffffff !important;
      display: block;
    }

    @keyframes waBubblePulse {
      0% {
        box-shadow: 0 0 0 0 rgba(37, 211, 102, 0.7);
      }
      70% {
        box-shadow: 0 0 0 8px rgba(37, 211, 102, 0);
      }
      100% {
        box-shadow: 0 0 0 0 rgba(37, 211, 102, 0);
      }
    }

    /* Tooltip on Hover */
    .bubble-wa-tooltip {
      position: absolute;
      bottom: calc(100% + 8px);
      right: 0;
      background: #0f172a;
      color: #ffffff;
      padding: 5px 10px;
      border-radius: 7px;
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
      pointer-events: none;
      opacity: 0;
      transform: translateY(6px);
      transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 6px 16px rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.12);
      display: flex;
      align-items: center;
      gap: 4px;
      z-index: 20;
    }

    .bubble-wa-tooltip::after {
      content: '';
      position: absolute;
      top: 100%;
      right: 9px;
      border-width: 5px;
      border-style: solid;
      border-color: #0f172a transparent transparent transparent;
    }

    .bubble-wa-btn:hover .bubble-wa-tooltip {
      opacity: 1;
      transform: translateY(0);
    }

    /* Enhanced Progressive Typing Indicator */
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      background: #ffffff;
      border-radius: 18px;
      width: fit-content;
      max-width: 90%;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
      border: 1px solid #e2e8f0;
      animation: fadeInTyping 0.25s ease-out;
    }

    .typing-dots {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
    }

    .typing-dot {
      width: 6px;
      height: 6px;
      background: var(--brand-color, #0d9488);
      border-radius: 50%;
      animation: pulse 1.4s infinite ease-in-out;
    }

    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    .typing-text {
      font-size: 12px;
      color: #64748b;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: opacity 0.2s ease, transform 0.2s ease;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .typing-text.fade-change {
      opacity: 0;
      transform: translateY(-3px);
    }

    @keyframes fadeInTyping {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.35; }
      40% { transform: scale(1.1); opacity: 1; }
    }

    /* WhatsApp-Style Product Media Collage */
    .media-collage {
      display: grid;
      gap: 3px;
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 8px;
      background: #0f172a;
      cursor: pointer;
    }

    .media-collage.count-1 {
      grid-template-columns: 1fr;
    }

    .media-collage.count-1 .media-item-wrap {
      height: 180px;
    }

    .media-collage.count-2 {
      grid-template-columns: 1fr 1fr;
    }
    .media-collage.count-2 .media-item-wrap {
      height: 130px;
    }

    .media-collage.count-3 {
      grid-template-columns: 1.2fr 1fr;
      grid-template-rows: 1fr 1fr;
      height: 160px;
    }

    .media-collage.count-3 .media-item-wrap:first-child {
      grid-row: span 2;
      height: 100%;
    }

    .media-collage.count-4 {
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr 1fr;
      height: 160px;
    }

    .media-item-wrap {
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #1e293b;
    }

    .media-item-wrap img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s;
    }

    .media-item-wrap:hover img {
      transform: scale(1.05);
    }

    .media-more-badge {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 800;
      backdrop-filter: blur(2px);
    }

    /* Inline Message Images */
    .inline-msg-img-wrap {
      margin: 8px 0;
      border-radius: 12px;
      overflow: hidden;
      max-height: 180px;
      background: #0f172a;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .inline-msg-img {
      width: 100%;
      height: 100%;
      max-height: 180px;
      object-fit: cover;
      display: block;
      transition: transform 0.25s ease;
    }

    .inline-msg-img:hover {
      transform: scale(1.04);
    }

    /* Fullscreen Image Lightbox */
    .media-lightbox {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.88);
      z-index: 9999999;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      backdrop-filter: blur(6px);
      cursor: zoom-out;
    }

    .lightbox-img {
      max-width: 90vw;
      max-height: 85vh;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.8);
      object-fit: contain;
    }

    .lightbox-close {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(255,255,255,0.2);
      color: #fff;
      border: none;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Input Footer */
    .chat-footer {
      padding: 12px 14px;
      background: #ffffff;
      border-top: 1px solid #f1f5f9;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .input-box {
      flex: 1;
      border: 1px solid #cbd5e1;
      padding: 9px 14px;
      border-radius: 24px;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }

    .input-box:focus {
      border-color: var(--brand-color, #F2541B);
    }

    .send-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--brand-color, #F2541B);
      color: #ffffff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
    }

    .send-btn:hover {
      transform: scale(1.05);
    }

    .send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .branding-tag {
      text-align: center;
      padding: 4px;
      font-size: 10px;
      color: #94a3b8;
      background: #ffffff;
    }
    
    .branding-tag a {
      color: #64748b;
      text-decoration: none;
      font-weight: 600;
    }

    @media (max-width: 480px) {
      .chat-card {
        width: calc(100vw - 32px);
        height: calc(100vh - 100px);
        bottom: 80px;
        right: 16px;
      }
      .widget-container {
        bottom: 16px;
        right: 16px;
      }
    }
  `;

  // HTML Structure inside Shadow DOM
  const wrapper = document.createElement('div');
  wrapper.className = 'widget-container';
  wrapper.innerHTML = `
    <!-- Chat Card -->
    <div class="chat-card" id="chatCard">
      <div class="chat-header">
        <div class="header-info">
          <div class="header-avatar">🤖</div>
          <div class="header-text">
            <h3 id="botNameText">AI Sales Executive</h3>
            <p><span class="status-dot"></span> Online & Ready</p>
          </div>
        </div>

        <div class="header-actions">
          <!-- Claude-style Context Circle Indicator -->
          <div class="context-meter-wrapper" id="contextMeter" title="AI Memory & Context Window">
            <svg class="context-pie-svg" viewBox="0 0 36 36">
              <path class="context-pie-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="context-pie-fill" id="contextPieFill" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="context-percent-text" id="contextPercentText">5%</span>
            
            <div class="context-tooltip" id="contextTooltip">
              <strong>AI Context Memory</strong><br/>
              <span id="tooltipTokens">Tokens: ~420 / 8,192</span><br/>
              <span id="tooltipDocs">RAG Docs: Active</span>
            </div>
          </div>

          <!-- Maximize / Minimize Button -->
          <button class="close-btn" id="expandChatBtn" title="Maximize chat window (2x)">
            <svg id="expandIcon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 3 21 3 21 9"></polyline>
              <polyline points="9 21 3 21 3 15"></polyline>
              <line x1="21" y1="3" x2="14" y2="10"></line>
              <line x1="3" y1="21" x2="10" y2="14"></line>
            </svg>
          </button>

          <!-- Restart / Clear Chat Button -->
          <button class="close-btn" id="resetChatBtn" title="Reset chat & memory">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          </button>

          <button class="close-btn" id="closeChatBtn" title="Close chat">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>

      <div class="messages-container" id="messagesBody">
        <!-- Messages will be injected here -->
      </div>

      <div class="chat-footer">
        <input type="text" class="input-box" id="userInput" placeholder="Ask about products, pricing..." autocomplete="off" />
        <button class="send-btn" id="sendBtn" title="Send message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="branding-tag">
        ⚡ Powered by <a href="/" target="_blank">VyapaarOS AI</a>
      </div>
    </div>

    <!-- Floating Launcher -->
    <button class="launcher-btn" id="launcherBtn" title="Chat with AI Executive">
      <span class="launcher-badge"></span>
      <svg id="launcherIcon" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
    </button>
  `;

  shadow.appendChild(style);
  shadow.appendChild(wrapper);

  // DOM References
  const chatCard = shadow.getElementById('chatCard');
  const launcherBtn = shadow.getElementById('launcherBtn');
  const closeChatBtn = shadow.getElementById('closeChatBtn');
  const resetChatBtn = shadow.getElementById('resetChatBtn');
  const expandChatBtn = shadow.getElementById('expandChatBtn');
  const expandIcon = shadow.getElementById('expandIcon');
  const messagesBody = shadow.getElementById('messagesBody');
  const userInput = shadow.getElementById('userInput');
  const sendBtn = shadow.getElementById('sendBtn');
  const botNameText = shadow.getElementById('botNameText');
  const contextPieFill = shadow.getElementById('contextPieFill');
  const contextPercentText = shadow.getElementById('contextPercentText');
  const tooltipTokens = shadow.getElementById('tooltipTokens');

  // Maximize / Restore Toggle
  const MAXIMIZE_SVG = `<polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line>`;
  const RESTORE_SVG = `<polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="10" y1="14" x2="3" y2="21"></line>`;

  function toggleMaximize() {
    const isMax = chatCard.classList.toggle('maximized');
    if (isMax) {
      expandIcon.innerHTML = RESTORE_SVG;
      expandChatBtn.title = "Restore normal size";
    } else {
      expandIcon.innerHTML = MAXIMIZE_SVG;
      expandChatBtn.title = "Maximize chat window (2x)";
    }
    setTimeout(() => {
      messagesBody.scrollTop = messagesBody.scrollHeight;
    }, 320);
  }

  if (expandChatBtn) {
    expandChatBtn.onclick = toggleMaximize;
  }

  // Reset Conversation Action
  function resetConversation() {
    chatHistory = [];
    config.session_id = 'vyapaar_sess_' + Math.random().toString(36).substring(2, 12);
    sessionStorage.setItem('vyapaar_session_id', config.session_id);  // Bug Fix #23
    messagesBody.innerHTML = '';
    updateContextMeter(4.5, 360, 8192);
    appendMessage('bot', config.welcome_message, config.suggestions);
  }

  if (resetChatBtn) {
    resetChatBtn.onclick = () => {
      if (confirm('Start a new conversation and clear chat history?')) {
        resetConversation();
      }
    };
  }

  // Update Context Meter
  function updateContextMeter(percentage, usedTokens, maxTokens) {
    const p = Math.min(100, Math.max(2, percentage));
    // stroke-dashoffset: 100 - p
    const offset = 100 - p;
    contextPieFill.style.strokeDashoffset = offset;
    contextPercentText.textContent = `${Math.round(p)}%`;

    if (p > 80) {
      contextPieFill.style.stroke = '#ef4444'; // red warning
    } else if (p > 50) {
      contextPieFill.style.stroke = '#eab308'; // yellow
    } else {
      contextPieFill.style.stroke = '#4ade80'; // green
    }

    if (usedTokens) {
      tooltipTokens.textContent = `Tokens: ~${usedTokens.toLocaleString()} / ${(maxTokens || 8192).toLocaleString()}`;
    }
  }

  // Apply Theme Brand Color
  function applyBrandColor(color) {
    wrapper.style.setProperty('--brand-color', color);
  }

  // Format Time
  function getTimeString() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Rich Text & Markdown Parser (Bold, Italic, Bullets, Lists, Links)
  function formatRichMarkdown(text) {
    if (!text) return '';
    
    // 1. Escape HTML entities
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 2. Bold: **text** or __text__
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // 3. Italic: *text* (if not followed by another *) or _text_
    html = html.replace(/(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
    html = html.replace(/\b_([^_]+?)_\b/g, '<em>$1</em>');

    // 4. Markdown Images ![alt](url) -> converted to styled img
    html = html.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g, '<div class="inline-msg-img-wrap"><img src="$2" alt="$1" class="inline-msg-img" onclick="window.__vyapaarOpenLightbox && window.__vyapaarOpenLightbox(\'$2\')" /></div>');

    // 5. Image Link markdown [📷 Image Link](url) or [Image](url) with image extension or unsplash -> clean image card
    html = html.replace(/\[(?:📷\s*)?(?:Image\s*Link|Image|Photo|View\s*Image|Design)\]\((https?:\/\/[^\s)]+)\)/gi, (match, url) => {
      return `<div class="inline-msg-img-wrap"><img src="${url}" alt="Product Photo" class="inline-msg-img" onclick="window.__vyapaarOpenLightbox && window.__vyapaarOpenLightbox('${url}')" /></div>`;
    });

    // 6. Regular Markdown Links [text](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // 7. Bullet items (lines starting with • or - or *)
    const lines = html.split('\n');
    let inList = false;
    const processedLines = lines.map(line => {
      const bulletMatch = line.match(/^(\s*)[•\-\*]\s+(.*)$/);
      if (bulletMatch) {
        return `<div class="bullet-item">• ${bulletMatch[2]}</div>`;
      }
      const numMatch = line.match(/^(\s*)(\d+\.)\s+(.*)$/);
      if (numMatch) {
        return `<div class="bullet-item">${numMatch[2]} ${numMatch[3]}</div>`;
      }
      return line;
    });

    html = processedLines.join('<br/>');

    // Remove redundant consecutive line breaks
    html = html.replace(/(<br\/>){3,}/g, '<br/><br/>');

    return html;
  }

  // Image Lightbox Fullscreen Preview
  function openLightbox(imgUrl) {
    const lb = document.createElement('div');
    lb.className = 'media-lightbox';
    lb.innerHTML = `
      <button class="lightbox-close" title="Close preview">&times;</button>
      <img src="${imgUrl}" class="lightbox-img" alt="Product Zoom" />
    `;
    lb.onclick = () => {
      // Bug Fix #16: Close on any click — including clicking the image itself
      if (lb.parentNode) lb.parentNode.removeChild(lb);
    };
    shadow.appendChild(lb);
  }
  window.__vyapaarOpenLightbox = openLightbox;

  // Append Message
  function appendMessage(sender, text, chips = [], whatsappUrl = null, images = []) {
    const row = document.createElement('div');
    row.className = `msg-row ${sender}`;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // 1. WhatsApp-Style Media Collage
    if (images && images.length > 0) {
      const collage = document.createElement('div');
      const count = Math.min(images.length, 4);
      collage.className = `media-collage count-${count}`;

      images.slice(0, 4).forEach((imgUrl, idx) => {
        const itemWrap = document.createElement('div');
        itemWrap.className = 'media-item-wrap';
        itemWrap.onclick = (e) => {
          e.stopPropagation();
          openLightbox(imgUrl);
        };

        const img = document.createElement('img');
        img.src = imgUrl;
        img.loading = 'lazy';
        img.alt = 'Product preview';
        itemWrap.appendChild(img);

        if (idx === 3 && images.length > 4) {
          const badge = document.createElement('div');
          badge.className = 'media-more-badge';
          badge.innerText = `+${images.length - 3}`;
          itemWrap.appendChild(badge);
        }

        collage.appendChild(itemWrap);
      });

      bubble.appendChild(collage);
    }

    // 2. Text Content
    const textWrap = document.createElement('div');
    textWrap.innerHTML = formatRichMarkdown(text);
    bubble.appendChild(textWrap);

    row.appendChild(bubble);

    if (chips && chips.length > 0) {
      const chipsContainer = document.createElement('div');
      chipsContainer.className = 'quick-chips';
      chips.forEach(chipText => {
        const chip = document.createElement('button');
        chip.className = 'chip-btn';
        chip.textContent = chipText;
        chip.onclick = () => {
          userInput.value = chipText;
          sendMessage();
        };
        chipsContainer.appendChild(chip);
      });
      row.appendChild(chipsContainer);
    }

    // Pulsing WhatsApp Action Icon on Bottom-Right of Bot Bubble
    if (whatsappUrl && sender === 'bot') {
      bubble.classList.add('has-wa');
      const waBtn = document.createElement('a');
      waBtn.className = 'bubble-wa-btn';
      waBtn.href = whatsappUrl;
      waBtn.target = '_blank';
      waBtn.rel = 'noopener noreferrer';
      waBtn.title = 'Direct WhatsApp Connect';
      waBtn.innerHTML = `
        <span class="bubble-wa-tooltip">Direct WhatsApp Connect ➔</span>
        <svg viewBox="0 0 24 24" class="bubble-wa-svg" style="fill:#ffffff; color:#ffffff;">
          <path fill="#ffffff" d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.04 2zm5.77 14.1c-.24.68-1.2 1.26-1.92 1.35-.49.06-1.12.08-3.26-.78-2.58-1.04-4.22-3.66-4.35-3.83-.13-.17-1.04-1.39-1.04-2.65 0-1.26.66-1.88.89-2.14.23-.26.51-.32.68-.32.17 0 .34 0 .49.01.16.01.37-.06.58.44.22.52.75 1.83.82 1.96.07.13.11.29.02.47-.09.18-.14.29-.28.45-.14.16-.29.35-.42.47-.14.14-.29.29-.12.58.17.29.74 1.22 1.59 1.98 1.09.97 2.01 1.27 2.3 1.41.29.14.46.12.63-.08.17-.2.73-.85.92-1.15.19-.3.38-.25.64-.15.26.1 1.64.77 1.92.91.28.14.47.21.54.33.07.12.07.7-.17 1.38z"/>
        </svg>
      `;
      bubble.appendChild(waBtn);
    }

    const time = document.createElement('span');
    time.className = 'msg-time';
    time.textContent = getTimeString();
    row.appendChild(time);

    messagesBody.appendChild(row);
    messagesBody.scrollTop = messagesBody.scrollHeight;
  }

  // Dynamic Progressive Typing Indicator
  let typingElem = null;
  let typingInterval = null;

  const TYPING_PHRASES = [
    // Stage 1 (0s): Immediate acknowledgment
    [
      "🤔 Soch raha hoon...",
      "🔍 Catalog check kar raha hoon...",
      "✨ Information dhoondh raha hoon...",
      "🤖 Details dekh raha hoon..."
    ],
    // Stage 2 (1.5s): Humble waiting
    [
      "✨ Bas thoda sa intezar kijiye...",
      "⚡ Best options nikaal raha hoon...",
      "⏳ Ek second, check kar raha hoon...",
      "🎯 Aapke liye best rate nikaal raha hoon..."
    ],
    // Stage 3 (3.2s+): Reassuring finish
    [
      "🙌 Bas aa hi gaya, response ready hai...",
      "⏳ Almost done, pricing calculate ho rahi hai...",
      "✨ Bas kuch pal aur, ready ho raha hai..."
    ]
  ];

  function showTyping() {
    if (typingElem) return;

    // Pick initial random phrase from Stage 1
    const stage1List = TYPING_PHRASES[0];
    const initialText = stage1List[Math.floor(Math.random() * stage1List.length)];

    typingElem = document.createElement('div');
    typingElem.className = 'msg-row bot';
    typingElem.innerHTML = `
      <div class="typing-indicator">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <span class="typing-text">${initialText}</span>
      </div>
    `;
    messagesBody.appendChild(typingElem);
    messagesBody.scrollTop = messagesBody.scrollHeight;

    const textSpan = typingElem.querySelector('.typing-text');
    let step = 0;

    // Transition smoothly through Stage 2 and Stage 3
    typingInterval = setInterval(() => {
      step++;
      const phraseGroup = TYPING_PHRASES[Math.min(step, TYPING_PHRASES.length - 1)];
      const nextPhrase = phraseGroup[Math.floor(Math.random() * phraseGroup.length)];

      if (textSpan) {
        textSpan.classList.add('fade-change');
        setTimeout(() => {
          textSpan.textContent = nextPhrase;
          textSpan.classList.remove('fade-change');
        }, 200);
      }
    }, 1700);
  }

  function hideTyping() {
    if (typingInterval) {
      clearInterval(typingInterval);
      typingInterval = null;
    }
    if (typingElem && typingElem.parentNode) {
      typingElem.parentNode.removeChild(typingElem);
      typingElem = null;
    }
  }

  // Toggle Chat
  function toggleChat() {
    isOpen = !isOpen;
    if (isOpen) {
      chatCard.classList.add('open');
      userInput.focus();
    } else {
      chatCard.classList.remove('open');
    }
  }

  launcherBtn.onclick = toggleChat;
  closeChatBtn.onclick = toggleChat;

  // Send Message API
  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isSending) return;

    // Display user message
    appendMessage('user', text);
    userInput.value = '';
    isSending = true;
    sendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch(`${backendBaseUrl}/api/v1/widget/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': apiKey
        },
        body: JSON.stringify({
          api_key: apiKey,
          session_id: config.session_id,
          message: text,
          history: chatHistory
        })
      });

      const data = await res.json();
      hideTyping();

      if (data.reply) {
        appendMessage('bot', data.reply, [], data.whatsapp_url, data.images || []);
        chatHistory.push({ role: 'user', content: text });
        chatHistory.push({ role: 'assistant', content: data.reply });

        // Update Claude-style Context Pie Meter
        if (data.context_stats) {
          updateContextMeter(
            data.context_stats.percentage, 
            data.context_stats.tokens_used, 
            data.context_stats.max_tokens
          );
        }
      } else {
        appendMessage('bot', data.error || 'Sorry, something went wrong. Please try again.');
      }
    } catch (err) {
      hideTyping();
      // Bug Fix #30: Show a retry button so user doesn't have to retype their message
      const errRow = document.createElement('div');
      errRow.className = 'msg-row bot';
      errRow.innerHTML = `
        <div class="msg-bubble" style="background:#fef2f2; border:1px solid #fecaca; color:#dc2626;">
          ⚠️ Network error — could not reach the server.
          <br/><button onclick="this.closest('.msg-row').remove(); window.__vyapaarRetry && window.__vyapaarRetry();"
            style="margin-top:8px; background:#dc2626; color:#fff; border:none; padding:5px 12px; border-radius:6px; cursor:pointer; font-size:11.5px; font-weight:700;">
            🔄 Retry
          </button>
        </div>`;
      messagesBody.appendChild(errRow);
      messagesBody.scrollTop = messagesBody.scrollHeight;
      // Store the last message so retry can resend it
      window.__vyapaarRetry = () => { userInput.value = text; sendMessage(); };
      console.error('VyapaarOS Widget Chat Error:', err);
    } finally {
      isSending = false;
      sendBtn.disabled = false;
    }
  }

  sendBtn.onclick = sendMessage;
  userInput.onkeydown = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  // Fetch Bot Config on Load
  async function initWidget() {
    try {
      const res = await fetch(`${backendBaseUrl}/api/v1/widget/config/?key=${apiKey}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      
      config = { ...config, ...data };
      applyBrandColor(config.brand_color);
      botNameText.textContent = config.bot_name;

      // Initialize meter with baseline token usage (system prompt + docs)
      updateContextMeter(4.5, 360, 8192);

      // Welcome Message
      const welcomeWaUrl = config.owner_whatsapp 
        ? `https://wa.me/${config.owner_whatsapp}?text=Hi%20${encodeURIComponent(config.client_name || 'Team')},%20I%20need%20assistance.` 
        : null;
      appendMessage('bot', config.welcome_message, config.suggestions, welcomeWaUrl);
    } catch (err) {
      console.warn('VyapaarOS: Could not fetch remote config, using defaults.', err);
      applyBrandColor('#F2541B');
      updateContextMeter(3, 240, 8192);
      appendMessage('bot', config.welcome_message, config.suggestions);
    }
  }

  initWidget();
})();

# 🤖 VyapaarOS AI Chatbot — Client Website Integration Guide

Welcome to the **VyapaarOS AI Sales Executive** embed guide! This document explains how to integrate your custom AI Chatbot into any website or e-commerce platform in less than 2 minutes.

---

## ⚡ The 1-Line Embed Code (Quick Start)

Copy the snippet below and paste it right before the closing `</body>` tag of your website:

```html
<!-- ======================================================== -->
<!-- 🤖 VyapaarOS AI Sales Executive Widget                   -->
<!-- ======================================================== -->
<script 
  src="https://bot.vyapaaros.in/static/widget.js" 
  data-api-key="YOUR_CLIENT_API_KEY_HERE" 
  defer>
</script>
```

> **Note:** Replace `YOUR_CLIENT_API_KEY_HERE` with your unique API key found in your [VyapaarOS Client Dashboard](https://bot.vyapaaros.in/login/).

---

## 🎨 Zero Styling Conflict (Shadow DOM)

The VyapaarOS widget is completely encapsulated inside a **Shadow DOM**. 
- It **will NOT conflict** with your site's Bootstrap, Tailwind, or custom CSS.
- It is 100% mobile-responsive and adjusts automatically to desktop, tablet, and mobile screens.

---

## 🛠️ Step-by-Step Platform Guides

### 1. Plain HTML / PHP / Custom Websites
1. Open your `index.html` or main template file.
2. Scroll to the very bottom.
3. Paste the script tag right above `</body>`:
   ```html
   <script 
     src="https://bot.vyapaaros.in/static/widget.js" 
     data-api-key="YOUR_CLIENT_API_KEY_HERE" 
     defer>
   </script>
   </body>
   ```

---

### 2. WordPress & WooCommerce
#### Option A: Using a Plugin (No Code)
1. In your WordPress Dashboard, go to **Plugins** ➔ **Add New**.
2. Search and install **"WPCode"** (or *Insert Headers and Footers*).
3. Go to **Code Snippets** ➔ **Header & Footer**.
4. In the **Footer** box, paste the script tag.
5. Click **Save Changes**.

#### Option B: In Theme `functions.php`
```php
function add_vyapaaros_ai_bot() {
    ?>
    <script 
      src="https://bot.vyapaaros.in/static/widget.js" 
      data-api-key="YOUR_CLIENT_API_KEY_HERE" 
      defer>
    </script>
    <?php
}
add_action('wp_footer', 'add_vyapaaros_ai_bot');
```

---

### 3. Shopify Stores
1. Open your **Shopify Admin** ➔ **Online Store** ➔ **Themes**.
2. Click the **`...` (Actions)** button on your active theme ➔ **Edit Code**.
3. Under **Layout**, click **`theme.liquid`**.
4. Scroll to the bottom of the file and paste right before `</body>`:
   ```liquid
   <script 
     src="https://bot.vyapaaros.in/static/widget.js" 
     data-api-key="YOUR_CLIENT_API_KEY_HERE" 
     defer>
   </script>
   ```
5. Click **Save**.

---

### 4. Google Tag Manager (GTM — Zero Codebase Touch)
1. Open your **Google Tag Manager** account.
2. Go to **Tags** ➔ **New** ➔ **Tag Configuration**.
3. Choose **Custom HTML**.
4. Paste the 1-line script tag.
5. In **Triggering**, select **Initialization - All Pages** (or *All Pages*).
6. Click **Save** and then **Submit & Publish**.

---

### 5. Next.js & React.js Applications

#### Next.js (App Router / Pages Router):
In your root layout (`app/layout.jsx` or `pages/_app.jsx`):
```jsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script
          src="https://bot.vyapaaros.in/static/widget.js"
          data-api-key="YOUR_CLIENT_API_KEY_HERE"
          strategy="lazyOnload"
        />
      </body>
    </html>
  );
}
```

#### React.js (Vite / CRA):
Paste directly into your `public/index.html` right before `</body>`.

---

### 6. Wix, Squarespace & Webflow
1. Go to your site's **Settings** ➔ **Custom Code / Embed Code**.
2. Choose **Body - End** as the placement.
3. Paste the script tag and click **Apply & Publish**.

---

## 💡 Layout Tip: Floating WhatsApp Button Co-existence

If you already have a floating WhatsApp icon in the bottom-right corner, adjust its position slightly upwards so both buttons look great together:

```css
/* Elevate your existing WhatsApp button above the AI Bot launcher */
.floating-whatsapp-btn {
    position: fixed !important;
    bottom: 96px !important;
    right: 24px !important;
    z-index: 9999 !important;
}
```

---

## 🎯 Bot Features Active on Your Site

- 💬 **Multilingual Support:** Converses naturally in Hindi, Hinglish, and English.
- ⚡ **Product & Rate Card Sync:** Automatically answers pricing, catalog specs, and services.
- 📲 **Instant WhatsApp Handoff:** Pulsing WhatsApp button inside bot bubbles for instant conversion.
- 📊 **Lead Capture:** Automatically captures visitor phone numbers and syncs with your Client Dashboard in real-time.

---

### 📞 Need Integration Support?
Contact the VyapaarOS Tech Team:
- **WhatsApp:** [+91 9955804730](https://wa.me/919955804730)
- **Portal:** [https://bot.vyapaaros.in/login/](https://bot.vyapaaros.in/login/)

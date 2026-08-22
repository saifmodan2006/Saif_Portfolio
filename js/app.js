/**
 * Saif Modan — Interactive Portfolio Engine
 * Inspired by amankureshi.com Aesthetic
 * Ultra-Smooth Interactions, Live Header Clock, & Cursor Portrait Follower
 */

document.addEventListener('DOMContentLoaded', () => {
  initPageLoader();
  initLiveClock();
  initScrollProgressBar();
  initScrollReveal();
  initWordRotator();
  initCursorPortraitFollower();
  initProjectFilters();
  initExperienceAccordion();
  initCopyEmail();
  initAiAssistant();
  initMenuDrawer();
  initHeaderScroll();
  initPrintResume();
  initVideoShowcase();
});

/* ==========================================================================
   1. Page Loader & Number Counter (amankureshi style)
   ========================================================================== */
function initPageLoader() {
  const loader = document.getElementById('page-loader');
  const counter = document.getElementById('loader-counter');
  if (!loader || !counter) return;

  let count = 0;
  const duration = 900; // ms
  const startTime = performance.now();

  function updateLoader(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease out cubic for realistic fast-then-settle counter
    const easedProgress = 1 - Math.pow(1 - progress, 3);
    count = Math.floor(easedProgress * 100);
    counter.textContent = count;

    if (progress < 1) {
      requestAnimationFrame(updateLoader);
    } else {
      counter.textContent = '100';
      setTimeout(() => {
        loader.classList.add('loaded');
        // Trigger initial hero elements reveal immediately
        document.querySelectorAll('.hero-section [data-reveal]').forEach(el => {
          el.classList.add('is-revealed');
        });
      }, 150);
    }
  }

  requestAnimationFrame(updateLoader);
}

/* ==========================================================================
   2. Live Time & Date Header Clock Widget (amankureshi style)
   ========================================================================== */
function initLiveClock() {
  const timeEl = document.getElementById('clock-time');
  const dateEl = document.getElementById('clock-date');
  if (!timeEl || !dateEl) return;

  function updateClock() {
    const now = new Date();

    // Format Time: 06:23:36 PM
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? String(hours).padStart(2, '0') : '12';

    timeEl.textContent = `${hours}:${minutes}:${seconds} ${ampm}`;

    // Format Date: Aug 22, 2026
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[now.getMonth()];
    const day = now.getDate();
    const year = now.getFullYear();

    dateEl.textContent = `${month} ${day}, ${year}`;
  }

  updateClock();
  setInterval(updateClock, 1000);
}

/* ==========================================================================
   3. Scroll Reading Progress Bar
   ========================================================================== */
function initScrollProgressBar() {
  const progressBar = document.getElementById('scroll-progress');
  if (!progressBar) return;

  window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    if (docHeight <= 0) return;
    const progressPercent = (scrollTop / docHeight) * 100;
    progressBar.style.width = `${progressPercent}%`;
  }, { passive: true });
}

/* ==========================================================================
   4. Scroll Reveal System (Ultra-Smooth GPU Accelerated)
   ========================================================================== */
function initScrollReveal() {
  const revealElements = document.querySelectorAll('[data-reveal]');
  if (!revealElements.length) return;

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          obs.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.05,
      rootMargin: '0px 0px -30px 0px'
    });

    revealElements.forEach(el => observer.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add('is-revealed'));
  }
}

/* ==========================================================================
   5. Floating Cursor-Following Portrait Follower (amankureshi exact style)
   ========================================================================== */
function initCursorPortraitFollower() {
  const trigger = document.getElementById('hero-name-trigger');
  const follower = document.getElementById('cursor-portrait-card');
  if (!trigger || !follower) return;

  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let currentX = mouseX;
  let currentY = mouseY;
  let isHovering = false;
  let isMobileActive = false;

  // Linear Interpolation for buttery cursor following
  function renderFollower() {
    if (isHovering && window.innerWidth > 768) {
      currentX += (mouseX - currentX) * 0.15;
      currentY += (mouseY - currentY) * 0.15;
      follower.style.left = `${currentX}px`;
      follower.style.top = `${currentY}px`;
    }
    requestAnimationFrame(renderFollower);
  }
  requestAnimationFrame(renderFollower);

  // Desktop Hover Track
  trigger.addEventListener('mouseenter', (e) => {
    if (window.innerWidth > 768) {
      isHovering = true;
      mouseX = e.clientX + 60;
      mouseY = e.clientY - 40;
      currentX = mouseX;
      currentY = mouseY;
      follower.style.left = `${currentX}px`;
      follower.style.top = `${currentY}px`;
      follower.classList.add('active');
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (isHovering && window.innerWidth > 768) {
      mouseX = e.clientX + 80;
      mouseY = e.clientY - 40;
    }
  });

  trigger.addEventListener('mouseleave', () => {
    if (window.innerWidth > 768) {
      isHovering = false;
      follower.classList.remove('active');
    }
  });

  // Mobile / Touch Tap Toggle
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    if (window.innerWidth <= 768) {
      isMobileActive = !isMobileActive;
      if (isMobileActive) {
        const rect = trigger.getBoundingClientRect();
        follower.style.left = `${window.innerWidth / 2}px`;
        follower.style.top = `${rect.bottom + 140}px`;
        follower.classList.add('active');
        trigger.classList.add('active');
      } else {
        follower.classList.remove('active');
        trigger.classList.remove('active');
      }
    }
  });

  document.addEventListener('click', (e) => {
    if (!trigger.contains(e.target)) {
      isMobileActive = false;
      follower.classList.remove('active');
      trigger.classList.remove('active');
    }
  });
}

/* ==========================================================================
   6. Dynamic Hero Word Rotator (amankureshi exact words)
   ========================================================================== */
function initWordRotator() {
  const words = ['Code.', 'Build.', 'Scale.', 'Secure.', 'Optimize.', 'Deploy.'];
  const rotatorEl = document.getElementById('rotator-word');
  if (!rotatorEl) return;

  let currentIndex = 0;

  setInterval(() => {
    currentIndex = (currentIndex + 1) % words.length;
    const nextWord = words[currentIndex];

    rotatorEl.style.animation = 'none';
    rotatorEl.offsetHeight; // trigger reflow
    rotatorEl.textContent = nextWord;
    rotatorEl.style.animation = 'wordSlide 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards';
  }, 2600);
}

/* ==========================================================================
   7. Project Category Filtering
   ========================================================================== */
function initProjectFilters() {
  const filterButtons = document.querySelectorAll('.filter-btn');
  const projectCards = document.querySelectorAll('.project-card');

  filterButtons.forEach(button => {
    button.addEventListener('click', () => {
      filterButtons.forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      });
      button.classList.add('active');
      button.setAttribute('aria-selected', 'true');

      const filterValue = button.getAttribute('data-filter');

      projectCards.forEach(card => {
        const categories = card.getAttribute('data-category') || '';
        if (filterValue === 'all' || categories.includes(filterValue)) {
          card.style.display = 'flex';
          card.style.opacity = '0';
          card.style.transform = 'translateY(10px)';
          setTimeout(() => {
            card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
          }, 30);
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

/* ==========================================================================
   8. Experience Accordion
   ========================================================================== */
function initExperienceAccordion() {
  const accordionItems = document.querySelectorAll('.accordion-item');

  accordionItems.forEach(item => {
    const trigger = item.querySelector('.accordion-trigger');
    if (!trigger) return;

    trigger.addEventListener('click', () => {
      const isActive = item.classList.contains('active');

      accordionItems.forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove('active');
          const otherTrigger = otherItem.querySelector('.accordion-trigger');
          if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
        }
      });

      if (isActive) {
        item.classList.remove('active');
        trigger.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
  });
}

/* ==========================================================================
   9. Copy Email & Toast Notification
   ========================================================================== */
function initCopyEmail() {
  const copyButtons = document.querySelectorAll('.copy-email-btn');
  const toast = document.getElementById('toast-notice');
  const toastMsg = document.getElementById('toast-message');

  let toastTimeout;

  copyButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const email = btn.getAttribute('data-email') || 'saifmodan000@gmail.com';

      navigator.clipboard.writeText(email).then(() => {
        showToast(`Copied ${email} to clipboard!`);
      }).catch(() => {
        showToast('Email: saifmodan000@gmail.com');
      });
    });
  });

  function showToast(message) {
    if (!toast) return;
    if (toastMsg) toastMsg.textContent = message;

    toast.classList.add('show');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }
}

/* ==========================================================================
   10. Interactive "Ask Saif AI" Assistant
   ========================================================================== */
function initAiAssistant() {
  const openBtn = document.getElementById('open-ai-modal');
  const closeBtn = document.getElementById('close-ai-modal');
  const modal = document.getElementById('ai-modal');
  const chatBody = document.getElementById('ai-chat-body');
  const form = document.getElementById('ai-input-form');
  const inputField = document.getElementById('ai-input-field');
  const suggestedChips = document.querySelectorAll('.suggested-chip');

  if (!modal) return;

  if (openBtn) {
    openBtn.addEventListener('click', () => {
      modal.classList.add('open');
      if (inputField) inputField.focus();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('open');
    });
  }

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('open');
    }
  });

  suggestedChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const promptText = chip.getAttribute('data-prompt');
      if (promptText) {
        handleUserMessage(promptText);
      }
    });
  });

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const message = inputField.value.trim();
      if (!message) return;
      handleUserMessage(message);
      inputField.value = '';
    });
  }

  function handleUserMessage(userText) {
    appendChatBubble(userText, 'user');
    const botResponse = generateAiResponse(userText);
    setTimeout(() => {
      appendChatBubble(botResponse, 'assistant');
    }, 350);
  }

  function appendChatBubble(text, sender) {
    if (!chatBody) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = text;
    chatBody.appendChild(bubble);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function generateAiResponse(query) {
    const q = query.toLowerCase();

    if (q.includes('video') || q.includes('commercial') || q.includes('brand') || q.includes('madhav') || q.includes('chilli') || q.includes('ad') || q.includes('diffusion')) {
      return `Saif specializes in <strong>AI Video Generation & Commercials</strong>! Check out his featured showcase for <strong>Madhav Chilli Powder</strong>. If you want custom AI commercial videos, ad creative, or brand storytelling for your business, <a href="contact.html" style="text-decoration:underline; font-weight:700;">contact Saif here</a>!`;
    }

    if (q.includes('skill') || q.includes('stack') || q.includes('tech') || q.includes('python')) {
      return `Saif specializes in <strong>AI Video Generation</strong>, <strong>Python, JavaScript, Flask, React.js, FastAPI</strong>, Data Analytics with <strong>Pandas, NumPy, Matplotlib, Seaborn, Power BI & Excel</strong>, Web Scraping with <strong>Selenium & BeautifulSoup</strong>, and Databases like <strong>MySQL, SQLite, & Supabase</strong>.`;
    }

    if (q.includes('project') || q.includes('face') || q.includes('resume') || q.includes('layoff') || q.includes('work')) {
      return `Saif's selected projects include <strong>Madhav Chilli Powder AI Commercial</strong>, <strong>Face Recognition System</strong> (FastAPI + React biometric platform), <strong>Resume Generator</strong>, <strong>Layoff Tracker</strong> (EDA & Data Visualization), <strong>AetherDrive</strong>, and <strong>Visual AI Activity Tracker</strong>.`;
    }

    if (q.includes('experience') || q.includes('tata') || q.includes('deloitte') || q.includes('job') || q.includes('simulation')) {
      return `Saif completed data analytics job simulations via Forage for <strong>Tata Group</strong> (AI-powered data analytics, GenAI EDA, and delinquency predictive modeling) and <strong>Deloitte Australia</strong> (Forensic data analytics and Tableau dashboards).`;
    }

    if (q.includes('contact') || q.includes('email') || q.includes('phone') || q.includes('hire') || q.includes('reach')) {
      return `You can reach Saif directly via email at <a href="mailto:saifmodan000@gmail.com" style="text-decoration:underline; font-weight:600;">saifmodan000@gmail.com</a>, phone at <a href="tel:+919824785082" style="text-decoration:underline; font-weight:600;">+91-9824785082</a>, or connect on <a href="https://www.linkedin.com/in/saif-modan" target="_blank" rel="noopener noreferrer" style="text-decoration:underline; font-weight:600;">LinkedIn</a> & <a href="https://github.com/saifmodan2006" target="_blank" rel="noopener noreferrer" style="text-decoration:underline; font-weight:600;">GitHub</a>!`;
    }

    if (q.includes('education') || q.includes('college') || q.includes('degree') || q.includes('university')) {
      return `Saif is pursuing his <strong>B.Tech in Computer Engineering</strong> at <strong>Silver Oak University</strong> (2025–2028), having completed his <strong>Diploma in Computer Engineering</strong> from <strong>LJ University</strong> (2022–2025) in Ahmedabad, Gujarat.`;
    }

    if (q.includes('certif') || q.includes('course')) {
      return `Saif holds verified certifications in <strong>Generative AI: Prompt Engineering Basics</strong>, <strong>Version Control (Git & GitHub)</strong>, <strong>Introduction to Python</strong>, <strong>Programming with Scratch</strong>, and <strong>Interpersonal Skills</strong>.`;
    }

    return `Thanks for asking! Saif Modan is an AI developer & Computer Engineering student from Ahmedabad specializing in AI Video Generation, Python backends, and data analytics. Feel free to ask about his commercial video projects, skills, or background!`;
  }
}

/* ==========================================================================
   11. Mobile Menu Drawer
   ========================================================================== */
function initMenuDrawer() {
  const openBtn = document.getElementById('open-menu-drawer');
  const closeBtn = document.getElementById('close-menu-drawer');
  const drawer = document.getElementById('menu-drawer');
  const links = document.querySelectorAll('.drawer-nav-link');

  if (!drawer) return;

  if (openBtn) {
    openBtn.addEventListener('click', () => {
      drawer.classList.add('open');
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      drawer.classList.remove('open');
    });
  }

  drawer.addEventListener('click', (e) => {
    if (e.target === drawer) {
      drawer.classList.remove('open');
    }
  });

  links.forEach(link => {
    link.addEventListener('click', () => {
      drawer.classList.remove('open');
    });
  });
}

/* ==========================================================================
   12. Header Scroll Shadow & Sticky Styling
   ========================================================================== */
function initHeaderScroll() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.05)';
      header.style.backgroundColor = 'rgba(255, 255, 255, 0.96)';
    } else {
      header.style.boxShadow = 'none';
      header.style.backgroundColor = 'rgba(255, 255, 255, 0.92)';
    }
  }, { passive: true });
}

/* ==========================================================================
   13. Print Resume Handler
   ========================================================================== */
function initPrintResume() {
  const printBtn = document.getElementById('print-resume-btn');
  if (!printBtn) return;

  printBtn.addEventListener('click', () => {
    window.print();
  });
}

/* ==========================================================================
   14. AI Video Showcase Player & Strict Protection
   ========================================================================== */
function initVideoShowcase() {
  const video = document.getElementById('showcase-ai-video');
  const soundBtn = document.getElementById('toggle-video-sound');
  const soundLabel = document.getElementById('audio-state-text');

  // Strict Protection: Disable Right-Click Context Menu and Drag on all videos
  const allVideos = document.querySelectorAll('video');
  allVideos.forEach(v => {
    v.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      return false;
    });
    v.addEventListener('dragstart', (e) => {
      e.preventDefault();
      return false;
    });
  });

  if (!video || !soundBtn) return;

  soundBtn.addEventListener('click', () => {
    if (video.muted) {
      video.muted = false;
      soundBtn.classList.add('active');
      if (soundLabel) soundLabel.textContent = 'SOUND ON 🔊';
    } else {
      video.muted = true;
      soundBtn.classList.remove('active');
      if (soundLabel) soundLabel.textContent = 'SOUND OFF 🔇';
    }
  });
}

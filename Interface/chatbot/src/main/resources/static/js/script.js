"use strict";

document.addEventListener('DOMContentLoaded', () => {
    
    // ==========================================
    // KHAI BÁO DOM ELEMENTS
    // ==========================================
    
    // UI Elements
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');
    const searchHistoryBtn = document.getElementById('search-history-btn');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const welcomeArea = document.getElementById('welcome-area');
    const suggestions = document.getElementById('suggestions');
    const suggestionChips = document.querySelectorAll('.chip');
    const messagesWrapper = document.getElementById('messages-wrapper');
    const chatContainer = document.getElementById('chat-container');

    // Auth & Profile Elements
    const avatarBtn = document.getElementById('avatar-btn');
    const authModal = document.getElementById('auth-modal');
    const closeModal = document.getElementById('close-modal');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    const profilePopup = document.getElementById('profile-popup');
    const accountList = document.getElementById('account-list');

    // ==========================================
    // MODULE 1: TƯƠNG TÁC UI CƠ BẢN
    // ==========================================
    
    // Đóng mở Sidebar
    menuToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));

    // Chức năng Kính lúp
    if (searchHistoryBtn) {
        searchHistoryBtn.addEventListener('click', () => {
            alert('Tính năng Tìm kiếm đoạn chat đang được phát triển! Cùng chờ đón nhé.');
        });
    }

    // Tự động thay đổi chiều cao Textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() !== '') {
            sendBtn.classList.add('active');
        } else {
            sendBtn.classList.remove('active');
        }
    });

    // Click vào nút Gợi ý (Chip)
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            // Lấy text trong chip (bỏ qua icon)
            const chipText = chip.textContent.trim();
            chatInput.value = chipText;
            chatInput.dispatchEvent(new Event('input')); // Trigger resize
            sendMessage(); // Gửi luôn
        });
    });

    // ==========================================
    // MODULE 2: QUẢN LÝ TÀI KHOẢN & AUTH
    // ==========================================
    
    function updateAvatarUI() {
        const username = localStorage.getItem('username');
        if (username) {
            avatarBtn.innerHTML = `<img src="https://ui-avatars.com/api/?name=${username}&background=a8c7fa&color=131314" alt="Avatar">`;
        } else {
            avatarBtn.innerHTML = `<img src="https://ui-avatars.com/api/?name=User&background=random" alt="Avatar">`;
        }
    }
    
    // Khởi tạo Avatar ban đầu
    updateAvatarUI(); 

    // Mở Popup Profile hoặc Modal Login
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const token = localStorage.getItem('token');
        if (token) {
            renderProfilePopup();
            profilePopup.classList.toggle('active');
            authModal.classList.remove('active');
        } else {
            authModal.classList.add('active');
            profilePopup.classList.remove('active');
        }
    });

    // Render danh sách tài khoản trong Popup
    function renderProfilePopup() {
        const currentUsername = localStorage.getItem('username');
        const currentFullName = localStorage.getItem('fullName') || currentUsername;
        
        document.getElementById('popup-avatar').src = `https://ui-avatars.com/api/?name=${currentUsername}&background=a8c7fa&color=131314`;
        document.getElementById('popup-fullname').innerText = `Chào ${currentFullName},`;

        const sessions = JSON.parse(localStorage.getItem('sessions')) || [];
        accountList.innerHTML = ''; 

        sessions.forEach(session => {
            if (session.username !== currentUsername) { 
                const div = document.createElement('div');
                div.className = 'account-item';
                div.innerHTML = `
                    <img src="https://ui-avatars.com/api/?name=${session.username}&background=random" alt="Avatar">
                    <div class="account-info">
                        <span class="acc-name">${session.fullName || session.username}</span>
                        <span class="acc-user">${session.username}</span>
                    </div>
                `;
                // Chuyển đổi tài khoản
                div.onclick = () => {
                    localStorage.setItem('token', session.token);
                    localStorage.setItem('userId', session.userId);
                    localStorage.setItem('username', session.username);
                    localStorage.setItem('fullName', session.fullName);
                    updateAvatarUI();
                    profilePopup.classList.remove('active');
                    
                    // Reset UI Chat
                    messagesWrapper.innerHTML = '';
                    if (welcomeArea) welcomeArea.style.display = 'block';
                    if (suggestions) suggestions.style.display = 'flex';
                };
                accountList.appendChild(div);
            }
        });
    }

    // Các nút trong Popup
    document.getElementById('add-account-btn').addEventListener('click', () => {
        profilePopup.classList.remove('active');
        authModal.classList.add('active'); 
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.clear(); 
        updateAvatarUI();
        profilePopup.classList.remove('active');
        messagesWrapper.innerHTML = '';
        if (welcomeArea) welcomeArea.style.display = 'block';
        if (suggestions) suggestions.style.display = 'flex';
    });

    // Đóng popup khi click ra ngoài
    document.addEventListener('click', (e) => {
        if (!profilePopup.contains(e.target) && !avatarBtn.contains(e.target)) {
            profilePopup.classList.remove('active');
        }
    });

    // --- Logic Modal Auth ---
    closeModal.addEventListener('click', () => authModal.classList.remove('active'));

    tabLogin.addEventListener('click', () => {
        tabLogin.classList.add('active'); tabRegister.classList.remove('active');
        loginForm.classList.add('active'); registerForm.classList.remove('active');
    });

    tabRegister.addEventListener('click', () => {
        tabRegister.classList.add('active'); tabLogin.classList.remove('active');
        registerForm.classList.add('active'); loginForm.classList.remove('active');
    });

    // API Đăng ký
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        const fullName = document.getElementById('reg-fullname').value;
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const msgEl = document.getElementById('reg-msg');

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fullName, username, password })
            });
            const text = await response.text();
            
            if (response.ok) {
                msgEl.className = 'auth-msg success-msg';
                msgEl.innerText = text;
                setTimeout(() => tabLogin.click(), 1500); 
            } else {
                msgEl.className = 'auth-msg error-msg';
                msgEl.innerText = text;
            }
        } catch (error) {
            msgEl.className = 'auth-msg error-msg';
            msgEl.innerText = 'Lỗi kết nối Server!';
        }
    });

    // API Đăng nhập
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const msgEl = document.getElementById('login-msg');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                const data = await response.json(); 
                
                let sessions = JSON.parse(localStorage.getItem('sessions')) || [];
                sessions = sessions.filter(s => s.username !== data.username);
                sessions.push(data);
                
                localStorage.setItem('sessions', JSON.stringify(sessions));
                localStorage.setItem('token', data.token); 
                localStorage.setItem('userId', data.userId);
                localStorage.setItem('username', data.username);
                localStorage.setItem('fullName', data.fullName || data.username);
                
                msgEl.className = 'auth-msg success-msg';
                msgEl.innerText = 'Đăng nhập thành công!';
                
                setTimeout(() => {
                    authModal.classList.remove('active');
                    updateAvatarUI();
                    loginForm.reset();
                    msgEl.innerText = '';
                }, 800);
            } else {
                msgEl.className = 'auth-msg error-msg';
                msgEl.innerText = 'Tài khoản hoặc mật khẩu không chính xác!';
            }
        } catch (error) {
            msgEl.innerText = 'Lỗi kết nối Server!';
        }
    });


    // ==========================================
    // MODULE 3: CHAT & API LOGIC
    // ==========================================
    
    function createMessageBubble(sender, content, isError = false) {
        const msgRow = document.createElement('div');
        msgRow.className = `msg-row ${sender}`;
        
        let iconHTML = '';
        let textColor = '';
        
        if (sender === 'ai') {
            if (isError) {
                iconHTML = `<span class="material-symbols-outlined" style="color: var(--color-error); margin-right: 10px;">error</span>`;
                textColor = `color: var(--color-error);`;
            } else {
                iconHTML = `<span class="material-symbols-outlined" style="color: var(--color-accent); margin-right: 10px;">spa</span>`;
            }
        }

        msgRow.innerHTML = `
            <div class="msg-bubble" style="${textColor}">
                ${iconHTML}
                <span>${content}</span>
            </div>`;
        return msgRow;
    }

    function createLoadingBubble() {
        const msgRow = document.createElement('div');
        msgRow.className = 'msg-row ai loading-msg';
        msgRow.innerHTML = `
            <div class="msg-bubble" style="opacity: 0.8; display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: var(--color-accent); animation: spin 2s linear infinite;">sync</span>
                <em>AI đang phân tích dữ liệu...</em>
            </div>`;
        return msgRow;
    }

    function scrollToBottom() {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        const token = localStorage.getItem('token');
        const userId = localStorage.getItem('userId');

        if (!text) return;

        // Bắt buộc đăng nhập
        if (!token) {
            alert("Bạn cần Đăng nhập để AI có thể lưu lại chế độ dinh dưỡng nhé!");
            authModal.classList.add('active');
            return;
        }

        // 1. Ẩn lời chào & Gợi ý
        if (welcomeArea) welcomeArea.style.display = 'none';
        if (suggestions) suggestions.style.display = 'none';

        // 2. Hiển thị tin nhắn người dùng
        messagesWrapper.appendChild(createMessageBubble('user', text));
        scrollToBottom();
        
        // 3. Khóa Input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        chatInput.disabled = true; 
        sendBtn.disabled = true;  
        sendBtn.classList.remove('active');

        // 4. Hiển thị Loading
        const loadingMsg = createLoadingBubble();
        messagesWrapper.appendChild(loadingMsg);
        scrollToBottom();

        try {
            // 5. Gọi API
            const response = await fetch(`/api/chat/send?userId=${userId}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: text })
            });

            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem('token');
                localStorage.removeItem('userId');
                updateAvatarUI();
                throw new Error("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại!");
            }

            if (!response.ok) {
                throw new Error(`Lỗi máy chủ: ${response.status}`);
            }

            const data = await response.json();
            const safeResponse = data.response || "Xin lỗi, tôi chưa hiểu ý bạn.";
            const formattedText = safeResponse.replace(/\n/g, '<br>');

            // Xóa Loading và thêm tin AI
            loadingMsg.remove();
            messagesWrapper.appendChild(createMessageBubble('ai', formattedText));

        } catch (error) {
            console.error("Lỗi Chat API:", error);
            loadingMsg.remove();
            messagesWrapper.appendChild(createMessageBubble('ai', error.message || 'Lỗi kết nối đến máy chủ AI!', true));
            
            if (error.message.includes("đăng nhập lại")) {
                 authModal.classList.add('active');
            }
        } finally {
            // 6. Mở khóa Input
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            scrollToBottom();
        }
    }

    // Gắn sự kiện gửi tin nhắn
    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); 
            sendMessage();
        }
    });
});
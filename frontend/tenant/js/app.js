const API_BASE = window.location.origin;

class TenantApp {
    constructor() {
        this.tenantId = localStorage.getItem('tenant_id');
        this.init();
    }

    async init() {
        this.jwtToken = localStorage.getItem('jwt_token');
        if (!this.jwtToken) {
            document.getElementById('loginModal').style.display = 'block';
            return; // Detener inicialización hasta que inicie sesión
        }

        this.setupNavigation();
        this.setupForms();
        this.setupModals();
        this.setupFilters();
        this.setupHumanToggle();
        this.setupQueueFilters();
        
        try {
            await this.loadDashboard();
            await this.loadProfile();
            await this.loadCategories();
            await this.loadProducts();
            await this.loadKBCategories();
            await this.loadKB();
            await this.loadChannels();
            await this.loadQueue();
        } catch (e) {
            if (e.message.includes('401')) {
                this.logout();
            }
        }
    }

    async handleLogin() {
        const usernameInput = document.getElementById('loginUsername');
        const passwordInput = document.getElementById('loginPassword');
        const errorEl = document.getElementById('loginError');
        
        const params = new URLSearchParams();
        params.append('username', usernameInput.value.trim());
        params.append('password', passwordInput.value.trim());

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params
            });

            if (!res.ok) {
                throw new Error('Credenciales incorrectas');
            }

            const data = await res.json();
            this.jwtToken = data.access_token;
            localStorage.setItem('jwt_token', this.jwtToken);
            
            // Ocultar modal y arrancar app
            document.getElementById('loginModal').style.display = 'none';
            this.init();
        } catch (e) {
            errorEl.textContent = e.message;
            errorEl.style.display = 'block';
        }
    }

    logout() {
        localStorage.removeItem('jwt_token');
        this.jwtToken = null;
        window.location.reload();
    }

    setupFilters() {
        const filterStatus = document.getElementById('filterStatus');
        const filterCategory = document.getElementById('filterCategory');
        const sortProducts = document.getElementById('sortProducts');
        if (filterStatus) {
            filterStatus.addEventListener('change', () => this.renderProducts());
        }
        if (filterCategory) {
            filterCategory.addEventListener('change', () => this.renderProducts());
        }
        if (sortProducts) {
            sortProducts.addEventListener('change', () => this.renderProducts());
        }
    }

    get headers() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.jwtToken}`,
        };
    }

    async fetch(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const res = await fetch(url, {
            ...options,
            headers: { ...this.headers, ...options.headers },
        });
        if (!res.ok) {
            const error = await res.json().catch(() => ({ error: 'Error desconocido' }));
            let errMsg = error.error;
            if (!errMsg && error.detail) {
                if (Array.isArray(error.detail)) {
                    errMsg = error.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                } else {
                    errMsg = error.detail;
                }
            }
            throw new Error(errMsg || `HTTP ${res.status}`);
        }
        return res.json();
    }

    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                const section = document.getElementById(link.dataset.section);
                if (section) section.classList.add('active');

                document.getElementById('pageTitle').textContent = link.textContent.trim();

                if (link.dataset.section === 'queue') {
                    this.loadQueue();
                }
            });
        });
    }

    setupForms() {
        document.getElementById('profileForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const data = {
                    name: document.getElementById('profileName').value,
                    email: document.getElementById('profileEmail').value || null,
                    phone: document.getElementById('profilePhone').value || null,
                    address: document.getElementById('profileAddress').value || null,
                    city: document.getElementById('profileCity').value || null,
                    website: document.getElementById('profileWebsite').value || null,
                    logo_url: document.getElementById('profileLogo').value || null,
                    business_hours: this.parseJSON(document.getElementById('profileHours').value),
                };
                await this.fetch('/tenants/me/profile', { method: 'PUT', body: JSON.stringify(data) });
                this.showToast('Perfil actualizado', 'success');
                await this.loadProfile();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        });
    }

    setupModals() {
        document.getElementById('modalClose').addEventListener('click', () => {
            document.getElementById('modal').classList.remove('active');
        });

        document.getElementById('addProductBtn').addEventListener('click', () => {
            this.showProductModal();
        });

        const addCategoryBtn = document.getElementById('addCategoryBtn');
        if (addCategoryBtn) {
            addCategoryBtn.addEventListener('click', () => {
                this.showCategoryModal();
            });
        }

        const addKBCategoryBtn = document.getElementById('addKBCategoryBtn');
        if (addKBCategoryBtn) {
            addKBCategoryBtn.addEventListener('click', () => {
                this.showKBCategoryModal();
            });
        }

        document.getElementById('addKbBtn').addEventListener('click', () => {
            this.showKBModal();
        });

        document.getElementById('kbSearchBtn').addEventListener('click', () => {
            this.searchKB();
        });
    }

    async loadDashboard() {
        try {
            const analytics = await this.fetch('/tenants/me/analytics');
            
            // Basic
            document.getElementById('userCount').textContent = analytics.basic.active_conversations_24h || 0;
            document.getElementById('convCount').textContent = analytics.basic.messages_today || 0;
            
            // Lost Sales
            const formatMoney = (amount) => {
                return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(amount);
            };
            
            document.getElementById('lostMoneyCount').textContent = formatMoney(analytics.lost_sales.dinero_en_la_mesa || 0);
            document.getElementById('lostCartsCount').textContent = analytics.lost_sales.personas_que_huyeron || 0;
            document.getElementById('lostProductsCount').textContent = analytics.lost_sales.total_productos_olvidados || 0;
        } catch (err) {
            console.error('Dashboard load failed:', err);
        }
    }

    async loadProfile() {
        try {
            const profile = await this.fetch('/tenants/me/profile');
            document.getElementById('tenantName').textContent = profile.name;
            document.getElementById('profileName').value = profile.name || '';
            document.getElementById('profileEmail').value = profile.email || '';
            document.getElementById('profilePhone').value = profile.phone || '';
            document.getElementById('profileAddress').value = profile.address || '';
            document.getElementById('profileCity').value = profile.city || '';
            document.getElementById('profileWebsite').value = profile.website || '';
            document.getElementById('profileLogo').value = profile.logo_url || '';
            document.getElementById('profileHours').value = profile.business_hours ? JSON.stringify(profile.business_hours, null, 2) : '';
            const statusBadge = document.getElementById('statusBadge');
            if (statusBadge) {
                if (profile.status === 'active') {
                    statusBadge.textContent = 'Activo';
                    statusBadge.className = 'status-badge active';
                } else {
                    statusBadge.textContent = 'Inactivo';
                    statusBadge.className = 'status-badge inactive';
                }
            }
            
            const toggle = document.getElementById('humanAvailableToggle');
            const statusText = document.getElementById('humanAvailableStatus');
            if (toggle) {
                toggle.checked = !!profile.human_available;
                if (statusText) {
                    statusText.textContent = toggle.checked ? 'CONECTADO' : 'DESCONECTADO';
                    statusText.style.background = toggle.checked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
                    statusText.style.color = toggle.checked ? 'var(--success)' : 'var(--danger)';
                }
            }
        } catch (err) {
            console.error('Profile load failed:', err);
        }
    }

    setupHumanToggle() {
        const toggle = document.getElementById('humanAvailableToggle');
        const statusText = document.getElementById('humanAvailableStatus');
        if (toggle) {
            toggle.addEventListener('change', async () => {
                try {
                    await this.fetch('/tenants/me/profile', {
                        method: 'PUT',
                        body: JSON.stringify({
                            human_available: toggle.checked
                        })
                    });
                    this.showToast(`Disponibilidad humana: ${toggle.checked ? 'Activa' : 'Inactiva'}`, 'success');
                    if (statusText) {
                        statusText.textContent = toggle.checked ? 'CONECTADO' : 'DESCONECTADO';
                        statusText.style.background = toggle.checked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
                        statusText.style.color = toggle.checked ? 'var(--success)' : 'var(--danger)';
                    }
                } catch (err) {
                    this.showToast(err.message, 'error');
                    toggle.checked = !toggle.checked;
                    if (statusText) {
                        statusText.textContent = toggle.checked ? 'CONECTADO' : 'DESCONECTADO';
                        statusText.style.background = toggle.checked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
                        statusText.style.color = toggle.checked ? 'var(--success)' : 'var(--danger)';
                    }
                }
            });
        }
    }

    setupQueueFilters() {
        const filterState = document.getElementById('queueFilterState');
        const queueSort = document.getElementById('queueSort');
        const queueSearch = document.getElementById('queueSearch');

        if (filterState) filterState.addEventListener('change', () => this.loadQueue());
        if (queueSort) queueSort.addEventListener('change', () => this.loadQueue());
        if (queueSearch) {
            let timeout = null;
            queueSearch.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => this.loadQueue(), 300);
            });
        }
    }

    async loadQueue() {
        const stateFilter = document.getElementById('queueFilterState');
        const queueSort = document.getElementById('queueSort');
        const queueSearch = document.getElementById('queueSearch');
        if (!stateFilter || !queueSort || !queueSearch) return;

        const stateVal = stateFilter.value;
        const sortVal = queueSort.value;
        const searchVal = queueSearch.value;

        const [sortBy, sortOrder] = sortVal.split('-');

        let url = `/tenants/me/conversations?state=${stateVal}&sort_by=${sortBy}&sort_order=${sortOrder}`;
        if (searchVal) {
            url += `&search=${encodeURIComponent(searchVal)}`;
        }

        try {
            const queueItems = await this.fetch(url);
            this.renderQueue(queueItems);
        } catch (err) {
            console.error('Queue load failed:', err);
            this.showToast('Error al cargar la cola: ' + err.message, 'error');
        }
    }

    renderQueue(items) {
        const tbody = document.getElementById('queueBody');
        if (!tbody) return;

        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No hay solicitudes en la cola.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        items.forEach(item => {
            const reqTime = new Date(item.created_at);
            const now = new Date();
            const diffMs = now - reqTime;
            const diffMins = Math.floor(diffMs / 60000);
            const waitTimeStr = diffMins > 0 ? `${diffMins} min` : 'Menos de 1 min';

            let badgeClass = 'badge-secondary';
            let badgeLabel = item.state;
            if (item.state === 'ESPERANDO_HUMANO') {
                badgeClass = 'badge-warning';
                badgeLabel = 'En Espera ⏳';
            } else if (item.state === 'HUMANO_ATENDIENDO') {
                badgeClass = 'badge-success';
                badgeLabel = 'Atendiendo 💁';
            } else if (item.state === 'POSPUESTA') {
                badgeClass = 'badge-info';
                badgeLabel = 'Pospuesta 😴';
            } else if (item.state === 'CANCELADA') {
                badgeClass = 'badge-danger';
                badgeLabel = 'Cancelada ❌';
            } else if (item.state === 'CHAT_LIBRE') {
                badgeClass = 'badge-primary';
                badgeLabel = 'Bot 🤖';
            }

            let actionsHtml = `
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.showChatPreview('${item.session_id}')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: transparent; border: 1px solid var(--border);">👁️ Ver Chat</button>
            `;

            if (item.state === 'ESPERANDO_HUMANO') {
                actionsHtml += `
                    <button type="button" class="btn btn-primary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'HUMANO_ATENDIENDO')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--success); border-color: var(--success); color: white;">💁 Atender</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'POSPUESTA')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--secondary); border-color: var(--secondary); color: white;">😴 Posponer</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'CANCELADA')" style="padding: 4px 8px; font-size: 12px; background: var(--danger); border-color: var(--danger); color: white;">❌ Cancelar</button>
                `;
            } else if (item.state === 'HUMANO_ATENDIENDO') {
                actionsHtml += `
                    <button type="button" class="btn btn-primary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'CHAT_LIBRE')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--primary); border-color: var(--primary); color: white;">🤖 Devolver al Bot</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'POSPUESTA')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--secondary); border-color: var(--secondary); color: white;">😴 Posponer</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'CANCELADA')" style="padding: 4px 8px; font-size: 12px; background: var(--danger); border-color: var(--danger); color: white;">❌ Cancelar</button>
                `;
            } else if (item.state === 'POSPUESTA') {
                actionsHtml += `
                    <button type="button" class="btn btn-primary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'HUMANO_ATENDIENDO')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--success); border-color: var(--success); color: white;">💁 Atender</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'CHAT_LIBRE')" style="margin-right: 5px; padding: 4px 8px; font-size: 12px; background: var(--primary); border-color: var(--primary); color: white;">🤖 Devolver al Bot</button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'CANCELADA')" style="padding: 4px 8px; font-size: 12px; background: var(--danger); border-color: var(--danger); color: white;">❌ Cancelar</button>
                `;
            } else {
                actionsHtml += `
                    <button type="button" class="btn btn-primary btn-sm" onclick="window.app.updateQueueState('${item.session_id}', 'ESPERANDO_HUMANO')" style="padding: 4px 8px; font-size: 12px; background: var(--primary); border-color: var(--primary); color: white;">⏳ Reabrir en Espera</button>
                `;
            }

            const clientName = item.user_display_name || item.user_external_id;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${clientName}</strong></td>
                <td><span style="text-transform: capitalize;">${item.user_platform}</span></td>
                <td>${waitTimeStr}</td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.last_message || ''}">
                    ${item.last_message || '<em style="color:var(--text-muted);">Sin mensajes</em>'}
                </td>
                <td><span class="badge ${badgeClass}">${badgeLabel}</span></td>
                <td>${actionsHtml}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    async updateQueueState(sessionId, newState) {
        try {
            await this.fetch(`/tenants/me/conversations/${sessionId}/state`, {
                method: 'PUT',
                body: JSON.stringify({ state: newState })
            });
            this.showToast('Estado de cola actualizado', 'success');
            await this.loadQueue();
        } catch (err) {
            console.error('Failed to update queue state:', err);
            this.showToast('Error al actualizar estado: ' + err.message, 'error');
        }
    }

    async showChatPreview(sessionId) {
        try {
            const messages = await this.fetch(`/tenants/me/conversations/${sessionId}/messages`);
            
            let chatHtml = `
                <div class="chat-preview-container" style="display: flex; flex-direction: column; max-height: 450px; min-height: 300px; background: #131316; border-radius: 8px; border: 1px solid var(--border); overflow: hidden; margin-top: 10px;">
                    <div class="chat-preview-header" style="padding: 10px 15px; background: var(--surface); border-bottom: 1px solid var(--border); font-size: 13px; font-weight: 500; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center;">
                        <span>Historial de Conversación</span>
                        <span style="font-family: monospace; font-size: 11px;">Sesión: ${sessionId.substring(0, 8)}...</span>
                    </div>
                    <div class="chat-preview-messages" style="flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; background: #0c0c0e;">
            `;

            if (messages.length === 0) {
                chatHtml += `
                    <div style="text-align: center; color: var(--text-muted); margin: auto;">No hay mensajes registrados.</div>
                `;
            } else {
                messages.forEach(m => {
                    const isUser = m.role === 'user';
                    const bubbleBg = isUser ? 'var(--primary-gradient)' : 'var(--surface)';
                    const bubbleColor = isUser ? '#ffffff' : 'var(--text)';
                    const align = isUser ? 'flex-end' : 'flex-start';
                    const timeStr = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    chatHtml += `
                        <div class="chat-msg" style="align-self: ${align}; max-width: 80%; display: flex; flex-direction: column; align-items: ${align};">
                            <div class="chat-bubble" style="background: ${bubbleBg}; color: ${bubbleColor}; padding: 10px 14px; border-radius: 12px; font-size: 14px; box-shadow: var(--shadow); line-height: 1.4; word-break: break-word;">
                                ${m.content}
                            </div>
                            <span style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">${timeStr}</span>
                        </div>
                    `;
                });
            }

            chatHtml += `
                    </div>
                </div>
            `;

            this.showCustomModal('Previsualizar Chat', chatHtml);
        } catch (err) {
            console.error('Failed to load chat history:', err);
            this.showToast('Error al cargar historial: ' + err.message, 'error');
        }
    }

    showCustomModal(titleText, bodyHtml) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');
        if (modal && title && body) {
            title.textContent = titleText;
            body.innerHTML = bodyHtml;
            modal.classList.add('active');
        }
    }

    async loadProducts() {
        try {
            this.products = await this.fetch('/tenants/me/products?limit=100');
            this.renderProducts();
        } catch (err) {
            console.error('Products load failed:', err);
        }
    }

    renderProducts() {
        if (!this.products) return;

        // 1. Get filter values
        const statusFilter = document.getElementById('filterStatus')?.value || 'all';
        const categoryFilter = document.getElementById('filterCategory')?.value || 'all';
        const sortFilter = document.getElementById('sortProducts')?.value || 'name';

        // 2. Filter products
        let filtered = [...this.products];
        if (statusFilter === 'active') {
            filtered = filtered.filter(p => p.is_available);
        } else if (statusFilter === 'inactive') {
            filtered = filtered.filter(p => !p.is_available);
        }
        
        if (categoryFilter !== 'all') {
            filtered = filtered.filter(p => p.category === categoryFilter);
        }

        // 3. Sort products
        if (sortFilter === 'name') {
            filtered.sort((a, b) => a.name.localeCompare(b.name));
        } else if (sortFilter === 'category_name') {
            filtered.sort((a, b) => {
                const catA = a.category || '';
                const catB = b.category || '';
                const catCompare = catA.localeCompare(catB);
                if (catCompare !== 0) return catCompare;
                return a.name.localeCompare(b.name);
            });
        }

        // 4. Render to DOM
        const tbody = document.getElementById('productsBody');
        tbody.innerHTML = '';
        filtered.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.name}</td>
                <td>${p.category || '-'}</td>
                <td>${p.price ? '$' + p.price.toLocaleString() : '-'}</td>
                <td>${p.stock}</td>
                <td>
                    <label class="status-checkbox-container">
                        <input type="checkbox" ${p.is_available ? 'checked' : ''} onchange="app.toggleProductStatus('${p.id}', this.checked)">
                        <span class="status-icon">${p.is_available ? '🟢' : '🔴'}</span>
                        <span class="status-text ${p.is_available ? 'text-active' : 'text-inactive'}">${p.is_available ? 'Activo' : 'Inactivo'}</span>
                    </label>
                </td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="app.editProduct('${p.id}')">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="app.deleteProduct('${p.id}')">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        const productCountEl = document.getElementById('productCount');
        if (productCountEl) productCountEl.textContent = filtered.length;
    }

    async toggleProductStatus(id, isChecked) {
        try {
            await this.fetch(`/tenants/me/products/${id}`, {
                method: 'PUT',
                body: JSON.stringify({
                    is_available: isChecked
                })
            });
            this.showToast('Estado de producto actualizado', 'success');
            if (this.products) {
                const product = this.products.find(p => p.id === id);
                if (product) product.is_available = isChecked;
                this.renderProducts();
            }
        } catch (err) {
            this.showToast(err.message, 'error');
            await this.loadProducts();
        }
    }

    async loadKB() {
        try {
            const entries = await this.fetch('/tenants/me/kb?limit=100');
            const tbody = document.getElementById('kbBody');
            tbody.innerHTML = '';
            entries.forEach(e => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${e.category}</td>
                    <td>${e.title}</td>
                    <td>${e.content.substring(0, 50)}...</td>
                    <td>${e.is_active ? '✅' : '❌'}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="app.editKB('${e.id}')">Editar</button>
                        <button class="btn btn-sm btn-danger" onclick="app.deleteKB('${e.id}')">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            const kbCountEl = document.getElementById('kbCount');
            if (kbCountEl) kbCountEl.textContent = entries.length;
        } catch (err) {
            console.error('KB load failed:', err);
        }
    }

    async loadChannels() {
        try {
            const channels = await this.fetch('/tenants/me/channels');
            const container = document.getElementById('channelsList');
            container.innerHTML = '';
            if (channels.length === 0) {
                container.innerHTML = '<p class="text-muted">No hay canales configurados.</p>';
                return;
            }
            channels.forEach(c => {
                const card = document.createElement('div');
                card.className = 'channel-card';
                card.innerHTML = `
                    <h4>${c.platform}</h4>
                    <p>${c.channel_identifier}</p>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            console.error('Channels load failed:', err);
        }
    }

    async searchKB() {
        const query = document.getElementById('kbSearchInput').value;
        if (!query) return;
        try {
            const result = await this.fetch('/tenants/me/kb/search', {
                method: 'POST',
                body: JSON.stringify({ query, top_k: 10 }),
            });
            this.showToast(`${result.count} resultados encontrados`, 'success');
        } catch (err) {
            this.showToast(err.message, 'error');
        }
    }

    showProductModal(product = null) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');

        title.textContent = product ? 'Editar Producto' : 'Nuevo Producto';

        let categoryOptions = '<option value="">Selecciona una categoría...</option>';
        if (this.categories && this.categories.length > 0) {
            const sortedCategories = [...this.categories].sort((a, b) => a.name.localeCompare(b.name));
            sortedCategories.forEach(c => {
                const selected = (product && product.category === c.name) ? 'selected' : '';
                categoryOptions += `<option value="${c.name}" ${selected}>${c.name}</option>`;
            });
        }

        body.innerHTML = `
            <form id="productForm">
                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" id="prodName" value="${product?.name || ''}" required spellcheck="true">
                </div>
                <div class="form-group">
                    <label>Descripción</label>
                    <textarea id="prodDesc" spellcheck="true">${product?.description || ''}</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Precio</label>
                        <input type="number" id="prodPrice" value="${product?.price || ''}" step="0.01" min="0">
                    </div>
                    <div class="form-group">
                        <label>Stock</label>
                        <input type="number" id="prodStock" value="${product?.stock || 0}" min="0" step="1">
                    </div>
                </div>
                <div class="form-group">
                    <label>Categoría</label>
                    <select id="prodCategory" required>
                        ${categoryOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>Estado</label>
                    <div class="status-checkbox-container" style="margin-top: 0.5rem;">
                        <input type="checkbox" id="prodAvailable" ${product ? (product.is_available ? 'checked' : '') : 'checked'} onchange="document.getElementById('modalStatusIcon').textContent = this.checked ? '🟢' : '🔴'; document.getElementById('modalStatusText').className = 'status-text ' + (this.checked ? 'text-active' : 'text-inactive'); document.getElementById('modalStatusText').textContent = this.checked ? 'Activo' : 'Inactivo';">
                        <span class="status-icon" id="modalStatusIcon">${product ? (product.is_available ? '🟢' : '🔴') : '🟢'}</span>
                        <span class="status-text ${product ? (product.is_available ? 'text-active' : 'text-inactive') : 'text-active'}" id="modalStatusText">${product ? (product.is_available ? 'Activo' : 'Inactivo') : 'Activo'}</span>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">Guardar</button>
                ${this.getSpellcheckWarningHTML()}
            </form>
        `;

        document.getElementById('productForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('prodName').value,
                description: document.getElementById('prodDesc').value || null,
                price: parseFloat(document.getElementById('prodPrice').value) || null,
                stock: parseInt(document.getElementById('prodStock').value) || 0,
                category: document.getElementById('prodCategory').value || null,
                is_available: document.getElementById('prodAvailable').checked,
            };
            try {
                if (product) {
                    await this.fetch(`/tenants/me/products/${product.id}`, { method: 'PUT', body: JSON.stringify(data) });
                } else {
                    await this.fetch('/tenants/me/products', { method: 'POST', body: JSON.stringify(data) });
                }
                this.showToast('Producto guardado', 'success');
                modal.classList.remove('active');
                await this.loadProducts();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        });

        modal.classList.add('active');
    }

    async editProduct(id) {
        const product = this.products.find(p => p.id === id);
        if (product) this.showProductModal(product);
    }

    async deleteProduct(id) {
        if (!confirm('¿Eliminar este producto?')) return;
        try {
            await this.fetch(`/tenants/me/products/${id}`, { method: 'DELETE' });
            this.showToast('Producto eliminado', 'success');
            await this.loadProducts();
        } catch (err) {
            this.showToast(err.message, 'error');
        }
    }

    showKBModal(entry = null) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');

        title.textContent = entry ? 'Editar Respuesta Automática' : 'Nueva Respuesta Automática';

        let kbCategoryOptions = '<option value="">Selecciona una categoría...</option>';
        if (this.kbCategories && this.kbCategories.length > 0) {
            const sortedKBCategories = [...this.kbCategories].sort((a, b) => a.name.localeCompare(b.name));
            sortedKBCategories.forEach(c => {
                const selected = (entry && entry.category === c.name) ? 'selected' : '';
                kbCategoryOptions += `<option value="${c.name}" ${selected}>${c.name}</option>`;
            });
        }

        body.innerHTML = `
            <form id="kbForm">
                <div class="form-group">
                    <label>Categoría</label>
                    <select id="kbCategory" required>
                        ${kbCategoryOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label>Título</label>
                    <input type="text" id="kbTitle" value="${entry?.title || ''}" required spellcheck="true">
                </div>
                <div class="form-group">
                    <label>Contenido</label>
                    <textarea id="kbContent" rows="5" required spellcheck="true">${entry?.content || ''}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Guardar</button>
                ${this.getSpellcheckWarningHTML()}
            </form>
        `;

        document.getElementById('kbForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                category: document.getElementById('kbCategory').value,
                title: document.getElementById('kbTitle').value,
                content: document.getElementById('kbContent').value,
            };
            try {
                if (entry) {
                    await this.fetch(`/tenants/me/kb/${entry.id}`, { method: 'PUT', body: JSON.stringify(data) });
                } else {
                    await this.fetch('/tenants/me/kb', { method: 'POST', body: JSON.stringify(data) });
                }
                this.showToast('Respuesta guardada', 'success');
                modal.classList.remove('active');
                await this.loadKB();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        });

        modal.classList.add('active');
    }

    async editKB(id) {
        const entries = await this.fetch('/tenants/me/kb?limit=100');
        const entry = entries.find(e => e.id === id);
        if (entry) this.showKBModal(entry);
    }

    async deleteKB(id) {
        if (!confirm('¿Eliminar esta respuesta automática?')) return;
        try {
            await this.fetch(`/tenants/me/kb/${id}`, { method: 'DELETE' });
            this.showToast('Respuesta eliminada', 'success');
            await this.loadKB();
        } catch (err) {
            this.showToast(err.message, 'error');
        }
    }

    async loadCategories() {
        try {
            this.categories = await this.fetch('/tenants/me/categories');
            this.renderCategories();
        } catch (err) {
            console.error('Categories load failed:', err);
        }
    }

    renderCategories() {
        if (!this.categories) return;
        
        // Actualizar el filtro de categorías en la tabla de productos
        const filterCategory = document.getElementById('filterCategory');
        if (filterCategory) {
            const currentValue = filterCategory.value;
            filterCategory.innerHTML = '<option value="all">Todas las categorías</option>';
            const sortedCategories = [...this.categories].sort((a, b) => a.name.localeCompare(b.name));
            sortedCategories.forEach(c => {
                filterCategory.innerHTML += `<option value="${c.name}">${c.name}</option>`;
            });
            filterCategory.value = currentValue || 'all'; // Mantener selección si existe
        }
        
        const tbody = document.getElementById('categoriesBody');
        tbody.innerHTML = '';
        this.categories.forEach(c => {
            const isGeneral = c.name === 'General';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.name}</td>
                <td>${c.description || '-'}</td>
                <td>
                    ${isGeneral 
                        ? `<span class="text-muted" style="font-size: 0.85rem; font-style: italic;">Sistema (Protegida)</span>`
                        : `<button class="btn btn-sm btn-secondary" onclick="app.editCategory('${c.id}')">Editar</button>
                           <button class="btn btn-sm btn-danger" onclick="app.deleteCategory('${c.id}')">Eliminar</button>`
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    showCategoryModal(category = null) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');

        title.textContent = category ? 'Editar Categoría' : 'Nueva Categoría';
        body.innerHTML = `
            <form id="categoryForm">
                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" id="catName" value="${category?.name || ''}" required placeholder="Ej. serbesas, binos, gaseosas..." spellcheck="true">
                </div>
                <div class="form-group">
                    <label>Descripción</label>
                    <textarea id="catDesc" spellcheck="true">${category?.description || ''}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Guardar</button>
                ${this.getSpellcheckWarningHTML()}
            </form>
        `;

        document.getElementById('categoryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const originalName = document.getElementById('catName').value;
            const data = {
                name: originalName,
                description: document.getElementById('catDesc').value || null,
            };
            try {
                let savedCategory;
                if (category) {
                    savedCategory = await this.fetch(`/tenants/me/categories/${category.id}`, { method: 'PUT', body: JSON.stringify(data) });
                } else {
                    savedCategory = await this.fetch('/tenants/me/categories', { method: 'POST', body: JSON.stringify(data) });
                }
                
                // Show spelling corrector notice if corrected
                if (savedCategory.name !== originalName) {
                    this.showToast(`Corrección ortográfica aplicada: "${originalName}" ➔ "${savedCategory.name}"`, 'success');
                } else {
                    this.showToast('Categoría guardada', 'success');
                }

                modal.classList.remove('active');
                await this.loadCategories();
                await this.loadProducts();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        });

        modal.classList.add('active');
    }

    async editCategory(id) {
        const category = this.categories.find(c => c.id === id);
        if (category) this.showCategoryModal(category);
    }

    async deleteCategory(id) {
        if (!confirm('¿Eliminar esta categoría?')) return;
        try {
            await this.fetch(`/tenants/me/categories/${id}`, { method: 'DELETE' });
            this.showToast('Categoría eliminada', 'success');
            await this.loadCategories();
            await this.loadProducts();
        } catch (err) {
            this.showToast(err.message, 'error');
        }
    }

    async loadKBCategories() {
        try {
            this.kbCategories = await this.fetch('/tenants/me/kb-categories');
            this.renderKBCategories();
        } catch (err) {
            console.error('KB Categories load failed:', err);
        }
    }

    renderKBCategories() {
        if (!this.kbCategories) return;
        
        // Alphabetical sorting
        const sortedKBCats = [...this.kbCategories].sort((a, b) => a.name.localeCompare(b.name));
        
        const tbody = document.getElementById('kbCategoriesBody');
        tbody.innerHTML = '';
        sortedKBCats.forEach(c => {
            const isGeneral = c.name === 'General';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.name}</td>
                <td>${c.description || '-'}</td>
                <td>
                    ${isGeneral 
                        ? `<span class="text-muted" style="font-size: 0.85rem; font-style: italic;">Sistema (Protegida)</span>`
                        : `<button class="btn btn-sm btn-secondary" onclick="app.editKBCategory('${c.id}')">Editar</button>
                           <button class="btn btn-sm btn-danger" onclick="app.deleteKBCategory('${c.id}')">Eliminar</button>`
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    showKBCategoryModal(category = null) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');

        title.textContent = category ? 'Editar Categoría de Respuesta' : 'Nueva Categoría de Respuesta';
        body.innerHTML = `
            <form id="kbCategoryForm">
                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" id="kbCatName" value="${category?.name || ''}" required placeholder="Ej. delivery, horarios, reclamos..." spellcheck="true">
                </div>
                <div class="form-group">
                    <label>Descripción</label>
                    <textarea id="kbCatDesc" spellcheck="true">${category?.description || ''}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Guardar</button>
                ${this.getSpellcheckWarningHTML()}
            </form>
        `;

        document.getElementById('kbCategoryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const originalName = document.getElementById('kbCatName').value;
            const data = {
                name: originalName,
                description: document.getElementById('kbCatDesc').value || null,
            };
            try {
                let savedCategory;
                if (category) {
                    savedCategory = await this.fetch(`/tenants/me/kb-categories/${category.id}`, { method: 'PUT', body: JSON.stringify(data) });
                } else {
                    savedCategory = await this.fetch('/tenants/me/kb-categories', { method: 'POST', body: JSON.stringify(data) });
                }
                
                // Show spelling corrector notice if corrected
                if (savedCategory.name !== originalName) {
                    this.showToast(`Corrección ortográfica aplicada: "${originalName}" ➔ "${savedCategory.name}"`, 'success');
                } else {
                    this.showToast('Categoría de respuesta guardada', 'success');
                }

                modal.classList.remove('active');
                await this.loadKBCategories();
                await this.loadKB();
            } catch (err) {
                this.showToast(err.message, 'error');
            }
        });

        modal.classList.add('active');
    }

    async editKBCategory(id) {
        const category = this.kbCategories.find(c => c.id === id);
        if (category) this.showKBCategoryModal(category);
    }

    async deleteKBCategory(id) {
        if (!confirm('¿Eliminar esta categoría de respuesta? Se reasignarán las respuestas asociadas a "General".')) return;
        try {
            await this.fetch(`/tenants/me/kb-categories/${id}`, { method: 'DELETE' });
            this.showToast('Categoría de respuesta eliminada', 'success');
            await this.loadKBCategories();
            await this.loadKB();
        } catch (err) {
            this.showToast(err.message, 'error');
        }
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    getSpellcheckWarningHTML() {
        return `<div class="spellcheck-warning-footer">* Sugerencia: Asegúrate de mantener activado el corrector ortográfico de tu navegador para evitar errores tipográficos.</div>`;
    }

    parseJSON(str) {
        try {
            return str ? JSON.parse(str) : null;
        } catch {
            return null;
        }
    }
}

window.app = new TenantApp();

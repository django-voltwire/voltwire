// VoltWire JavaScript Client
class VoltWire {
    constructor() {
        this.components = new Map();
        this.spaEnabled = true;
        this.init();
    }

    init() {
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.bindEvents();
        this.processComponents();
        this.setupSPANavigation();
    }

    bindEvents() {
        // Delegate all VoltWire events
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('submit', this.handleSubmit.bind(this));
        document.addEventListener('input', this.handleInput.bind(this));
        document.addEventListener('change', this.handleChange.bind(this));
    }

    handleClick(event) {
        const target = event.target;
        const component = this.findComponent(target);

        if (!component) return;

        // Handle vw:click
        const clickAction = target.getAttribute('vw:click');
        if (clickAction) {
            event.preventDefault();
            this.executeAction(component, clickAction, target);
            return;
        }

        // Handle vw:toggle
        const toggleProperty = target.getAttribute('vw:toggle');
        if (toggleProperty) {
            event.preventDefault();
            this.toggleProperty(component, toggleProperty);
            return;
        }

        // Handle SPA links
        if (target.hasAttribute('vw:spa') && target.tagName === 'A' && target.href) {
            event.preventDefault();
            this.spaNavigate(target.href);
            return;
        }
    }

    handleSubmit(event) {
        const form = event.target;
        const component = this.findComponent(form);

        if (!component) return;

        const submitAction = form.getAttribute('vw:submit');
        if (submitAction) {
            event.preventDefault();
            this.executeAction(component, submitAction, form);
        }
    }

    handleInput(event) {
        const target = event.target;
        const component = this.findComponent(target);

        if (!component) return;

        // Handle vw:model
        const modelProperty = target.getAttribute('vw:model');
        if (modelProperty) {
            this.updateProperty(component, modelProperty, target.value);
        }

        // Handle vw:model.live
        const modelLiveProperty = target.getAttribute('vw:model.live');
        if (modelLiveProperty) {
            this.updateProperty(component, modelLiveProperty, target.value);
        }
    }

    handleChange(event) {
        const target = event.target;
        const component = this.findComponent(target);

        if (!component) return;

        // Handle vw:model for select, checkbox, radio
        const modelProperty = target.getAttribute('vw:model');
        if (modelProperty) {
            let value;
            if (target.type === 'checkbox') {
                value = target.checked;
            } else if (target.type === 'radio') {
                value = target.checked ? target.value : null;
            } else {
                value = target.value;
            }
            this.updateProperty(component, modelProperty, value);
        }
    }

    findComponent(element) {
        // Find the nearest component container
        let current = element;
        while (current && current !== document) {
            if (current.hasAttribute('data-voltwire-component')) {
                return current.getAttribute('data-voltwire-component');
            }
            current = current.parentElement;
        }
        return null;
    }

    async executeAction(componentName, action, element) {
        const component = this.getComponentData(componentName);
        if (!component) return;

        // Show loading state
        this.setLoading(element, true);

        try {
            const formData = new FormData();
            formData.append('voltwire_action', action);

            // Add component properties
            for (const [key, value] of Object.entries(component.properties)) {
                formData.append(key, value);
            }

            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-VoltWire-Request': 'true',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });

            const data = await response.json();
            await this.handleResponse(data);

        } catch (error) {
            console.error('VoltWire action error:', error);
        } finally {
            this.setLoading(element, false);
        }
    }

    async updateProperty(componentName, property, value) {
        const component = this.getComponentData(componentName);
        if (!component) return;

        component.properties[property] = value;

        // Optional: Debounced live updates
        if (this.shouldUpdateLive(property)) {
            clearTimeout(this.liveUpdateTimeout);
            this.liveUpdateTimeout = setTimeout(() => {
                this.executeAction(componentName, 'update_property', null);
            }, 300);
        }
    }

    toggleProperty(componentName, property) {
        const component = this.getComponentData(componentName);
        if (!component) return;

        const currentValue = component.properties[property];
        component.properties[property] = !currentValue;

        // Update UI immediately
        this.updateUI(componentName);
    }

    async spaNavigate(url) {
        if (!this.spaEnabled) {
            window.location.href = url;
            return;
        }

        try {
            // Show loading state
            document.body.classList.add('voltwire-loading');

            const response = await fetch(url, {
                headers: {
                    'X-VoltWire-SPA': 'true',
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (response.redirected) {
                window.history.pushState({}, '', response.url);
            }

            const html = await response.text();
            await this.updatePage(html);

            // Update browser history
            window.history.pushState({}, '', url);

        } catch (error) {
            console.error('SPA navigation error:', error);
            window.location.href = url;
        } finally {
            document.body.classList.remove('voltwire-loading');
        }
    }

    async updatePage(html) {
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');

        // Update title
        const newTitle = newDoc.querySelector('title');
        if (newTitle) {
            document.title = newTitle.textContent;
        }

        // Update main content
        const mainContent = document.querySelector('main, .main-content, [role="main"]') || document.body;
        const newContent = newDoc.querySelector('main, .main-content, [role="main"]') || newDoc.body;

        if (mainContent && newContent) {
            mainContent.innerHTML = newContent.innerHTML;
        }

        // Re-initialize VoltWire
        this.processComponents();
    }

    async handleResponse(data) {
        if (data.redirect) {
            window.location.href = data.redirect;
            return;
        }

        if (data.html) {
            await this.updateComponent(data.html);
        }

        if (data.messages) {
            this.showMessages(data.messages);
        }

        if (data.properties) {
            this.updateProperties(data.properties);
        }
    }

    async updateComponent(html) {
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');
        const componentElement = newDoc.querySelector('[data-voltwire-component]');

        if (componentElement) {
            const componentName = componentElement.getAttribute('data-voltwire-component');
            const currentElement = document.querySelector(`[data-voltwire-component="${componentName}"]`);

            if (currentElement) {
                currentElement.innerHTML = componentElement.innerHTML;
                this.processComponent(currentElement);
            }
        }
    }

    updateProperties(properties) {
        for (const [componentName, componentProperties] of Object.entries(properties)) {
            const component = this.getComponentData(componentName);
            if (component) {
                Object.assign(component.properties, componentProperties);
            }
        }
    }

    showMessages(messages) {
        // Simple toast implementation
        messages.forEach(message => {
            const toast = document.createElement('div');
            toast.className = `voltwire-toast voltwire-toast-${message.type}`;
            toast.textContent = message.text;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 3000);
        });
    }

    setLoading(element, isLoading) {
        if (!element) return;

        if (isLoading) {
            element.setAttribute('vw-loading', 'true');
            element.disabled = true;
        } else {
            element.removeAttribute('vw-loading');
            element.disabled = false;
        }
    }

    shouldUpdateLive(property) {
        // Check if property should trigger live updates
        return property && property.includes('.live');
    }

    getComponentData(componentName) {
        return this.components.get(componentName);
    }

    processComponents() {
        // Find and initialize all components
        const components = document.querySelectorAll('[data-voltwire-component]');
        components.forEach(component => {
            const componentName = component.getAttribute('data-voltwire-component');
            const properties = JSON.parse(component.getAttribute('data-voltwire-properties') || '{}');

            this.components.set(componentName, {
                element: component,
                properties: properties
            });
        });
    }

    processComponent(element) {
        const componentName = element.getAttribute('data-voltwire-component');
        const properties = JSON.parse(element.getAttribute('data-voltwire-properties') || '{}');

        this.components.set(componentName, {
            element: element,
            properties: properties
        });
    }

    setupSPANavigation() {
        // Handle browser back/forward
        window.addEventListener('popstate', (event) => {
            this.spaNavigate(window.location.href);
        });

        // Prefetch links with vw:prefetch
        document.addEventListener('mouseenter', (event) => {
            const target = event.target;
            if (target.tagName === 'A' && target.hasAttribute('vw:prefetch')) {
                this.prefetch(target.href);
            }
        }, { once: true });
    }

    async prefetch(url) {
        try {
            await fetch(url, {
                headers: {
                    'X-VoltWire-Prefetch': 'true',
                }
            });
        } catch (error) {
            // Silent fail for prefetch
        }
    }
}

// Initialize VoltWire
if (typeof window !== 'undefined') {
    window.VoltWire = new VoltWire();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoltWire;
}

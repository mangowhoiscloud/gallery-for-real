/**
 * app.js — shared API utility for the shop frontend.
 *
 * Auth flow:
 *   - Credentials stored as Base64(email:password) in sessionStorage under key 'auth'
 *   - Every API call attaches Authorization: Basic <credentials>
 *   - 401 response redirects to /static/login.html (preserves return URL)
 */

(function (window) {
  'use strict';

  var AUTH_KEY = 'auth';
  var USER_KEY = 'user';

  /* ------------------------------------------------------------------ */
  /* Credential helpers                                                   */
  /* ------------------------------------------------------------------ */

  function saveCredentials(email, password) {
    var encoded = btoa(email + ':' + password);
    sessionStorage.setItem(AUTH_KEY, encoded);
  }

  function clearCredentials() {
    sessionStorage.removeItem(AUTH_KEY);
    sessionStorage.removeItem(USER_KEY);
  }

  function getCredentials() {
    return sessionStorage.getItem(AUTH_KEY);
  }

  function saveUser(user) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function getUser() {
    var raw = sessionStorage.getItem(USER_KEY);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (e) { return null; }
  }

  function isLoggedIn() {
    return !!getCredentials();
  }

  /* ------------------------------------------------------------------ */
  /* Core API call                                                        */
  /* ------------------------------------------------------------------ */

  /**
   * apiCall(path, options) → Promise<any>
   *
   * Wraps fetch() with:
   *   - Base URL prefix (empty → same-origin)
   *   - JSON request/response bodies
   *   - Authorization header from sessionStorage
   *   - 401 → redirect to login.html
   *   - Non-2xx → rejects with parsed error body
   *
   * @param {string} path    - e.g. '/api/products'
   * @param {object} options - same as fetch options + optional `body` (object → auto-JSON)
   * @returns {Promise}      - resolves with parsed JSON body (or null for 204)
   */
  function apiCall(path, options) {
    options = options || {};
    var headers = options.headers ? Object.assign({}, options.headers) : {};

    var creds = getCredentials();
    if (creds) {
      headers['Authorization'] = 'Basic ' + creds;
    }

    if (options.body && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    options.headers = headers;

    return fetch(path, options).then(function (res) {
      if (res.status === 401) {
        clearCredentials();
        var returnUrl = encodeURIComponent(window.location.href);
        window.location.href = '/static/login.html?return=' + returnUrl;
        return Promise.reject(new Error('Unauthorized'));
      }

      if (res.status === 204) {
        return null;
      }

      return res.json().then(function (data) {
        if (!res.ok) {
          var err = new Error(data.message || 'Request failed');
          err.status = res.status;
          err.data = data;
          return Promise.reject(err);
        }
        return data;
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Auth helpers                                                         */
  /* ------------------------------------------------------------------ */

  /**
   * login(email, password) → Promise<user>
   * Validates credentials against POST /api/members/login.
   * On success, stores credentials + user profile in sessionStorage.
   */
  function login(email, password) {
    return apiCallNoAuth('/api/members/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    }).then(function (user) {
      saveCredentials(email, password);
      saveUser(user);
      return user;
    });
  }

  /**
   * register(data) → Promise<user>
   * Creates account via POST /api/members.
   * On success, auto-logs in (stores credentials).
   * data: { email, password, name, phone?, address? }
   */
  function register(data) {
    return apiCallNoAuth('/api/members', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(function (user) {
      saveCredentials(data.email, data.password);
      saveUser(user);
      return user;
    });
  }

  function logout() {
    clearCredentials();
    window.location.href = '/static/login.html';
  }

  /* apiCallNoAuth — same as apiCall but never injects Authorization header */
  function apiCallNoAuth(path, options) {
    options = options || {};
    return fetch(path, options).then(function (res) {
      if (res.status === 204) return null;
      return res.json().then(function (data) {
        if (!res.ok) {
          var err = new Error(data.message || 'Request failed');
          err.status = res.status;
          err.data = data;
          return Promise.reject(err);
        }
        return data;
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* DOM helpers                                                          */
  /* ------------------------------------------------------------------ */

  /** requireAuth() — redirects to login if not authenticated */
  function requireAuth() {
    if (!isLoggedIn()) {
      var returnUrl = encodeURIComponent(window.location.href);
      window.location.href = '/static/login.html?return=' + returnUrl;
    }
  }

  /** showAlert(containerId, message, type) — renders inline alert */
  function showAlert(containerId, message, type) {
    var el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = '<div class="alert alert-' + (type || 'error') + '">' +
      escapeHtml(message) + '</div>';
  }

  function clearAlert(containerId) {
    var el = document.getElementById(containerId);
    if (el) el.innerHTML = '';
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /** renderNavbar(elementId) — injects navbar with auth-aware links */
  function renderNavbar(elementId) {
    var el = document.getElementById(elementId);
    if (!el) return;

    var user = getUser();
    var right = '';
    if (user) {
      right = '<span class="text-muted" style="color:#ccc;font-size:0.88rem">Hello, ' +
        escapeHtml(user.name || user.email) + '</span>' +
        (user.role === 'ADMIN' ? '' : '') +
        ' <a href="#" onclick="App.logout();return false;" class="btn-nav">Logout</a>';
    } else {
      right = '<a href="/static/login.html" class="btn-nav">Login / Register</a>';
    }

    el.innerHTML =
      '<nav class="navbar"><div class="container">' +
      '<a class="brand" href="/static/index.html">ShopLegacy</a>' +
      '<nav>' +
      '<a href="/static/index.html">Products</a>' +
      (isLoggedIn() ? '<a href="/static/cart.html">Cart</a>' : '') +
      (isLoggedIn() ? '<a href="/static/orders.html">Orders</a>' : '') +
      right +
      '</nav>' +
      '</div></nav>';
  }

  /** statusBadge(status) — returns HTML badge for order/product status */
  function statusBadge(status) {
    var map = {
      PENDING:   'badge-warning',
      CONFIRMED: 'badge-info',
      SHIPPED:   'badge-info',
      DELIVERED: 'badge-success',
      CANCELLED: 'badge-danger',
      ACTIVE:    'badge-success',
      INACTIVE:  'badge-secondary'
    };
    var cls = map[status] || 'badge-secondary';
    return '<span class="badge ' + cls + '">' + status + '</span>';
  }

  /** formatPrice(amount) — formats a number as currency string */
  function formatPrice(amount) {
    return '$' + parseFloat(amount).toFixed(2);
  }

  /* ------------------------------------------------------------------ */
  /* Public API                                                           */
  /* ------------------------------------------------------------------ */

  window.App = {
    apiCall: apiCall,
    login: login,
    register: register,
    logout: logout,
    isLoggedIn: isLoggedIn,
    getUser: getUser,
    saveCredentials: saveCredentials,
    saveUser: saveUser,
    requireAuth: requireAuth,
    showAlert: showAlert,
    clearAlert: clearAlert,
    escapeHtml: escapeHtml,
    renderNavbar: renderNavbar,
    statusBadge: statusBadge,
    formatPrice: formatPrice
  };

}(window));

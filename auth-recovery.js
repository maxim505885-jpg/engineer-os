(() => {
  const SUPABASE_URL = "https://jaikhckrwblrkhoizikn.supabase.co";
  const SUPABASE_KEY = "sb_publishable_T8KMHBiql8I6TmUVwX4FXA_1pWvBOQd";
  const auth = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

  const RECOVERY_COOLDOWN = 60 * 1000;
  const recoveryKey = "engineer_os_recovery_last_request";

  function esc(v) {
    return String(v ?? "").replace(/[&<>"']/g, c =>
      ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;" }[c])
    );
  }

  function recoveryRedirect() {
    return window.location.origin + "/?recovery=1";
  }

  function setMessage(text, type = "notice") {
    const el = document.querySelector("#authRecoveryMessage");
    if (!el) return;
    el.className = type === "error" ? "notice" : "notice";
    el.textContent = text;
    el.hidden = false;
  }

  function injectForgotButton() {
    const form = document.querySelector("#authForm");
    if (!form || document.querySelector("#forgotPasswordBtn")) return;

    const btn = document.createElement("button");
    btn.id = "forgotPasswordBtn";
    btn.type = "button";
    btn.className = "btn secondary";
    btn.textContent = "Восстановить пароль";

    const message = document.createElement("div");
    message.id = "authRecoveryMessage";
    message.className = "notice";
    message.hidden = true;
    message.style.marginTop = "8px";

    form.appendChild(btn);
    form.appendChild(message);

    btn.addEventListener("click", async () => {
      const email = document.querySelector("#authEmail")?.value.trim();
      if (!email) {
        setMessage("Сначала укажи e-mail.", "error");
        document.querySelector("#authEmail")?.focus();
        return;
      }

      const last = Number(localStorage.getItem(recoveryKey) || 0);
      const remaining = RECOVERY_COOLDOWN - (Date.now() - last);
      if (remaining > 0) {
        setMessage("Запрос уже отправлялся. Подожди " + Math.ceil(remaining / 1000) + " сек. перед повтором.", "error");
        return;
      }

      btn.disabled = true;
      btn.textContent = "Отправка…";
      setMessage("Отправляем запрос восстановления…");

      const { error } = await auth.auth.resetPasswordForEmail(email, {
        redirectTo: recoveryRedirect()
      });

      if (error) {
        setMessage("Не удалось отправить восстановление: " + error.message, "error");
        btn.disabled = false;
        btn.textContent = "Восстановить пароль";
        return;
      }

      localStorage.setItem(recoveryKey, String(Date.now()));
      setMessage("Запрос отправлен. Проверь почту. Повторная отправка будет доступна через 60 секунд.");
      btn.disabled = true;
      btn.textContent = "Запрос отправлен";
    });
  }

  function showRecoveryForm() {
    const page = document.querySelector("#page");
    if (!page) return;

    page.innerHTML = `
      <div style="max-width:440px;margin:8vh auto">
        <div class="card">
          <div class="eyebrow">ENGINEER OS / PASSWORD RECOVERY</div>
          <h2 style="margin-top:8px">Новый пароль</h2>
          <p class="label">Ссылка восстановления активна. Задай новый пароль для учётной записи.</p>
          <form id="recoveryForm" class="grid" style="margin-top:18px">
            <input id="newPassword" type="password" autocomplete="new-password" minlength="8" placeholder="Новый пароль" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px">
            <input id="newPassword2" type="password" autocomplete="new-password" minlength="8" placeholder="Повтори новый пароль" required style="background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px">
            <button class="btn primary" type="submit">Сохранить пароль</button>
          </form>
          <div id="recoveryResult" class="notice" hidden style="margin-top:12px"></div>
        </div>
      </div>`;

    document.querySelector("#recoveryForm").addEventListener("submit", async e => {
      e.preventDefault();
      const p1 = document.querySelector("#newPassword").value;
      const p2 = document.querySelector("#newPassword2").value;
      const result = document.querySelector("#recoveryResult");

      if (p1 !== p2) {
        result.textContent = "Пароли не совпадают.";
        result.hidden = false;
        return;
      }

      if (p1.length < 8) {
        result.textContent = "Пароль должен содержать не менее 8 символов.";
        result.hidden = false;
        return;
      }

      const { error } = await auth.auth.updateUser({ password: p1 });
      if (error) {
        result.textContent = "Не удалось изменить пароль: " + error.message;
        result.hidden = false;
        return;
      }

      result.textContent = "Пароль изменён. Сейчас вернёмся к входу.";
      result.hidden = false;
      setTimeout(async () => {
        await auth.auth.signOut();
        window.location.href = window.location.origin;
      }, 1200);
    });
  }

  function watchLogin() {
    const observer = new MutationObserver(() => injectForgotButton());
    observer.observe(document.body, { childList: true, subtree: true });
    injectForgotButton();
  }

  auth.auth.onAuthStateChange((event) => {
    if (event === "PASSWORD_RECOVERY") showRecoveryForm();
  });

  if (new URLSearchParams(window.location.search).get("recovery") === "1") {
    setTimeout(showRecoveryForm, 200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watchLogin);
  } else {
    watchLogin();
  }
})();
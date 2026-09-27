/* =========================================================
   Future Era — Landing Page Animation Timeline
   ========================================================= */

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function pick(list) {
  return list.flat().filter(Boolean);
}

function splitWords(el) {
  const lines = el.innerHTML
    .replace(/<br\s*\/?>/gi, "\n")
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  el.textContent = "";
  el.setAttribute("aria-label", lines.join(" ").replace(/\s+/g, " "));

  const lineInners = [];

  lines.forEach((lineText) => {
    const lineEl = document.createElement("span");
    lineEl.className = "title-line";

    const words = lineText.split(/\s+/);
    const lineWords = [];

    words.forEach((word, i) => {
      const mask = document.createElement("span");
      mask.className = "line-mask";
      const inner = document.createElement("span");
      inner.textContent = word;
      mask.appendChild(inner);
      lineEl.appendChild(mask);
      if (i < words.length - 1) lineEl.appendChild(document.createTextNode(" "));
      lineWords.push(inner);
    });

    lineInners.push(lineWords);
    el.appendChild(lineEl);
  });

  return lineInners;
}

function initIntro() {
  const titleEls = gsap.utils.toArray(".intro__title, .intro__title1");
  const subEl = document.querySelector(".intro__subtitle");
  if (!titleEls.length || !subEl) return;

  const titleGroups = titleEls.map((el) => splitWords(el).flat());
  const titleWords = titleGroups.flat();

  const els = {
    eyebrow: document.querySelector(".intro__eyebrow"),
    glowWrap: document.querySelector(".intro__glow-wrap"),
    glow: document.querySelector(".intro__glow"),
    glow2: document.querySelector(".intro__glow-secondary"),
    subtitle: subEl,
    tags: document.querySelectorAll(".intro__tag"),
    actions: document.querySelector(".intro__actions"),
  };

  if (reduceMotion) {
    gsap.set(
      pick([els.eyebrow, els.actions, titleWords, els.subtitle, els.tags, els.glow, els.glow2]),
      { opacity: 1, y: 0, x: 0, scale: 1, yPercent: 0 }
    );
    return;
  }

  // Set initial hidden states
  if (els.eyebrow) gsap.set(els.eyebrow, { opacity: 0, y: -22, scale: 0.92 });
  gsap.set(pick([titleWords]), { yPercent: 120, opacity: 0 });
  gsap.set(pick([els.subtitle]), { opacity: 0, y: 22 });
  gsap.set(pick([els.tags]), { opacity: 0, y: 16, scale: 0.9 });
  gsap.set(pick([els.actions]), { opacity: 0, y: 24 });
  gsap.set(pick([els.glow, els.glow2]), { opacity: 0, scale: 0.6 });

  const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

  // 1. Ambient Glow Bloom
  tl.to(pick([els.glow, els.glow2]), {
    opacity: 1,
    scale: 1,
    duration: 1.8,
    ease: "power2.out",
    stagger: 0.2,
  }, 0);

  // 2. Eyebrow Badge Pop (if present)
  if (els.eyebrow) {
    tl.to(els.eyebrow, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.8,
      ease: "back.out(1.5)",
    }, 0.2);
  }

  // 3. Staggered Masked Title Reveal
  titleGroups.forEach((group, i) => {
    tl.to(
      pick([group]),
      {
        yPercent: 0,
        opacity: 1,
        duration: 0.95,
        stagger: 0.05,
        ease: "power4.out",
      },
      i === 0 ? 0.35 : "-=0.65"
    );
  });

  // 4. Subtitle Smooth Reveal
  tl.to(
    pick([els.subtitle]),
    {
      opacity: 1,
      y: 0,
      duration: 0.85,
      ease: "power2.out",
    },
    "-=0.4"
  );

  // 5. Feature Tag Pills Stagger
  tl.to(
    pick([els.tags]),
    {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.6,
      stagger: 0.07,
      ease: "back.out(1.4)",
    },
    "-=0.5"
  );

  // 6. Action CTA Buttons Reveal
  tl.to(
    pick([els.actions]),
    {
      opacity: 1,
      y: 0,
      duration: 0.75,
      ease: "power3.out",
    },
    "-=0.4"
  );

  // Gentle continuous ambient breathing float for glow orbs
  if (els.glow) {
    gsap.to(els.glow, {
      y: 18,
      x: -12,
      scale: 1.08,
      duration: 5.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });
  }
  if (els.glow2) {
    gsap.to(els.glow2, {
      y: -15,
      x: 14,
      scale: 1.06,
      duration: 6.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      delay: 0.5,
    });
  }

  // Hero parallax scrub on scroll
  gsap.to(".intro__inner", {
    yPercent: -15,
    opacity: 0.2,
    ease: "none",
    scrollTrigger: {
      trigger: ".intro",
      start: "top top",
      end: "bottom top",
      scrub: 0.5,
    },
  });
}

function initAbout() {
  if (reduceMotion) return;

  gsap.utils.toArray("[data-reveal]").forEach((el) => {
    gsap.from(el, {
      y: 50,
      opacity: 0,
      duration: 1.1,
      ease: "expo.out",
      scrollTrigger: { trigger: el, start: "top 85%" },
    });
  });

  gsap.utils.toArray(".card").forEach((card) => {
    const h3 = card.querySelector("h3");
    gsap.from(card.querySelector("p"), {
      y: 20,
      opacity: 0,
      duration: 0.9,
      ease: "power3.out",
      delay: 0.15,
      scrollTrigger: { trigger: card, start: "top 85%" },
    });
    card.addEventListener("mouseenter", () =>
      gsap.to(h3, { letterSpacing: "0.3em", duration: 0.5, ease: "expo.out" })
    );
    card.addEventListener("mouseleave", () =>
      gsap.to(h3, { letterSpacing: "0.2em", duration: 0.5, ease: "expo.out" })
    );
  });
}

/* =========================================================
   Community & Auth / Profile Client Store & Functions
   ========================================================= */

const AUTH_USERS = "future-era:users";
const AUTH_SESSION = "future-era:session";
const PROFILE_KEY = "future-era:profile";
const FOLLOWS_KEY = "future-era:follows:";
const HOME_PAGE = "/";
let RANKED = null;

function esc(text) {
    return String(text == null ? "" : text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function readStore(key, fallback) {
    try {
        const raw = window.localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch (err) {
        return fallback;
    }
}

function writeStore(key, value) {
    try {
        window.localStorage.setItem(key, JSON.stringify(value));
    } catch (err) {
        /* storage unavailable */
    }
}

const sessionOf = () => readStore(AUTH_SESSION, {}) || {};

const userRecord = (email) => {
    const users = readStore(AUTH_USERS, {}) || {};
    return email && users[email] ? users[email] : {};
};

function myGroups() {
    const g = userRecord(sessionOf().email).groups;
    return Array.isArray(g) ? g : [];
}

function setMyGroups(ids) {
    const s = sessionOf();
    if (!s.email) return false;

    const users = readStore(AUTH_USERS, {}) || {};
    const rec = users[s.email] || { name: s.name, email: s.email };
    rec.groups = ids;
    users[s.email] = rec;
    writeStore(AUTH_USERS, users);

    window.dispatchEvent(new CustomEvent("future-era:groups-changed"));
    return true;
}

function announceRanked(data) {
    RANKED = data;
    window.dispatchEvent(new CustomEvent("future-era:ranked", { detail: data }));
}

function showPeopleError(err) {
    const slide = document.getElementById("people-slide");
    if (slide) {
        slide.innerHTML =
            '<p class="people__empty" role="alert">Could not load member list. ' +
            esc(err.message || err) + '</p>';
    }
    if (window.console) console.error("community members load error:", err);
}

function showProfileError(err) {
    if (window.console && console.warn) console.warn("[profile]", err);
}

/* =========================================================
   AUTH MODAL CONTROLLER
   ========================================================= */

function initAuth() {
    const dialog = document.getElementById("auth-dialog");
    const openBtns = Array.from(document.querySelectorAll("[data-auth-open]"));
    if (!dialog || !openBtns.length) return;

    const who = document.querySelector("[data-auth-who]");
    const msg = document.getElementById("auth-msg");
    const closeBtn = dialog.querySelector("[data-auth-close]");
    const tabs = Array.from(dialog.querySelectorAll("[data-auth-tab]"));
    const panels = {
        login: document.getElementById("auth-panel-login"),
        signup: document.getElementById("auth-panel-signup"),
    };

    const digest = (text) => {
        const subtle = window.crypto && window.crypto.subtle;
        if (subtle && window.TextEncoder) {
            return subtle
                .digest("SHA-256", new window.TextEncoder().encode(text))
                .then((buf) =>
                    Array.from(new Uint8Array(buf))
                        .map((b) => b.toString(16).padStart(2, "0"))
                        .join("")
                );
        }
        let h = 0;
        for (let i = 0; i < text.length; i += 1) h = (h * 31 + text.charCodeAt(i)) | 0;
        return Promise.resolve("weak:" + h);
    };

    const looksLikeEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
    const val = (panel, id) => {
        const el = panel.querySelector("#" + id);
        return el ? String(el.value || "").trim() : "";
    };

    const say = (text, ok) => {
        if (!msg) return;
        msg.textContent = text;
        msg.classList.toggle("auth__msg--ok", !!ok);
        msg.classList.add("is-shown");
    };

    const hush = () => {
        if (!msg) return;
        msg.textContent = "";
        msg.classList.remove("is-shown", "auth__msg--ok");
    };

    const setTab = (name) => {
        tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.authTab === name)));
        Object.keys(panels).forEach((key) => {
            if (panels[key]) panels[key].classList.toggle("is-active", key === name);
        });
    };

    const renderWho = () => {
        const session = readStore(AUTH_SESSION, {});
        const signedIn = !!(session && session.email);

        openBtns.forEach((btn) => btn.classList.toggle("is-hidden", signedIn));

        if (who) {
            who.classList.toggle("is-shown", signedIn);
            const badge = who.querySelector("[data-auth-initial]");
            if (badge && signedIn) {
                const seed = String(session.name || session.email || "F").trim();
                badge.textContent = seed.charAt(0).toUpperCase();
            }
            const chipName = who.querySelector("[data-profile-chipname]");
            if (chipName && signedIn) {
                chipName.textContent = session.name || session.email || "Profile";
            }
        }

        window.dispatchEvent(new CustomEvent("future-era:session"));
    };

    const open = (name) => {
        setTab(name || "login");
        hush();

        if (typeof dialog.showModal === "function") {
            if (!dialog.open) dialog.showModal();
        } else {
            dialog.setAttribute("open", "");
        }

        const panel = panels[name] || panels.login;
        const first = panel && panel.querySelector ? panel.querySelector(".inp") : null;
        if (first) window.setTimeout(() => first.focus(), 40);
    };

    const close = () => {
        if (typeof dialog.close === "function") dialog.close();
        else dialog.removeAttribute("open");
    };

    const land = (message, panel) => {
        say(message, true);
        try {
            if (panel && typeof panel.reset === "function") panel.reset();
        } catch (err) {}

        window.setTimeout(() => {
            close();
        }, 900);
    };

    openBtns.forEach((btn) => btn.addEventListener("click", () => open("login")));
    if (closeBtn) closeBtn.addEventListener("click", close);
    window.addEventListener("future-era:open-auth", () => open("login"));

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            setTab(tab.dataset.authTab);
            hush();
        });
    });

    dialog.addEventListener("click", (e) => {
        if (e.target === dialog) close();
    });

    const signout = document.querySelector("[data-auth-signout]");
    if (signout) {
        signout.addEventListener("click", () => {
            try { window.localStorage.removeItem(AUTH_SESSION); } catch (e) {}
            renderWho();
        });
    }

    if (panels.signup) {
        panels.signup.addEventListener("submit", (e) => {
            e.preventDefault();
            const name = val(panels.signup, "auth-signup-name");
            const email = val(panels.signup, "auth-signup-email").toLowerCase();
            const pass = val(panels.signup, "auth-signup-pass");

            if (!name) return say("Please enter your name.");
            if (!looksLikeEmail(email)) return say("That email does not look right.");
            if (pass.length < 6) return say("Password needs to be at least 6 characters.");

            const users = readStore(AUTH_USERS, {});
            if (users[email]) return say("That email is already registered. Try logging in.");

            digest(email + "::" + pass).then((hash) => {
                users[email] = { name, email, hash };
                writeStore(AUTH_USERS, users);
                writeStore(AUTH_SESSION, { name, email });
                renderWho();
                land("Account created. Welcome to FutureEra!", panels.signup);
            });
        });
    }

    if (panels.login) {
        panels.login.addEventListener("submit", (e) => {
            e.preventDefault();
            const email = val(panels.login, "auth-login-email").toLowerCase();
            const pass = val(panels.login, "auth-login-pass");

            if (!looksLikeEmail(email)) return say("That email does not look right.");
            if (!pass) return say("Please enter your password.");

            const users = readStore(AUTH_USERS, {});
            const user = users[email];
            if (!user) return say("No account found with that email. Please sign up.");

            digest(email + "::" + pass).then((hash) => {
                if (hash !== user.hash) return say("Password does not match.");
                writeStore(AUTH_SESSION, { name: user.name, email: user.email });
                renderWho();
                land("Signed in. Welcome back!", panels.login);
            });
        });
    }

    renderWho();
}

/* =========================================================
   PROFILE POPUP CONTROLLER
   ========================================================= */

function initProfile() {
    const dialog = document.getElementById("profile-dialog");
    const openBtns = Array.from(document.querySelectorAll("[data-profile-open]"));
    if (!dialog || !openBtns.length) return;

    const el = {};
    ["initial", "email", "following-count", "followers-count", "group-count", "group-hint",
        "tags", "tags-empty", "following", "following-empty",
        "groups", "groups-empty", "group-choices"].forEach((key) => {
        el[key] = dialog.querySelector("[data-profile-" + key + "]");
    });
    const closeBtn = dialog.querySelector("[data-profile-close]");
    const chipName = document.querySelector("[data-profile-chipname]");

    const session = () => readStore(AUTH_SESSION, {}) || {};
    const record = () => userRecord(session().email);

    const followIds = () => {
        const s = session();
        const list = s.email ? readStore(FOLLOWS_KEY + s.email, []) : [];
        return Array.isArray(list) ? list : [];
    };

    let registry = [];
    let members = {};
    let label = { interests: {}, skills: {}, groups: {} };
    let asked = false;

    const getJSON = (url) => fetch(url).then((res) => {
        if (!res.ok) throw new Error(url + " status " + res.status);
        return res.json();
    });

    const load = () => {
        if (asked) return Promise.resolve();
        asked = true;
        return Promise.all([getJSON("/api/groups"), getJSON("/api/people")])
            .then(([g, p]) => {
                registry = g.groups || [];
                label.groups = {};
                registry.forEach((row) => { label.groups[row.id] = row.label; });

                members = {};
                (p.people || []).forEach((m) => { members[m.id] = m; });

                label.interests = {};
                (p.interests || []).forEach((row) => { label.interests[row.id] = row.label; });
                label.skills = {};
                (p.skills || []).forEach((row) => { label.skills[row.id] = row.label; });
            })
            .catch((err) => {
                asked = false;
                throw err;
            });
    };

    const groupLabel = (id) => label.groups[id] || id;

    const paintTags = () => {
        if (!el.tags) return;
        const picks = readStore(PROFILE_KEY, {}) || {};
        const asList = (v) => (Array.isArray(v) ? v : []);
        const rows = asList(picks.interests)
            .map((id) => ({ text: label.interests[id] || id, kind: "Interest" }))
            .concat(asList(picks.skills).map((id) => ({
                text: label.skills[id] || id, kind: "Skill",
            })));

        el.tags.innerHTML = rows.map((row) =>
            '<li' + (row.kind === "Skill" ? ' class="is-skill"' : "") +
            ' title="' + esc(row.kind) + '">' + esc(row.text) + "</li>").join("");

        if (el["tags-empty"]) el["tags-empty"].hidden = rows.length > 0;
    };

    const paintFollowing = () => {
        const ids = followIds();
        if (el["following-count"]) el["following-count"].textContent = ids.length;
        if (el.following) {
            el.following.innerHTML = ids.map((id) => {
                const m = members[id];
                return "<li><b>" + esc(m ? m.name : id) + "</b>" +
                    '<span class="prof__listsub">' +
                    esc(m ? m.handle || "" : "") + "</span></li>";
            }).join("");
        }
        if (el["following-empty"]) el["following-empty"].hidden = ids.length > 0;
    };

    const paintGroups = () => {
        const mine = myGroups();
        if (el["group-count"]) el["group-count"].textContent = mine.length;
        if (el.groups) {
            el.groups.innerHTML = mine.map((id) => {
                const row = registry.filter((g) => g.id === id)[0];
                return "<li><b>" + esc(groupLabel(id)) + "</b>" +
                    (row && row.members ? ' <span class="prof__listsub">(' + esc(row.members) + " members)</span>" : "") +
                    "</li>";
            }).join("");
        }
        if (el["groups-empty"]) el["groups-empty"].hidden = mine.length > 0;

        if (el["group-choices"]) {
            Array.prototype.forEach.call(
                el["group-choices"].querySelectorAll('input[type="checkbox"]'),
                (box) => { box.checked = mine.indexOf(box.value) !== -1; },
            );
        }
    };

    const paint = () => {
        const s = session();
        const me = record();
        const name = String(me.name || s.name || "").trim();
        const email = me.email || s.email || "";

        const seed = (name || email || "F").trim();
        if (el.initial) el.initial.textContent = seed.charAt(0).toUpperCase();
        if (el.email) el.email.textContent = email;
        if (chipName) chipName.textContent = name || email || "Profile";
        if (el["followers-count"]) el["followers-count"].textContent = "0";

        paintTags();
        paintFollowing();
        paintGroups();
    };

    const buildChoices = () => {
        if (!el["group-choices"]) return;
        const mine = myGroups();
        el["group-choices"].innerHTML = registry.map((row, i) =>
            '<li class="prof__choice" style="display: flex; align-items: center; gap: 8px; margin: 4px 0;">' +
            '<input type="checkbox" id="prof-group-' + i + '" value="' + esc(row.id) + '"' +
            (mine.indexOf(row.id) !== -1 ? " checked" : "") + " />" +
            '<label for="prof-group-' + i + '" style="font-size: 13px; cursor: pointer;">' + esc(row.label) + "</label></li>").join("");

        if (el["group-hint"]) el["group-hint"].textContent = "";
    };

    const close = () => {
        if (dialog.open && typeof dialog.close === "function") dialog.close();
    };

    const open = () => {
        if (!session().email) return;

        if (typeof dialog.showModal === "function") {
            if (!dialog.open) dialog.showModal();
        }

        paint();
        buildChoices();

        load()
            .then(() => { paint(); buildChoices(); })
            .catch((err) => {
                if (el["group-hint"]) el["group-hint"].textContent = "Groups unavailable offline";
                showProfileError(err);
            });
    };

    openBtns.forEach((btn) => btn.addEventListener("click", open));
    if (closeBtn) closeBtn.addEventListener("click", close);
    dialog.addEventListener("click", (e) => { if (e.target === dialog) close(); });

    if (el["group-choices"]) {
        el["group-choices"].addEventListener("change", (e) => {
            const box = e.target.closest ? e.target.closest('input[type="checkbox"]') : null;
            if (!box) return;

            const mine = myGroups();
            const next = box.checked
                ? (mine.indexOf(box.value) === -1 ? mine.concat([box.value]) : mine)
                : mine.filter((id) => id !== box.value);

            setMyGroups(next);
            paint();
        });
    }

    window.addEventListener("future-era:session", () => {
        if (!session().email) close();
        else paint();
    });
}

/* =========================================================
   COMMUNITY PAGE ANIMATIONS & CONTROLLERS
   ========================================================= */

function initCommunity() {
    const section = document.querySelector("#community");
    if (!section) return;

    if (window.gsap && window.ScrollTrigger) {
        gsap.utils.toArray("#community [data-reveal]").forEach((el) => {
            gsap.from(el, {
                y: 40,
                opacity: 0,
                duration: 0.9,
                ease: "expo.out",
                scrollTrigger: { trigger: el, start: "top 88%" },
            });
        });

        gsap.utils.toArray(".channel").forEach((card) => {
            gsap.from(card, {
                y: 30,
                opacity: 0,
                duration: 0.7,
                ease: "power3.out",
                scrollTrigger: { trigger: card, start: "top 88%" },
            });
        });
    }
}

function initCommunityFollow() {
    const slide = document.getElementById("people-slide");
    const interestBox = document.getElementById("people-interests");
    const skillBox = document.getElementById("people-skills");
    const status = document.getElementById("people-status");
    const filter = document.getElementById("people-skill-filter");

    if (!slide || !interestBox || !skillBox) return;

    let vocabulary = { interests: [], skills: [] };
    let label = { interests: {}, skills: {} };
    let mine = { interests: [], skills: [] };

    const stored = readStore(PROFILE_KEY, {}) || {};
    mine.interests = Array.isArray(stored.interests) ? stored.interests : [];
    mine.skills = Array.isArray(stored.skills) ? stored.skills : [];

    const followKey = () => {
        const session = readStore(AUTH_SESSION, {}) || {};
        return session.email ? FOLLOWS_KEY + session.email : "";
    };

    const following = () => {
        const key = followKey();
        const list = key ? readStore(key, []) : [];
        return Array.isArray(list) ? list : [];
    };

    const labelOf = (kind, id) => (label[kind] && label[kind][id]) || id;

    const load = () => {
        const q = new URLSearchParams();
        if (mine.interests.length) q.set("interests", mine.interests.join(","));
        if (mine.skills.length) q.set("skills", mine.skills.join(","));
        const query = q.toString();

        return fetch("/api/people" + (query ? "?" + query : ""))
            .then((res) => {
                if (!res.ok) throw new Error("server error " + res.status);
                return res.json();
            })
            .then((data) => {
                vocabulary = { interests: data.interests || [], skills: data.skills || [] };
                label = {
                    interests: Object.fromEntries(vocabulary.interests.map((t) => [t.id, t.label])),
                    skills: Object.fromEntries(vocabulary.skills.map((t) => [t.id, t.label])),
                };

                if (data.mine) {
                    mine.interests = data.mine.interests || [];
                    mine.skills = data.mine.skills || [];
                }

                renderChips();
                renderPeople(data.people || []);
                announceRanked(data);
            });
    };

    const chip = (kind, id, text) =>
        '<button class="people__chip" type="button" data-tag="' + esc(id) + '" data-kind="' + kind + '"' +
        ' aria-pressed="' + (mine[kind].indexOf(id) > -1 ? "true" : "false") + '">' +
        esc(text) + "</button>";

    const renderChips = () => {
        interestBox.innerHTML = vocabulary.interests
            .map((t) => chip("interests", t.id, t.label))
            .join("");

        const needle = filter ? String(filter.value || "").trim().toLowerCase() : "";
        const shown = vocabulary.skills.filter(
            (t) => !needle || t.label.toLowerCase().indexOf(needle) > -1 || t.id.indexOf(needle) > -1
        );

        skillBox.innerHTML = shown.length
            ? shown.map((t) => chip("skills", t.id, t.label)).join("")
            : '<span class="person__followers">No matching skills found.</span>';
    };

    const toggleTag = (kind, id) => {
        const at = mine[kind].indexOf(id);
        if (at > -1) mine[kind].splice(at, 1);
        else mine[kind].push(id);

        writeStore(PROFILE_KEY, mine);
        load().catch(showPeopleError);
    };

    const card = (person, isFollowed) => {
        const match = person.match || {};
        const scored = match.score !== null && match.score !== undefined;
        const shared = (match.interests || []).concat(match.skills || []);
        const mineSet = new Set(shared);

        const tags = (person.skills || [])
            .slice(0, 4)
            .map((id) => '<span class="tag' + (mineSet.has(id) ? ' tag--shared' : '') + '">' + esc(labelOf("skills", id)) + '</span>')
            .join("");

        const why = scored
            ? (shared.length
                ? "Shares " + (match.interests || []).length + " interests and " + (match.skills || []).length + " skills with you"
                : "Different tech stack, same trajectory")
            : "Pick tags above to compute live match score";

        return (
            '<article class="person' + (isFollowed ? " is-following" : "") + '" role="listitem" data-person="' + esc(person.id) + '">' +
            '<div class="person__top">' +
            '<span class="person__avatar" aria-hidden="true">' + esc(person.name.charAt(0).toUpperCase()) + "</span>" +
            '<span class="person__id">' +
            '<h3 class="person__name">' + esc(person.name) + "</h3>" +
            '<span class="person__handle">' + esc(person.handle || "") + "</span>" +
            "</span>" +
            "</div>" +
            '<span class="person__role">' + esc(person.roleLabel || person.role || "") + "</span>" +
            '<p class="person__blurb">' + esc(person.blurb || "") + "</p>" +
            (tags ? '<div class="person__tags">' + tags + "</div>" : "") +
            '<p class="person__why">' + esc(why) + "</p>" +
            '<div class="person__foot">' +
            '<span class="person__score">' + (scored ? "<b>" + esc(match.score) + "%</b> match" : "not ranked") + "</span>" +
            '<button class="follow' + (isFollowed ? " is-following" : "") + '" type="button" data-follow="' + esc(person.id) + '" aria-pressed="' + (isFollowed ? "true" : "false") + '">' +
            (isFollowed ? "Following" : "Follow") +
            "</button>" +
            "</div>" +
            '<span class="person__followers">' + esc(person.followers || 0) + " followers</span>" +
            "</article>"
        );
    };

    const renderPeople = (list) => {
        const followed = following();
        if (!list.length) {
            slide.innerHTML = '<p class="people__empty">No member suggestions found.</p>';
            return;
        }

        slide.innerHTML = list.map((p) => card(p, followed.indexOf(p.id) > -1)).join("");

        if (status) {
            const bits = [];
            if (mine.interests.length) bits.push(mine.interests.length + " interests");
            if (mine.skills.length) bits.push(mine.skills.length + " skills");
            status.innerHTML = bits.length
                ? list.length + " peers, ranked by your <b>" + bits.join("</b> and <b>") + "</b>"
                : list.length + " peers available, most followed first";
        }
    };

    const flipFollow = (id, button) => {
        const key = followKey();
        if (!key) {
            window.dispatchEvent(new CustomEvent("future-era:open-auth"));
            return;
        }

        const list = following();
        const at = list.indexOf(id);
        const nowFollowing = at === -1;
        if (nowFollowing) list.push(id);
        else list.splice(at, 1);

        writeStore(key, list);

        const article = button.closest(".person");
        if (article) {
            article.classList.toggle("is-following", nowFollowing);
            button.setAttribute("aria-pressed", String(nowFollowing));
            button.classList.toggle("is-following", nowFollowing);
            button.textContent = nowFollowing ? "Following" : "Follow";
        }
    };

    const prev = document.querySelector("[data-people-prev]");
    const next = document.querySelector("[data-people-next]");

    const nudge = (dir) => {
        const cardEl = slide.querySelector(".person");
        const width = cardEl ? cardEl.getBoundingClientRect().width + 20 : 300;
        slide.scrollBy({ left: dir * width * 1.5, behavior: "smooth" });
    };

    if (prev) prev.addEventListener("click", () => nudge(-1));
    if (next) next.addEventListener("click", () => nudge(1));

    interestBox.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-tag]");
        if (btn) toggleTag(btn.dataset.kind, btn.dataset.tag);
    });

    skillBox.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-tag]");
        if (btn) toggleTag(btn.dataset.kind, btn.dataset.tag);
    });

    slide.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-follow]");
        if (btn) flipFollow(btn.dataset.follow, btn);
    });

    if (filter) {
        filter.addEventListener("input", () => renderChips());
    }

    window.addEventListener("future-era:session", () => {
        if (slide.querySelector(".person")) load().catch(showPeopleError);
    });

    load().catch(showPeopleError);
}

function initCommunityGroups() {
    const list = document.getElementById("groups-list");
    const status = document.getElementById("groups-status");
    if (!list) return;

    let rows = [];

    const render = () => {
        const mine = myGroups();
        list.innerHTML = rows.map((g) => {
            const on = mine.indexOf(g.id) > -1;
            const m = g.match || {};
            const scored = m.score !== null && m.score !== undefined;

            return (
                '<li class="group-card' + (on ? " is-joined" : "") + '" data-group="' + esc(g.id) + '">' +
                '<div class="group-card__top" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">' +
                '<h3 class="group-card__title" style="margin: 0;">' + esc(g.label) + "</h3>" +
                '<span class="group-card__members">' + esc(g.members || 0) + " members</span>" +
                "</div>" +
                '<p class="group-card__blurb">' + esc(g.blurb || "") + "</p>" +
                '<p class="group__why" style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">' +
                (scored ? "<b>" + esc(m.score) + "% match</b> for your profile" : "Community discussion group") +
                "</p>" +
                '<button class="group-card__join' + (on ? " is-member" : "") + '" type="button" data-group-join="' + esc(g.id) + '">' +
                (on ? "Joined ✓" : "Join Group") +
                "</button>" +
                "</li>"
            );
        }).join("");
    };

    const flipJoin = (id) => {
        if (!sessionOf().email) {
            window.dispatchEvent(new CustomEvent("future-era:open-auth"));
            return;
        }

        const mine = myGroups();
        const at = mine.indexOf(id);
        const joining = at === -1;
        const next = joining ? mine.concat([id]) : mine.filter((g) => g !== id);

        setMyGroups(next);
        render();
    };

    const onRanked = (e) => {
        const data = e.detail || RANKED;
        if (!data) return;
        rows = data.groups || [];
        if (status) {
            status.textContent = rows.length + " active community hubs matching engineering paths.";
        }
        render();
    };

    list.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-group-join]");
        if (btn) flipJoin(btn.dataset.groupJoin);
    });

    window.addEventListener("future-era:session", render);
    window.addEventListener("future-era:groups-changed", render);
    window.addEventListener("future-era:ranked", onRanked);

    fetch("/api/groups")
        .then((r) => r.json())
        .then((d) => {
            rows = d.groups || [];
            render();
        })
        .catch(() => {});
}

/* =========================================================
   INITIALIZATION
   ========================================================= */

function init() {
    if (window.location.hash) {
        history.replaceState(null, "", window.location.pathname);
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const targetId = this.getAttribute("href");
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: "smooth" });
            }
        });
    });

    if (window.gsap && window.ScrollTrigger) {
        gsap.registerPlugin(ScrollTrigger);
    }

    initIntro();
    initAbout();
    initAuth();
    initProfile();
    initCommunity();
    initCommunityFollow();
    initCommunityGroups();
}

if (document.readyState === "complete") {
    init();
} else {
    window.addEventListener("load", init);
}

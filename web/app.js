/* ==========================================================
   政治理论 · 常识判断 —— 体系化辨析题（四选一 / 间隔重复）
   数据来自 data.js 的 window.QUIZ_DATA
   ========================================================== */
(function () {
  "use strict";

  var DATA = window.QUIZ_DATA || { parts: [] };
  var KEY = "polquiz_v3";
  var OLD_KEYS = ["polquiz_v2", "polquiz_v1"];

  var MIN = 60000, DAY = 86400000;
  var INTERVALS = [0, 10 * MIN, 1 * DAY, 2 * DAY, 4 * DAY, 7 * DAY, 15 * DAY, 30 * DAY, 60 * DAY];
  var MAX_LV = INTERVALS.length - 1;
  var LV_NAME = ["重学", "初记", "巩固", "熟悉", "牢固", "牢固", "牢固", "长期"];

  var DEFAULT = {
    version: 3,
    cards: {},
    favs: {},
    stats: {},
    streak: { last: "", days: 0 },
    settings: { newLimit: 30, batch: 40 },
    theme: "light"
  };
  var store = JSON.parse(JSON.stringify(DEFAULT));

  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} }

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (raw) {
        var o = JSON.parse(raw);
        store = Object.assign(store, o);
        store.settings = Object.assign({ newLimit: 30, batch: 40 }, store.settings || {});
        store.streak = Object.assign({ last: "", days: 0 }, store.streak || {});
        store.cards = store.cards || {};
        store.stats = store.stats || {};
        return;
      }
      // 旧版本只保留「收藏」，答题记录因题目全换了，不再迁移
      for (var k = 0; k < OLD_KEYS.length; k++) {
        var old = localStorage.getItem(OLD_KEYS[k]);
        if (old) {
          try {
            var v = JSON.parse(old);
            if (v.favs) store.favs = v.favs;
            if (v.theme) store.theme = v.theme;
          } catch (e) {}
          break;
        }
      }
    } catch (e) {}
  }

  function dayKey(d) {
    d = d || new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function startOfToday() { var d = new Date(); d.setHours(0, 0, 0, 0); return d.getTime(); }

  /* ---------------- 索引 ---------------- */
  var leaves = [], ALL_Q = [], nodeByKey = {}, openState = {};

  (function buildIndex(nodes, path) {
    nodes.forEach(function (n) {
      if (n.qs) {
        n.path = path.concat([n.title]);
        leaves.push(n);
        n.qs.forEach(function (q) { q.sec = n; });
        ALL_Q = ALL_Q.concat(n.qs);
      } else {
        buildIndex(n.children || [], path.concat([n.title]));
      }
    });
  })(DATA.parts, []);

  function qsOf(node) {
    if (node.qs) return node.qs;
    var out = [];
    (function rec(n) {
      if (n.qs) { out = out.concat(n.qs); return; }
      (n.children || []).forEach(rec);
    })(node);
    return out;
  }
  function totalOf(node) {
    if (node.__total === undefined) {
      node.__total = node.qs ? node.qs.length
        : (node.children || []).reduce(function (s, c) { return s + totalOf(c); }, 0);
    }
    return node.__total;
  }

  /* ---------------- 记忆调度 ---------------- */
  function isLearned(q) { return !!store.cards[q.id]; }
  function isDue(q) { var c = store.cards[q.id]; return c && c.due <= Date.now(); }
  function dueItems() {
    return ALL_Q.filter(isDue).sort(function (a, b) { return store.cards[a.id].due - store.cards[b.id].due; });
  }
  function newItems() { return ALL_Q.filter(function (q) { return !store.cards[q.id]; }); }
  function newToday() {
    var t = startOfToday(), n = 0;
    for (var id in store.cards) { var c = store.cards[id]; if (c.seen === 1 && c.last >= t) n++; }
    return n;
  }

  function grade(q, correct) {
    var now = Date.now();
    var c = store.cards[q.id] || { lv: 0, seen: 0, ok: 0, wrong: 0, last: 0 };
    c.seen = (c.seen || 0) + 1;
    c.last = now;
    if (correct) {
      c.lv = Math.min((c.lv || 0) + 1, MAX_LV);
      c.ok = (c.ok || 0) + 1;
      c.due = now + INTERVALS[c.lv];
    } else {
      c.lv = 0;
      c.wrong = (c.wrong || 0) + 1;
      c.due = now + 8 * MIN;
    }
    store.cards[q.id] = c;

    var d = dayKey();
    var s = store.stats[d] || (store.stats[d] = { n: 0, ok: 0, new: 0 });
    s.n++; if (correct) s.ok++;
    if (c.seen === 1) s.new++;

    var y = dayKey(new Date(now - DAY));
    if (store.streak.last !== d) {
      store.streak.days = (store.streak.last === y) ? (store.streak.days || 0) + 1 : 1;
      store.streak.last = d;
    }
    save();
  }

  /* ---------------- DOM 工具 ---------------- */
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ---------------- 统计 ---------------- */
  function refreshStats() {
    var learned = 0;
    for (var i = 0; i < ALL_Q.length; i++) if (isLearned(ALL_Q[i])) learned++;
    var due = dueItems().length;
    $("statTotal").textContent = ALL_Q.length;
    $("statLearned").textContent = learned;
    $("statDue").textContent = due;

    var nNew = Math.max(0, store.settings.newLimit - newToday());
    $("dueN").textContent = due > 99 ? "99+" : due;
    $("newN").textContent = nNew;
    var s = store.stats[dayKey()] || { n: 0 };
    $("doneN").textContent = s.n;
    $("streak").textContent = store.streak.days > 1 ? "🔥 连续 " + store.streak.days + " 天" : "";
    $("startToday").textContent = (due + Math.min(nNew, 20)) ? "开始今日复习" : "开始学新题";
    $("todaySub").textContent = due ? "先清 " + Math.min(due, 40) + " 道到期题，再学新的" : "暂无到期题，今天可以学新内容";
  }

  /* ---------------- 侧栏树 ---------------- */
  function renderTree() {
    var host = $("tree");
    host.innerHTML = "";
    nodeByKey = {};
    buildTree(DATA.parts, 0, host, "");
    markActive();
    expandInitial();
    updateCounts();
  }

  function learnedIn(node, memo) {
    if (memo[node.__key] !== undefined) return memo[node.__key];
    var c;
    if (node.qs) {
      c = 0;
      for (var i = 0; i < node.qs.length; i++) if (isLearned(node.qs[i])) c++;
    } else {
      c = 0;
      for (var j = 0; j < node.children.length; j++) c += learnedIn(node.children[j], memo);
    }
    memo[node.__key] = c;
    return c;
  }

  function updateCounts() {
    var memo = {};
    var rows = document.querySelectorAll(".node-row[data-key]");
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var n = nodeByKey[r.dataset.key];
      if (!n) continue;
      var tot = totalOf(n), done = learnedIn(n, memo);
      var cnt = r.querySelector(".cnt");
      cnt.textContent = done + "/" + tot;
      cnt.className = "cnt" + (done === tot ? " done" : (done ? " some" : ""));
    }
    refreshStats();
  }

  function buildTree(nodes, level, parentEl, parentKey) {
    nodes.forEach(function (n, i) {
      var key = parentKey + "/" + i;
      n.__key = key;
      nodeByKey[key] = n;
      var isLeaf = !!n.qs;

      var wrap = document.createElement("div");
      wrap.className = "node lv" + Math.min(level, 3);

      var row = document.createElement("div");
      row.className = "node-row";
      row.dataset.key = key;

      var caret = document.createElement("span");
      caret.className = "caret";
      caret.textContent = isLeaf ? "" : "▶";

      var label = document.createElement("span");
      label.className = "label";
      label.textContent = n.title;
      label.title = n.title;

      var cnt = document.createElement("span");
      cnt.className = "cnt";

      row.appendChild(caret);
      row.appendChild(label);
      if (!isLeaf) {
        var play = document.createElement("button");
        play.className = "mini-play";
        play.textContent = "练";
        play.title = "练习本节";
        play.addEventListener("click", function (ev) {
          ev.stopPropagation();
          startCustom(qsOf(n), n.title, n, "seq");
        });
        row.appendChild(play);
      }
      row.appendChild(cnt);
      wrap.appendChild(row);

      var childBox = null;
      if (!isLeaf) {
        childBox = document.createElement("div");
        childBox.className = "children";
        if (openState[key]) { childBox.classList.add("open"); caret.classList.add("open"); }
        wrap.appendChild(childBox);
        buildTree(n.children || [], level + 1, childBox, key);
      }
      parentEl.appendChild(wrap);

      row.addEventListener("click", function () {
        if (isLeaf) startCustom(n.qs, n.title, n, "seq");
        else toggleNode(childBox, caret, key);
      });
    });
  }

  function toggleNode(childBox, caret, key) {
    if (!childBox) return;
    var open = childBox.classList.toggle("open");
    caret.classList.toggle("open", open);
    openState[key] = open;
  }

  function markActive() {
    var rows = document.querySelectorAll(".node-row.active");
    for (var i = 0; i < rows.length; i++) rows[i].classList.remove("active");
    if (session.scope && session.scope.__key) {
      var r = document.querySelector('.node-row[data-key="' + session.scope.__key + '"]');
      if (r) r.classList.add("active");
    }
  }

  function expandInitial() {
    var host = $("tree");
    host.querySelectorAll(".lv0 > .children, .lv1 > .children").forEach(function (c) {
      c.classList.add("open");
      var row = c.parentElement.querySelector(".node-row");
      if (row) {
        var caret = row.querySelector(".caret");
        if (caret) caret.classList.add("open");
        openState[row.dataset.key] = true;
      }
    });
  }

  /* ---------------- 会话 ---------------- */
  var session = { items: [], pos: 0, mode: "seq", title: "", scope: null, answered: {}, retries: {}, nextKey: 0 };

  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function setSession(items, mode, title, scope) {
    if (tvOpen) closeTreeViewOnly();
    session = {
      items: items.map(function (q, i) { return { q: q, key: i }; }),
      pos: 0, mode: mode, title: title, scope: scope || null,
      answered: {}, retries: {}, nextKey: items.length
    };
    $("card").hidden = false;
    $("empty").hidden = true;
    $("scopeTitle").textContent = title + "（" + items.length + " 题）";
    markActive();
    syncModeButtons(mode);
    renderCard();
  }

  function showEmpty(title, html) {
    if (tvOpen) closeTreeViewOnly();
    session = { items: [], pos: 0, mode: "seq", title: title, scope: null, answered: {}, retries: {}, nextKey: 0 };
    $("scopeTitle").textContent = title;
    $("card").hidden = true;
    $("empty").hidden = false;
    $("empty").innerHTML = html;
    markActive();
  }

  function startToday() {
    var due = dueItems();
    var canNew = Math.max(0, store.settings.newLimit - newToday());
    var fresh = newItems().slice(0, canNew);
    var batch = due.slice(0, store.settings.batch).concat(fresh);
    if (!batch.length) {
      showEmpty("今日复习", "<b>今天的任务完成了 🎉</b><br><br>没有到期题目，新学额度也用完了。<br>" +
        "可以去左侧章节里自由练习，或者明天再来——遗忘曲线会自动把该复习的题送回来。");
      return;
    }
    setSession(batch, "today", "今日复习", null);
  }

  function startCustom(items, title, scope, mode) {
    if (!items.length) { showEmpty(title, "这里还没有题目"); return; }
    var arr = items.slice();
    if (mode === "random") shuffle(arr);
    setSession(arr, mode, title, scope);
  }

  function startWrong() {
    var items = ALL_Q.filter(function (q) { var c = store.cards[q.id]; return c && (c.lv || 0) === 0 && c.wrong > 0; });
    if (!items.length) { showEmpty("错题重练", "还没有错题，先去做今日复习吧 👈"); return; }
    setSession(shuffle(items), "wrong", "错题重练", null);
  }

  function startFav() {
    var items = ALL_Q.filter(function (q) { return store.favs[q.id]; });
    if (!items.length) { showEmpty("我的收藏", "还没有收藏，点题目右上角的 ☆ 收藏"); return; }
    setSession(items.slice(), "fav", "我的收藏", null);
  }

  function syncModeButtons(mode) {
    document.querySelectorAll(".mode-btn").forEach(function (b) {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
  }

  /* ---------------- 渲染 ---------------- */
  function cur() { return session.items[session.pos] || null; }

  var LETTER = ["A", "B", "C", "D"];
  var CN_NUM = "〇一二三四五六七八九十十一十二十三十四十五十六十七十八十九二十";

  function cnNum(n) {
    var map = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
      "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"];
    return map[n] || String(n);
  }

  function renderCard() {
    var entry = cur();
    if (!entry) { finish(); return; }
    var q = entry.q, key = entry.key;

    var sec = q.sec || {};
    var pathArr = sec.path || [];
    var path = pathArr.join(" / ");
    $("qTitle").textContent = sec.title || "";
    $("qTitle").title = sec.title || "";
    $("path").textContent = pathArr.slice(0, -1).join(" / ");
    $("path").title = path;

    var c = store.cards[q.id];
    var badge = $("cardBadge");
    if (!c) { badge.textContent = "新题"; badge.className = "badge new"; }
    else { badge.textContent = LV_NAME[c.lv] || "重学"; badge.className = "badge lv" + c.lv; }

    var fav = $("favBtn");
    fav.classList.toggle("on", !!store.favs[q.id]);
    fav.textContent = store.favs[q.id] ? "★" : "☆";

    $("counter").textContent = (session.pos + 1) + " / " + session.items.length;
    $("qNo").textContent = String(session.pos + 1).padStart(2, "0");
    $("barFill").style.width = ((session.pos + 1) / session.items.length * 100) + "%";

    var ans = session.answered[key];
    var answered = !!ans;

    /* 题干 */
    var st = $("statement");
    st.innerHTML = "";
    var text = String(q.q || "").replace(/_{2,}/g, "（　　）");
    st.textContent = text;

    /* 选项 */
    var box = $("options");
    box.innerHTML = "";
    (q.o || []).forEach(function (o, i) {
      var b = document.createElement("button");
      b.className = "opt";
      b.innerHTML = "<span class='key'>" + LETTER[i] + "</span><span class='txt'></span>";
      b.querySelector(".txt").textContent = o;
      if (answered) {
        b.disabled = true;
        if (i === q.a) b.classList.add("right");
        else if (i === ans.picked) b.classList.add("wrong");
        else b.classList.add("dim");
      } else {
        b.addEventListener("click", function () { pick(i); });
      }
      box.appendChild(b);
    });

    /* 反馈 */
    var fb = $("feedback");
    if (answered) {
      fb.hidden = false;
      var good = ans.ok;
      fb.className = "feedback " + (good ? "ok" : "bad");
      var head = ans.cheated
        ? "已看答案：" + LETTER[q.a] + " " + esc(q.o[q.a])
        : (good ? "✓ 答对了" : "✗ 正确答案：" + LETTER[q.a] + " " + esc(q.o[q.a]));
      var body = "";
      if (q.why) body += "<div class='why'><b>解析：</b>" + esc(q.why) + "</div>";
      if (q.at) body += "<div class='at'><b>体系位置：</b>" + esc(q.at) +
        " <a href='javascript:void 0' class='link' id='fbTree'>看体系图 ›</a></div>";
      fb.innerHTML = "<div class='fb-head'>" + head + "</div>" + body;
      var fbTree = document.getElementById("fbTree");
      if (fbTree) fbTree.addEventListener("click", function () { openTree(q); });
    } else {
      fb.hidden = true;
    }

    $("prevBtn").disabled = session.pos === 0;
    $("nextBtn").textContent = session.pos === session.items.length - 1 ? "完成本轮" : "下一题";
    $("revealBtn").style.visibility = answered ? "hidden" : "visible";
    $("footHint").textContent = answered ? "Enter 进入下一题" : "按 1–4 选答案，Enter 下一题";
  }

  /* ---------------- 作答 ---------------- */
  function afterGrade(entry, correct) {
    var q = entry.q;
    var n = session.retries[q.id] || 0;
    if (!correct && n < 1) {
      session.retries[q.id] = n + 1;
      var at = Math.min(session.pos + 3, session.items.length);
      session.items.splice(at, 0, { q: q, key: session.nextKey++ });
    }
    renderCard();
    updateCounts();
  }

  function pick(i) {
    var entry = cur();
    if (!entry) return;
    var q = entry.q;
    if (session.answered[entry.key]) return;
    var good = i === q.a;
    session.answered[entry.key] = { ok: good, picked: i };
    grade(q, good);
    afterGrade(entry, good);
  }

  function reveal() {
    var entry = cur();
    if (!entry) return;
    var q = entry.q;
    if (session.answered[entry.key]) return;
    session.answered[entry.key] = { ok: false, picked: -1, cheated: true };
    grade(q, false);
    renderCard();
    updateCounts();
  }

  function next() {
    if (session.pos < session.items.length - 1) { session.pos++; renderCard(); }
    else finish();
  }
  function prev() {
    if (session.pos > 0) { session.pos--; renderCard(); }
  }

  function finish() {
    var ok = 0, total = 0;
    for (var k in session.answered) { total++; if (session.answered[k].ok) ok++; }
    var rate = total ? Math.round(ok / total * 100) : 0;
    var due = dueItems().length;
    $("card").hidden = true;
    $("empty").hidden = false;
    $("empty").innerHTML =
      "<b>本轮完成！</b><br>作答 " + total + " 道 · 正确 " + ok + " · 正确率 " + rate + "%" +
      "<br><br>现在还有 <b>" + due + "</b> 道到期；答错的题 8 分钟后会回到复习队列。" +
      "<br>明天再来，系统会按间隔自动安排复习。<br><br>" +
      "<button class='primary-btn' id='goToday'>再练一轮</button> " +
      "<button class='ghost-btn' id='goWrong'>去练错题</button>";
    $("scopeTitle").textContent = "本轮结束";
    setTimeout(function () {
      var a = $("goToday"), b = $("goWrong");
      if (a) a.addEventListener("click", startToday);
      if (b) b.addEventListener("click", startWrong);
    }, 0);
    updateCounts();
  }

  /* ---------------- 体系图（整页） ---------------- */
  var ACCENTS = ["#b3261e", "#b07a17", "#1f6feb", "#1e7a46", "#8b5cf6", "#0f766e", "#c2410c"];
  var CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳";
  var tvOpen = false;

  function splitMark(text) {
    var t = String(text || "");
    var m = t.match(/^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)$/);
    if (m) return { mark: m[1], text: m[2] };
    m = t.match(/^(\d+)\s*[.、．]\s*(.*)$/);
    if (m) return { mark: m[1], text: m[2] };
    m = t.match(/^([一二三四五六七八九十]+)\s*[、.．]\s*(.*)$/);
    if (m) return { mark: m[1], text: m[2] };
    return { mark: "", text: t };
  }

  function countLeaves(n) {
    if (!n.ch || !n.ch.length) return 1;
    return n.ch.reduce(function (s, c) { return s + countLeaves(c); }, 0);
  }

  function hlMatch(name, hl) {
    var nn = String(name).replace(/[\s①-⑳]/g, "");
    return hl.some(function (h) {
      var hh = h.replace(/[\s①-⑳]/g, "");
      return hh && nn && (nn === hh || nn.indexOf(hh) >= 0 || hh.indexOf(nn) >= 0);
    });
  }

  function openTree(q) {
    var sec = q.sec;
    if (!sec) return;
    var hl = String(q.at || "").split(/[›>]/).map(function (s) { return s.replace(/\s/g, ""); }).filter(Boolean);

    $("tvTitle").textContent = sec.title;
    $("tvPath").textContent = (sec.path || []).join("  /  ");

    var chips = $("tvChips");
    var body = $("tvBody");
    chips.innerHTML = "";
    body.innerHTML = "";

    var tree = sec.tree || [];
    if (!tree.length) {
      body.innerHTML = "<p class='tv-empty'>本节暂无体系图，可以直接看解析。</p>";
    }

    tree.forEach(function (n1, i) {
      var accent = ACCENTS[i % ACCENTS.length];
      var id = "tvsec" + i;

      var chip = document.createElement("button");
      chip.className = "tv-chip";
      chip.style.setProperty("--accent", accent);
      var cn = document.createElement("b");
      cn.textContent = n1.t;
      var cc = document.createElement("i");
      cc.textContent = countLeaves(n1);
      chip.appendChild(cn);
      chip.appendChild(cc);
      chip.addEventListener("click", function () {
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      chips.appendChild(chip);

      body.appendChild(renderTvSection(n1, i, accent, id, hl));
    });

    $("treeView").hidden = false;
    $("stage").hidden = true;
    $("topbar").style.display = "none";
    tvOpen = true;
    window.scrollTo(0, 0);

    if (hl.length) {
      setTimeout(function () {
        var hit = $("tvBody").querySelector(".tv-hit");
        if (hit) hit.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 60);
    }
  }

  function renderTvSection(n1, i, accent, id, hl) {
    var secEl = document.createElement("section");
    secEl.className = "tv-sec";
    secEl.id = id;
    secEl.style.setProperty("--accent", accent);

    var head = document.createElement("div");
    head.className = "tv-sec-h";
    var num = document.createElement("span");
    num.className = "tv-sec-num";
    num.textContent = cnNum(i + 1) + "、";
    var tt = document.createElement("div");
    tt.className = "tv-sec-tt";
    var b = document.createElement("b");
    b.textContent = n1.t;
    tt.appendChild(b);
    if (n1.d) {
      var d = document.createElement("p");
      d.textContent = n1.d;
      tt.appendChild(d);
    }
    var cnt = document.createElement("span");
    cnt.className = "tv-sec-cnt";
    cnt.textContent = countLeaves(n1) + " 项";

    head.appendChild(num);
    head.appendChild(tt);
    head.appendChild(cnt);
    if (hlMatch(n1.t, hl)) head.classList.add("tv-sec-hit");
    secEl.appendChild(head);

    var bodyWrap = document.createElement("div");
    bodyWrap.className = "tv-sec-body";
    secEl.appendChild(bodyWrap);

    head.addEventListener("click", function () { secEl.classList.toggle("closed"); });

    (n1.ch || []).forEach(function (n2, j) {
      bodyWrap.appendChild(renderTvCard(n2, i, j, accent, hl));
    });

    return secEl;
  }

  function renderTvCard(n2, i, j, accent, hl) {
    var card = document.createElement("article");
    card.className = "tv-card";
    card.style.setProperty("--accent", accent);

    var head = document.createElement("div");
    head.className = "tv-card-h";
    var no = document.createElement("span");
    no.className = "tv-card-no";
    no.textContent = "（" + cnNum(j + 1) + "）";
    var tt = document.createElement("div");
    tt.className = "tv-card-tt";
    var b = document.createElement("b");
    b.textContent = n2.t;
    tt.appendChild(b);
    if (n2.d) {
      var d = document.createElement("p");
      d.textContent = n2.d;
      tt.appendChild(d);
    }
    head.appendChild(no);
    head.appendChild(tt);
    if (n2.ch && n2.ch.length) {
      var badge = document.createElement("span");
      badge.className = "tv-card-cnt";
      badge.textContent = n2.ch.length;
      head.appendChild(badge);
    }
    card.appendChild(head);

    if (n2.ch && n2.ch.length) {
      card.appendChild(renderTvList(n2.ch, 1, hl));
    }
    return card;
  }

  function renderTvList(nodes, level, hl) {
    var ul = document.createElement("ul");
    ul.className = "tv-list lv" + Math.min(level, 3);
    nodes.forEach(function (n, idx) {
      var li = document.createElement("li");
      li.className = "tv-li" + (hlMatch(n.t, hl) ? " tv-hit" : "");

      var mk = document.createElement("span");
      mk.className = "tv-mark";
      var sm = splitMark(n.t);
      mk.textContent = sm.mark || (level > 1 ? "" : (idx + 1));
      if (!mk.textContent) mk.classList.add("dot");

      var wrap = document.createElement("div");
      wrap.className = "tv-li-main";
      var txt = document.createElement("span");
      txt.className = "tv-li-t";
      txt.textContent = sm.text;
      wrap.appendChild(txt);
      if (n.d) {
        var dd = document.createElement("span");
        dd.className = "tv-li-d";
        dd.textContent = n.d;
        wrap.appendChild(dd);
      }
      li.appendChild(mk);
      li.appendChild(wrap);
      ul.appendChild(li);

      if (n.ch && n.ch.length) {
        var sub = document.createElement("li");
        sub.className = "tv-sub";
        sub.appendChild(renderTvList(n.ch, level + 1, hl));
        ul.appendChild(sub);
      }
    });
    return ul;
  }

  function closeTreeViewOnly() {
    $("treeView").hidden = true;
    $("stage").hidden = false;
    $("topbar").style.display = "";
    tvOpen = false;
  }

  function closeTree() {
    closeTreeViewOnly();
    window.scrollTo(0, 0);
  }
  /* ---------------- 搜索 ---------------- */
  function doSearch(text) {
    var box = $("searchResult");
    text = text.trim();
    if (!text) { box.hidden = true; box.innerHTML = ""; return; }
    var hits = ALL_Q.filter(function (q) {
      if (q.q.indexOf(text) >= 0) return true;
      for (var i = 0; i < (q.o || []).length; i++) if (String(q.o[i]).indexOf(text) >= 0) return true;
      return (q.why || "").indexOf(text) >= 0;
    });
    box.hidden = false;
    if (!hits.length) { box.innerHTML = "<div class='sr-empty'>没有匹配的题目</div>"; return; }
    box.innerHTML = "";
    var head = document.createElement("div");
    head.className = "sr-item";
    head.style.color = "var(--brand)";
    head.innerHTML = "<b>练习这 " + hits.length + " 道题</b>";
    head.addEventListener("click", function () {
      box.hidden = true;
      startCustom(hits, "搜索：" + text, null, "seq");
    });
    box.appendChild(head);
    hits.slice(0, 8).forEach(function (q) {
      var d = document.createElement("div");
      d.className = "sr-item";
      d.textContent = String(q.q).slice(0, 34) + "…";
      d.addEventListener("click", function () {
        box.hidden = true;
        startCustom(hits, "搜索：" + text, null, "seq");
        for (var i = 0; i < session.items.length; i++) {
          if (session.items[i].q === q) { session.pos = i; break; }
        }
        renderCard();
      });
      box.appendChild(d);
    });
  }

  /* ---------------- 初始化 ---------------- */
  function init() {
    load();
    if (store.theme === "dark") document.documentElement.setAttribute("data-theme", "dark");
    $("themeBtn").textContent = store.theme === "dark" ? "切换日间模式" : "切换夜间模式";

    renderTree();

    var due = dueItems().length;
    if (due > 0 || newItems().length) startToday();
    else showEmpty("今日复习", "今天的任务完成了 🎉");

    $("startToday").addEventListener("click", startToday);
    $("nextBtn").addEventListener("click", next);
    $("prevBtn").addEventListener("click", prev);
    $("revealBtn").addEventListener("click", reveal);
    $("treeBtn").addEventListener("click", function () { var e = cur(); if (e) openTree(e.q); });
    $("tvBack").addEventListener("click", closeTree);
    $("tvBack2").addEventListener("click", closeTree);
    $("tvFloat").addEventListener("click", closeTree);
    $("tvToggle").addEventListener("click", function () {
      var secs = document.querySelectorAll(".tv-sec");
      var anyOpen = false;
      for (var i = 0; i < secs.length; i++) if (!secs[i].classList.contains("closed")) anyOpen = true;
      for (var j = 0; j < secs.length; j++) secs[j].classList.toggle("closed", anyOpen);
      $("tvToggle").textContent = anyOpen ? "展开分节" : "收起分节";
    });

    $("newLimit").value = String(store.settings.newLimit);
    $("newLimit").addEventListener("change", function (e) {
      store.settings.newLimit = parseInt(e.target.value, 10) || 30;
      save(); refreshStats();
    });

    $("favBtn").addEventListener("click", function () {
      var e = cur();
      if (!e) return;
      var id = e.q.id;
      if (store.favs[id]) delete store.favs[id]; else store.favs[id] = 1;
      save(); renderCard();
    });

    document.querySelectorAll(".mode-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        var m = b.dataset.mode;
        if (m === "wrong") startWrong();
        else if (m === "fav") startFav();
        else if (session.scope) startCustom(qsOf(session.scope), session.scope.title, session.scope, m);
        else startCustom(ALL_Q, "全部题目", null, m);
      });
    });

    $("search").addEventListener("input", function (e) { doSearch(e.target.value); });

    $("themeBtn").addEventListener("click", function () {
      store.theme = store.theme === "dark" ? "light" : "dark";
      if (store.theme === "dark") document.documentElement.setAttribute("data-theme", "dark");
      else document.documentElement.removeAttribute("data-theme");
      $("themeBtn").textContent = store.theme === "dark" ? "切换日间模式" : "切换夜间模式";
      save();
    });

    $("resetBtn").addEventListener("click", function () {
      if (!confirm("确定清空全部学习记录（复习进度、收藏、统计）吗？")) return;
      store = JSON.parse(JSON.stringify(DEFAULT));
      save();
      renderTree(); startToday();
    });

    $("expandAll").addEventListener("click", function () {
      document.querySelectorAll(".children").forEach(function (c) { c.classList.add("open"); });
      document.querySelectorAll(".caret").forEach(function (c) { if (c.textContent) c.classList.add("open"); });
    });
    $("collapseAll").addEventListener("click", function () {
      document.querySelectorAll(".children").forEach(function (c) { c.classList.remove("open"); });
      document.querySelectorAll(".caret").forEach(function (c) { c.classList.remove("open"); });
    });

    $("menuBtn").addEventListener("click", function () {
      $("sidebar").classList.add("open");
      $("overlay").classList.add("show");
    });
    $("overlay").addEventListener("click", function () {
      $("sidebar").classList.remove("open");
      $("overlay").classList.remove("show");
    });

    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
      if (e.key === "Escape") { if (tvOpen) closeTree(); return; }
      if (tvOpen) return;
      var entry = cur();
      if (!entry) return;
      if (e.key >= "1" && e.key <= "4") {
        var i = parseInt(e.key, 10) - 1;
        if (!session.answered[entry.key] && entry.q.o[i] !== undefined) pick(i);
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (session.answered[entry.key]) next();
      } else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();



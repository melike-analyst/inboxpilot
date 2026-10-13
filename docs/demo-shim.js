/* Static demo backend: replaces fetch() for /stats, /tickets and /triage so the
 * dashboard runs on GitHub Pages with no server. Logic mirrors api/app/rules.py. */
(function () {
  const CATS = {
    billing: ["invoice","refund","charge","payment","bill","receipt","fatura","ödeme","iade","ücret"],
    technical: ["error","bug","crash","not working","doesn't work","login","password","broken","hata","çalışmıyor","giriş","şifre"],
    sales: ["price","pricing","quote","demo","plan","enterprise","fiyat","teklif"],
    complaint: ["terrible","worst","unacceptable","angry","complaint","disappointed","şikayet","rezalet","memnun değil"],
  };
  const URGENT = ["urgent","asap","immediately","outage","acil","hemen","production down"];
  const HIGH = ["refund","cannot","can't","broken","not working","charged twice","iade","çalışmıyor","hata","unacceptable","rezalet"];
  const NEG = ["terrible","worst","angry","disappointed","unacceptable","broken","bad","rezalet","kötü","şikayet","berbat"];
  const POS = ["thanks","thank you","great","love","awesome","perfect","teşekkür","harika","süper"];
  const KB = [
    ["refunds.md", "refund charged twice payment invoice order card", "Refunds are available within 14 days of purchase. Reply to the invoice email with your order number. Approved refunds return to the original payment method within 5-7 business days."],
    ["account.md", "password reset login forgot email access", "Use \"Forgot password\" on the login page. The reset link is valid for 30 minutes. If you do not receive the email, check the spam folder and wait 5 minutes before retrying."],
    ["pricing.md", "price pricing plan plans demo quote enterprise pro starter", "We offer Starter, Pro and Enterprise plans. A 30-minute demo can be booked with the sales team, and Enterprise quotes are prepared within 2 business days after the demo."],
  ];
  const count = (t, ws) => ws.filter(w => t.includes(w)).length;

  function classify(message, subject) {
    const text = ((subject || "") + " " + message).toLowerCase();
    let best = "general", bestScore = 0;
    for (const [c, ws] of Object.entries(CATS)) { const n = count(text, ws); if (n > bestScore) { best = c; bestScore = n; } }
    let priority = "low";
    if (count(text, URGENT)) priority = "urgent";
    else if (best === "complaint" || count(text, HIGH)) priority = "high";
    else if (["sales","billing","technical"].includes(best)) priority = "medium";
    const neg = count(text, NEG), pos = count(text, POS);
    const sentiment = neg > pos ? "negative" : pos > neg ? "positive" : "neutral";
    let summary = message.replace(/\s+/g, " ").trim();
    if (summary.length > 140) summary = summary.slice(0, 137) + "...";
    return { category: best, priority, sentiment, summary, text };
  }

  function retrieve(text) {
    const words = new Set(text.split(/[^\p{L}']+/u).filter(w => w.length > 2));
    let top = null, topScore = 0;
    for (const [src, kw, body] of KB) {
      const s = kw.split(" ").filter(w => words.has(w)).length;
      if (s > topScore) { top = [src, body]; topScore = s; }
    }
    return top;
  }

  const SEEDS = [
    ["email","ayse@example.com","Invoice problem","I was charged twice this month. Please refund the extra payment."],
    ["web","john@example.com","Cannot login","URGENT: login is not working and our team is blocked."],
    ["telegram","mehmet",null,"Kurumsal plan için fiyat teklifi alabilir miyim?"],
    ["web","sara@example.com","Thanks","Thanks, the new dashboard is great!"],
    ["email","tom@example.com","Terrible experience","This is the worst support I have seen. I am very disappointed."],
    ["web","elif@example.com","Password reset","I forgot my password and the reset email never arrives."],
    ["form","can@example.com","Demo request","We would like a demo of the Pro plan for our team."],
    ["email","zeynep@example.com","Fatura","Faturamda hata var, iade istiyorum."],
  ];

  const tickets = [];
  function triage(m) {
    const r = classify(m.message, m.subject);
    const hit = retrieve(r.text);
    const name = m.sender ? m.sender.split("@")[0] : "there";
    const body = hit ? hit[1] : `We received your ${r.category} request and a team member will reply soon.`;
    const t = {
      id: tickets.length + 1, created_at: new Date().toISOString(), source: m.source || "web",
      sender: m.sender || null, subject: m.subject || null, message: m.message,
      category: r.category, priority: r.priority, sentiment: r.sentiment, summary: r.summary,
      suggested_reply: `Hi ${name},\n\nThanks for reaching out.\n\n${body}\n\nBest regards,\nSupport Team`,
      kb_sources: hit ? hit[0] : "", provider: "rules (in-browser demo)",
    };
    tickets.push(t);
    return t;
  }
  SEEDS.forEach(([source, sender, subject, message]) => triage({ source, sender, subject, message }));

  function stats() {
    const by = k => tickets.reduce((a, t) => (a[t[k]] = (a[t[k]] || 0) + 1, a), {});
    return { total: tickets.length, today: tickets.length, by_category: by("category"),
             by_priority: by("priority"), by_sentiment: by("sentiment") };
  }
  const json = (obj, status = 200) => Promise.resolve(new Response(JSON.stringify(obj), {
    status, headers: { "Content-Type": "application/json" } }));

  const realFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    const u = new URL(url, location.href);
    const path = u.pathname.replace(/^.*\/(?=(stats|tickets|triage)$)/, "/");
    if (path === "/stats") return json(stats());
    if (path === "/tickets") {
      const p = u.searchParams.get("priority");
      return json(tickets.filter(t => !p || t.priority === p).slice().reverse());
    }
    if (path === "/triage") {
      const body = JSON.parse((opts && opts.body) || "{}");
      if (!body.message) return json({ detail: "message required" }, 422);
      const t = triage(body);
      return json({ ...t, needs_alert: ["high", "urgent"].includes(t.priority), provider: t.provider });
    }
    return realFetch(url, opts);
  };
  window.__demoClassify = classify; // exposed for tests
})();

// Floating embers drifting up from the bottom of the page, plus a reading progress bar on posts.
(() => {
  const canvas = document.getElementById('embers');
  if (!canvas || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const ctx = canvas.getContext('2d');
  let w, h, embers = [];
  const resize = () => { w = canvas.width = innerWidth; h = canvas.height = innerHeight; };
  const spawn = (anywhere = false) => ({
    x: Math.random() * w, y: anywhere ? Math.random() * h : h + 10,
    r: Math.random() * 1.8 + 0.6, speed: Math.random() * 0.6 + 0.25,
    drift: Math.random() * Math.PI * 2, life: Math.random() * 0.6 + 0.4,
  });
  resize();
  addEventListener('resize', resize);
  const count = Math.min(70, Math.floor(innerWidth / 18));
  embers = Array.from({ length: count }, () => spawn(true));
  const tick = () => {
    ctx.clearRect(0, 0, w, h);
    for (const e of embers) {
      e.y -= e.speed; e.drift += 0.02; e.x += Math.sin(e.drift) * 0.4;
      const fade = Math.min(1, e.y / h) * e.life;
      const glow = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 4);
      glow.addColorStop(0, `rgba(253, 186, 116, ${fade})`);
      glow.addColorStop(1, 'rgba(249, 115, 22, 0)');
      ctx.fillStyle = glow;
      ctx.beginPath(); ctx.arc(e.x, e.y, e.r * 4, 0, Math.PI * 2); ctx.fill();
      if (e.y < -10) Object.assign(e, spawn());
    }
    requestAnimationFrame(tick);
  };
  tick();
})();

(() => {
  const bar = document.getElementById('progress');
  if (!bar) return;
  const update = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = `${max > 0 ? (scrollY / max) * 100 : 0}%`;
  };
  addEventListener('scroll', update, { passive: true });
  update();
})();

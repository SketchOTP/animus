/* Canvas chart helpers for Command Center (D-140). */
(function (global) {
  'use strict';

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function drawSparkline(canvas, values, color) {
    if (!canvas || !values || !values.length) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    var pad = 12;
    var max = Math.max.apply(null, values.concat([1]));
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = color || cssVar('--cc-accent', '#0071e3');
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    values.forEach(function (v, i) {
      var x = pad + (i / Math.max(values.length - 1, 1)) * (w - pad * 2);
      var y = h - pad - (v / max) * (h - pad * 2);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.lineTo(w - pad, h - pad);
    ctx.lineTo(pad, h - pad);
    ctx.closePath();
    ctx.fillStyle = (color || cssVar('--cc-accent', '#0071e3')).replace(')', ', 0.12)').replace('rgb', 'rgba').replace('#0071e3', 'rgba(0,113,227,0.12)');
    if (color && color.indexOf('#') === 0) ctx.fillStyle = 'rgba(0,113,227,0.12)';
    ctx.fill();
  }

  function drawDonut(canvas, segments) {
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    var cx = w / 2;
    var cy = h / 2;
    var outer = Math.min(w, h) * 0.42;
    var inner = outer * 0.62;
    var total = segments.reduce(function (s, seg) { return s + (seg.value || 0); }, 0) || 1;
    var start = -Math.PI / 2;
    ctx.clearRect(0, 0, w, h);
    segments.forEach(function (seg) {
      var slice = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(cx, cy, outer, start, start + slice);
      ctx.arc(cx, cy, inner, start + slice, start, true);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      start += slice;
    });
    ctx.fillStyle = cssVar('--cc-text', '#1d1d1f');
    ctx.font = '600 22px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(total), cx, cy);
  }

  function drawRing(canvas, pct, color, label) {
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    var cx = w / 2;
    var cy = h / 2;
    var r = Math.min(w, h) * 0.38;
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 14;
    ctx.strokeStyle = 'rgba(110,110,115,0.15)';
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = color || cssVar('--cc-accent', '#0071e3');
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.max(0, Math.min(pct, 1)));
    ctx.stroke();
    if (label) {
      ctx.fillStyle = cssVar('--cc-text-muted', '#6e6e73');
      ctx.font = '600 13px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(label, cx, cy + 4);
    }
  }

  global.CCCharts = {
    drawSparkline: drawSparkline,
    drawDonut: drawDonut,
    drawRing: drawRing
  };
})(window);

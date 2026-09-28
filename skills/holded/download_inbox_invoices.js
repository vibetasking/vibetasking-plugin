(function () {
  try {
    function pad2(n) { return String(n).padStart(2, "0"); }

    function sleepSync(ms) {
      const end = Date.now() + (Number(ms) || 0);
      while (Date.now() < end) {}
    }

    function parseSimpleDateToLocalMidnight(input) {
      if (input == null) throw new Error("Missing required parameter: startDate/endDate");
      const s = String(input).trim();
      if (!s) throw new Error("Empty date string: " + input);

      const m = s.match(/^\s*(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\s*$/);
      if (m) {
        let d = parseInt(m[1], 10);
        let mo = parseInt(m[2], 10);
        let y = parseInt(m[3], 10);
        if (y < 100) y = 2000 + y;
        if (!(y >= 1970 && y <= 2100)) throw new Error("Year out of range in date: " + s);
        if (!(mo >= 1 && mo <= 12)) throw new Error("Month out of range in date: " + s);
        const dim = new Date(y, mo, 0).getDate();
        if (!(d >= 1 && d <= dim)) throw new Error("Day out of range in date: " + s);
        return new Date(y, mo - 1, d, 0, 0, 0, 0);
      }

      const t = Date.parse(s);
      if (!Number.isFinite(t)) throw new Error("Unrecognized date format: " + s);
      const dt = new Date(t);
      return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate(), 0, 0, 0, 0);
    }

    function toISOWithOffset(d, endOfDay) {
      const dt = new Date(d.getTime());
      if (endOfDay) dt.setHours(23, 59, 59, 999);
      const offMin = -dt.getTimezoneOffset();
      const sign = offMin >= 0 ? "+" : "-";
      const abs = Math.abs(offMin);
      const hh = pad2(Math.floor(abs / 60));
      const mm = pad2(abs % 60);

      const yyyy = dt.getFullYear();
      const mon = pad2(dt.getMonth() + 1);
      const day = pad2(dt.getDate());
      const h = pad2(dt.getHours());
      const m = pad2(dt.getMinutes());
      const s = pad2(dt.getSeconds());

      return `${yyyy}-${mon}-${day}T${h}:${m}:${s}${sign}${hh}:${mm}`;
    }

    function xhrSync(url, options = {}) {
      const xhr = new XMLHttpRequest();
      xhr.open(options.method || "GET", url, false);
      xhr.withCredentials = options.withCredentials !== false;
      if (options.binary === true && xhr.overrideMimeType) {
        xhr.overrideMimeType("text/plain; charset=x-user-defined");
      }
      if (options.headers) {
        for (const [k, v] of Object.entries(options.headers)) xhr.setRequestHeader(k, v);
      }
      xhr.send(options.body || null);
      return xhr;
    }

    function absUrl(pathOrUrl) {
      if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
      if (pathOrUrl.startsWith("/")) return location.origin + pathOrUrl;
      return location.origin + "/" + pathOrUrl;
    }

    function safeJsonParse(text) {
      try { return JSON.parse(text); } catch { return null; }
    }

    function normalizeInboxResponse(payload) {
      if (Array.isArray(payload)) return { items: payload, hasMore: false, next: null };

      if (payload && typeof payload === "object") {
        const items =
          (Array.isArray(payload.items) && payload.items) ||
          (Array.isArray(payload.data) && payload.data) ||
          (Array.isArray(payload.results) && payload.results) ||
          (Array.isArray(payload.inbox) && payload.inbox) ||
          [];
        const pagination = payload.pagination || payload.paging || payload.page || null;

        let hasMore = false;
        let next = null;
        if (pagination) {
          if (typeof pagination.next === "number") { hasMore = true; next = pagination.next; }
          if (typeof pagination.nextPage === "number") { hasMore = true; next = pagination.nextPage; }
          if (typeof pagination.next_page === "number") { hasMore = true; next = pagination.next_page; }
          if (typeof pagination.hasMore === "boolean") { hasMore = pagination.hasMore; }
          if (typeof pagination.has_more === "boolean") { hasMore = pagination.has_more; }
          if (typeof pagination.cursor === "string" && pagination.cursor) { hasMore = true; next = pagination.cursor; }
          if (typeof pagination.nextCursor === "string" && pagination.nextCursor) { hasMore = true; next = pagination.nextCursor; }
        }

        return { items, hasMore, next, raw: payload };
      }
      return { items: [], hasMore: false, next: null };
    }

    function buildInboxUrl(fromIso, toIso, pageHint) {
      const base = "/internal/inbox";
      const statuses = ["new", "processing", "error", "pending_to_verify", "done"];
      const params = new URLSearchParams();
      params.set("status", statuses.join(","));
      params.set("from", fromIso);
      params.set("to", toIso);

      params.set("limit", "200");
      if (pageHint != null) {
        if (typeof pageHint === "number") params.set("page", String(pageHint));
        else params.set("cursor", String(pageHint));
      }

      return `${base}?${params.toString()}`;
    }

    function fetchInboxAll(fromIso, toIso) {
      const collected = [];
      const seenIds = new Set();

      let page = 1;
      let cursor = null;
      let safety = 0;

      while (safety++ < 200) {
        const hint = cursor || page;
        const url = buildInboxUrl(fromIso, toIso, hint);
        const xhr = xhrSync(url, { method: "GET", headers: { Accept: "application/json, text/plain, */*" } });

        const responseURL = xhr.responseURL || url;
        if (responseURL.includes("/login") || responseURL.includes("auth")) {
          throw new Error("Session expired or redirected to login. Please log in to Holded again.");
        }
        if (xhr.status < 200 || xhr.status >= 300) {
          throw new Error(`Inbox request failed (${xhr.status}). URL: ${url}`);
        }

        const payload = safeJsonParse(xhr.responseText);
        if (!payload) {
          const t = String(xhr.responseText || "");
          if (t.trim().startsWith("<")) throw new Error("Session expired (HTML response received instead of JSON).");
          throw new Error("Failed to parse inbox response as JSON. Response starts with: " + t.slice(0, 200));
        }

        const norm = normalizeInboxResponse(payload);
        const items = norm.items || [];

        let addedThisRound = 0;
        for (const it of items) {
          const id = it && it.id ? String(it.id) : null;
          if (!id) continue;
          if (seenIds.has(id)) continue;
          seenIds.add(id);
          collected.push(it);
          addedThisRound++;
        }

        if (Array.isArray(payload) && !norm.hasMore) break;

        if (norm.hasMore && norm.next && typeof norm.next === "string") {
          cursor = norm.next;
          page = 1;
          if (addedThisRound === 0) break;
          continue;
        }

        if (norm.hasMore && typeof norm.next === "number") {
          page = norm.next;
          cursor = null;
          if (addedThisRound === 0) break;
          continue;
        }

        if (items.length < 200) break;

        page += 1;
        cursor = null;
        if (addedThisRound === 0) break;
      }

      return collected;
    }

    function buildDownloadUrl(item) {
      if (!item || !item.id || !item.file || !item.file.rawFilename) return null;
      const id = String(item.id);
      const raw = String(item.file.rawFilename);
      return absUrl(`/internal/inbox/${encodeURIComponent(id)}/${encodeURIComponent(raw)}/download`);
    }

    function sanitizeFilename(name) {
      let s = String(name || "invoice.pdf");
      s = s.replace(/[\u0000-\u001F\u007F]/g, "");
      s = s.replace(/[\\/]+/g, "_");
      s = s.replace(/[:*?"<>|]+/g, "_");
      s = s.trim();
      if (!s) s = "invoice.pdf";
      if (s.length > 180) {
        const extMatch = s.match(/(\.[A-Za-z0-9]{1,10})$/);
        const ext = extMatch ? extMatch[1] : "";
        s = s.slice(0, 180 - ext.length) + ext;
      }
      return s;
    }

    function triggerDownloadBlob(blob, filename) {
      const a = document.createElement("a");
      const url = URL.createObjectURL(blob);
      a.href = url;
      a.download = filename;
      a.rel = "noopener";
      a.style.display = "none";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        URL.revokeObjectURL(url);
        a.remove();
      }, 5000);
    }

    function binaryStringToUint8Array(binStr) {
      const len = binStr.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = binStr.charCodeAt(i) & 0xff;
      return bytes;
    }

    function mimeFromFilename(fn) {
      const f = String(fn || "").toLowerCase();
      if (f.endsWith(".pdf")) return "application/pdf";
      if (f.endsWith(".png")) return "image/png";
      if (f.endsWith(".jpg") || f.endsWith(".jpeg")) return "image/jpeg";
      if (f.endsWith(".zip")) return "application/zip";
      return "application/octet-stream";
    }

    // Where each format's bytes must open, and how far in (a PDF header may sit anywhere in its first 1024 bytes)
    const SIGNATURES = {
      "application/pdf": { within: 1024, any: [[0x25, 0x50, 0x44, 0x46, 0x2d]] },
      "image/png": { within: 0, any: [[0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]] },
      "image/jpeg": { within: 0, any: [[0xff, 0xd8, 0xff]] },
      "application/zip": { within: 0, any: [[0x50, 0x4b, 0x03, 0x04], [0x50, 0x4b, 0x05, 0x06]] },
    };

    function opensAs(bytes, signature) {
      for (let at = 0; at <= signature.within; at++) {
        for (const sig of signature.any) {
          if (at + sig.length <= bytes.length && sig.every((b, k) => bytes[at + k] === b)) return true;
        }
      }
      return false;
    }

    // A file request the session no longer covers still answers 2xx: a login page after the redirect, or an HTML or
    // JSON error body. Only bytes that open as the file the name promises count as a download.
    function rejectedDownload(xhr, requested, bytes, mime) {
      const finalUrl = xhr.responseURL || requested;
      if (finalUrl !== requested && /\/login|auth/i.test(finalUrl)) return { expired: true, reason: "Session expired (redirected to login)" };

      const type = String((xhr.getResponseHeader && xhr.getResponseHeader("Content-Type")) || "").toLowerCase();
      if (type.includes("text/html") || type.includes("application/json")) {
        return { expired: false, reason: `Received ${type.split(";")[0]} instead of the file` };
      }

      const signature = SIGNATURES[mime];
      if (signature && !opensAs(bytes, signature)) return { expired: false, reason: `The response is not a ${mime} file` };
      if (!signature) {
        let at = 0;
        while (at < bytes.length && at < 64 && (bytes[at] === 0x20 || bytes[at] === 0x09 || bytes[at] === 0x0a || bytes[at] === 0x0d)) at++;
        if (bytes[at] === 0x3c || bytes[at] === 0x7b) return { expired: false, reason: "Received an HTML or JSON body instead of the file" };
      }
      return null;
    }

    if (typeof startDate === "undefined" || !startDate) {
      return { success: false, message: "Missing parameter: startDate" };
    }
    if (typeof endDate === "undefined" || !endDate) {
      return { success: false, message: "Missing parameter: endDate" };
    }

    const start = parseSimpleDateToLocalMidnight(startDate);
    const end = parseSimpleDateToLocalMidnight(endDate);
    if (end.getTime() < start.getTime()) throw new Error("endDate is before startDate");

    const fromIso = toISOWithOffset(start, false);
    const toIso = toISOWithOffset(end, true);

    const items = fetchInboxAll(fromIso, toIso);

    if (!Array.isArray(items) || items.length === 0) {
      console.table([]);
      return { success: true, message: "No invoices found in the selected date range.", downloadedCount: 0, attemptedCount: 0, from: fromIso, to: toIso, downloads: [] };
    }

    const downloads = [];
    const failures = [];
    let sessionExpired = false;
    let attempted = 0;

    for (let i = 0; i < items.length && !sessionExpired; i++) {
      attempted++;
      const it = items[i];
      const status = it && it.status ? String(it.status) : "";
      const filename = sanitizeFilename(
        it && it.file && it.file.filename
          ? it.file.filename
          : (it && it.file && it.file.rawFilename ? it.file.rawFilename : `invoice_${it && it.id ? it.id : i}`)
      );
      const url = buildDownloadUrl(it);

      if (!url) {
        failures.push({ id: it && it.id ? String(it.id) : "", status, filename, reason: "Missing download URL components (id/rawFilename)" });
        continue;
      }

      let ok = false;
      let reason = "";
      try {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", url, false);
        xhr.withCredentials = true;
        if (xhr.overrideMimeType) xhr.overrideMimeType("text/plain; charset=x-user-defined");
        xhr.send(null);

        if (xhr.status >= 200 && xhr.status < 300) {
          const bin = xhr.responseText || "";
          if (!bin) throw new Error("Empty response");
          const bytes = binaryStringToUint8Array(bin);
          if (!bytes || bytes.byteLength === 0) throw new Error("Empty bytes");
          const mime = mimeFromFilename(filename);
          const rejected = rejectedDownload(xhr, url, bytes, mime);
          if (rejected) {
            sessionExpired = rejected.expired;
            throw new Error(rejected.reason);
          }
          triggerDownloadBlob(new Blob([bytes], { type: mime }), filename);
          ok = true;
        } else {
          reason = `HTTP ${xhr.status}`;
        }
      } catch (e) {
        reason = (e && e.message) ? e.message : String(e);
      }

      const dateIso = (function () {
        const raw = (it && (it.date || it.scannedAt)) ? String(it.date || it.scannedAt) : "";
        const t = Date.parse(raw);
        return Number.isFinite(t) ? new Date(t).toISOString() : "";
      })();

      const row = {
        id: it && it.id ? String(it.id) : "",
        status,
        date: dateIso,
        filename,
        downloadUrl: url,
        downloaded: ok
      };

      if (ok) downloads.push(row);
      else failures.push({ ...row, reason: reason || "Unknown failure" });

      sleepSync(250);
    }

    console.table(downloads.map(d => ({ filename: d.filename, status: d.status, date: d.date, id: d.id })));

    const runAt = new Date();
    const stamp = (function (dt) {
      const y = dt.getFullYear();
      const m = pad2(dt.getMonth() + 1);
      const d = pad2(dt.getDate());
      const hh = pad2(dt.getHours());
      const mm = pad2(dt.getMinutes());
      const ss = pad2(dt.getSeconds());
      return `${y}-${m}-${d}_${hh}${mm}${ss}`;
    })(runAt);

    const summaryName = `download_summary_${stamp}.txt`;

    const lines = [];
    lines.push(`Holded invoice download summary`);
    lines.push(`Run at: ${runAt.toISOString()}`);
    lines.push(`Range: ${fromIso} -> ${toIso}`);
    lines.push(`Downloaded: ${downloads.length}`);
    lines.push(`Failed: ${failures.length}`);
    if (sessionExpired) lines.push(`Stopped: the session expired after ${attempted} of ${items.length} document(s)`);
    lines.push("");
    lines.push("Downloaded files:");
    if (downloads.length === 0) lines.push("(none)");
    else for (const d of downloads) lines.push(`- ${d.filename} | status=${d.status} | date=${d.date} | id=${d.id}`);
    lines.push("");
    lines.push("Failures:");
    if (failures.length === 0) lines.push("(none)");
    else for (const f of failures) lines.push(`- ${f.filename || ""} | status=${f.status || ""} | date=${f.date || ""} | id=${f.id || ""} | reason=${f.reason || ""}`);

    triggerDownloadBlob(new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" }), summaryName);

    return {
      success: !sessionExpired,
      message: sessionExpired
        ? `The Holded session expired after ${attempted} of ${items.length} document(s): downloaded ${downloads.length}. Log in again and rerun for the rest. Summary: ${summaryName}`
        : `Downloaded ${downloads.length} file(s). Failed ${failures.length}. Summary: ${summaryName}`,
      from: fromIso,
      to: toIso,
      listedCount: items.length,
      attemptedCount: attempted,
      downloadedCount: downloads.length,
      failedCount: failures.length,
      sessionExpired,
      downloads,
      failures
    };
  } catch (e) {
    return { success: false, message: (e && e.message) ? e.message : String(e) };
  }
})();
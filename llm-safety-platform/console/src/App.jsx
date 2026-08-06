import React, { useEffect, useState } from "react";

const api = async (path, token, opts = {}) => {
  const r = await fetch(path, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "X-Roles": "Admin,Security,AppOwner,Auditor",
      ...(opts.headers || {}),
    },
  });
  const data = await r.json();
  if (!r.ok) throw data;
  return data;
};

export default function App() {
  const [token, setToken] = useState("admin-dev-token");
  const [dash, setDash] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/v1/admin/dashboard", token)
      .then(setDash)
      .catch((e) => setErr(JSON.stringify(e)));
  }, [token]);

  return (
    <div style={{ fontFamily: "IBM Plex Sans, sans-serif", padding: 24, background: "#0f1419", color: "#e7ecf3", minHeight: "100vh" }}>
      <h1>LLM Safety Platform Console</h1>
      <p>React/Vite 治理台（生产也可直接使用 /console 静态页）</p>
      <label>
        Admin Token{" "}
        <input value={token} onChange={(e) => setToken(e.target.value)} style={{ width: 260 }} />
      </label>
      {err && <pre style={{ color: "#f07178" }}>{err}</pre>}
      {dash && (
        <ul>
          <li>审计 {dash.audit_count}</li>
          <li>VK {dash.vk_count}</li>
          <li>待审批 {dash.pending_approvals}</li>
          <li>红队 {dash.redteam_runs}</li>
        </ul>
      )}
      <p>
        完整运维页见 <a href="/console/" style={{ color: "#3d8bfd" }}>/console/</a>（静态 SPA）
      </p>
    </div>
  );
}

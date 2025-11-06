// src/components/Dashboard.js
import React, { useState, useEffect } from "react";
import { FaMoneyBill, FaSignOutAlt, FaDownload } from "react-icons/fa";
import "../App.css"; // ensure this is your single css file

export default function Dashboard({ user, onLogout }) {
  const [balance, setBalance] = useState(0);
  const [amount, setAmount] = useState("");
  const [recipient, setRecipient] = useState("");
  const [message, setMessage] = useState("");
  const [transactions, setTransactions] = useState([]);
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const API = "http://127.0.0.1:5000";

  useEffect(() => {
    fetchBalance();
    // eslint-disable-next-line
  }, []);

  // Robust fetch wrapper
  async function apiPost(path, body) {
    try {
      const res = await fetch(`${API}/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      const data = await res.json().catch(() => ({}));
      return { ok: res.ok, data, status: res.status };
    } catch (err) {
      return { ok: false, error: "network" };
    }
  }

  async function fetchBalance() {
    setMessage("");
    try {
      const res = await fetch(`${API}/balance`);
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.message || "Failed to fetch balance");
        setBalance(0);
        setTransactions([]);
        return;
      }
      setBalance(Number(data.balance || 0));
      // normalize transactions robustly
      const raw = Array.isArray(data.transactions) ? data.transactions : [];
      const normalized = raw.map((t) => ({
        type: (t.type || t.action || "info").toString(),
        amount: Number(t.amount ?? t.value ?? 0),
        timestamp: t.timestamp || t.time || t.date || "",
        to_user: t.to_user || t.to || t.recipient || null,
      }));
      setTransactions(normalized);
    } catch (e) {
      setMessage("Server unreachable");
    }
  }

  const showTempMessage = (msg, kind = "success", autoClear = true) => {
    setMessage(msg);
    // optionally include class via string; CSS distinguishes "wrong" -> error if you prefer
    if (autoClear) setTimeout(() => setMessage(""), 4500);
  };

  const handleDeposit = async () => {
    const amt = Number(amount);
    if (!amt || amt <= 0) return showTempMessage("Enter a valid positive amount", "error");
    const r = await apiPost("deposit", { amount: amt });
    if (r.ok) {
      showTempMessage(r.data.message || "Deposited successfully");
      setAmount("");
      fetchBalance();
    } else {
      showTempMessage(r.data?.message || (r.error === "network" ? "Failed to connect" : "Action failed"), "error");
    }
  };

  const handleWithdraw = async () => {
    const amt = Number(amount);
    if (!amt || amt <= 0) return showTempMessage("Enter a valid positive amount", "error");
    const pin = prompt("Enter your PIN:");
    if (!pin) return showTempMessage("PIN is required", "error");
    const r = await apiPost("withdraw", { amount: amt, pin });
    if (r.ok) {
      showTempMessage(r.data.message || "Withdrawn successfully");
      setAmount("");
      fetchBalance();
    } else {
      showTempMessage(r.data?.message || "Action failed", "error");
    }
  };

  const handleTransfer = async () => {
    const amt = Number(amount);
    if (!recipient) return showTempMessage("Enter recipient username", "error");
    if (!amt || amt <= 0) return showTempMessage("Enter a valid positive amount", "error");
    const pin = prompt("Enter your PIN:");
    if (!pin) return showTempMessage("PIN is required", "error");
    const r = await apiPost("transfer", { to_user: recipient, amount: amt, pin });
    if (r.ok) {
      showTempMessage(r.data.message || "Transfer successful");
      setAmount("");
      setRecipient("");
      fetchBalance();
    } else {
      showTempMessage(r.data?.message || "Action failed", "error");
    }
  };

  const downloadCsv = async () => {
    if (!transactions || transactions.length === 0) return showTempMessage("No transaction history available yet.", "error");
    try {
      const res = await fetch(`${API}/download_csv`);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `${user}_transactions.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      showTempMessage("CSV downloaded successfully!");
    } catch {
      showTempMessage("Error downloading CSV.", "error");
    }
  };

  const submitRating = (val) => {
    // optimistic UI: close and logout after backend call finishes
    fetch(`${API}/rate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating: val }),
    }).finally(() => {
      setShowRating(false);
      setTimeout(() => onLogout(), 700);
    });
  };

  return (
    <div className="dashboard-container" role="main">
      {/* SIDEBAR */}
      <aside className="sidebar" aria-label="sidebar">
        <div className="logo" style={{ textAlign: "center" }}>
          <FaMoneyBill size={28} />
          <h2 style={{ margin: "8px 0" }}>Smart ATM+</h2>
          <small style={{ opacity: 0.8 }}>{user}</small>
        </div>

        <div style={{ width: "100%", marginTop: 12 }}>
          <nav className="nav-links" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <button className="nav-btn" onClick={() => { /* future: navigate */ }}>Dashboard</button>
            <button className="nav-btn" onClick={() => { /* future: navigate */ }}>Transactions</button>
            <button className="nav-btn" onClick={() => downloadCsv()}><FaDownload /> Export</button>
          </nav>
        </div>

        <div style={{ width: "100%", textAlign: "center" }}>
          <button className="logout-btn" onClick={() => setShowRating(true)}><FaSignOutAlt /> Logout</button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main-content" aria-live="polite">
        <header className="dashboard-header">
          <div>
            <h2 style={{ margin: 0 }}>Welcome, <span className="user">{user}</span> 👋</h2>
            <p style={{ margin: 0, opacity: 0.8 }}>Your trusted banking dashboard</p>
          </div>
          <div className="avatar" aria-hidden>{user ? user.charAt(0).toUpperCase() : "U"}</div>
        </header>

        <section className="balance-card glass-card" aria-label="balance">
          <h1 style={{ margin: 0 }}>₹{Number(balance || 0).toFixed(2)}</h1>
          <p className="balance-sub">Available Balance</p>
        </section>

        <section className="actions-grid" aria-label="actions">
          <div className="action-card">
            <input
              aria-label="amount"
              type="number"
              placeholder="Enter amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <div className="button-row">
              <button onClick={handleDeposit}>Deposit</button>
              <button onClick={handleWithdraw}>Withdraw</button>
            </div>
          </div>

          <div className="action-card">
            <input
              aria-label="recipient"
              type="text"
              placeholder="Recipient username"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
            />
            <button className="transfer-btn" onClick={handleTransfer}>Transfer</button>
          </div>
        </section>

        {/* status message */}
        {message ? (
          <div className={`status-message ${/wrong|fail|error|required|insufficient/i.test(message) ? "error" : "success"}`}>
            {message}
          </div>
        ) : null}

        <section className="transactions-card glass-card" aria-label="transactions">
          <h3 style={{ marginTop: 0 }}>Recent Transactions</h3>
          <ul className="transactions-list" style={{ paddingLeft: 0, margin: 0, listStyle: "none" }}>
            {transactions.length === 0 ? (
              <li>No transactions yet</li>
            ) : (
              transactions.map((t, i) => (
                <li key={i} className="transaction-item">
                  <span style={{ textTransform: "capitalize" }}>{t.type}</span>
                  <span>₹{Number(t.amount || 0).toFixed(2)}</span>
                  <span style={{ color: "#cbd5e1" }}>{t.timestamp || ""}</span>
                </li>
              ))
            )}
          </ul>
        </section>

        <div style={{ display: "flex", justifyContent: "center", gap: 12 }}>
          <button className="download-btn" onClick={downloadCsv} disabled={transactions.length === 0}>⬇️ Download History</button>
        </div>
      </main>

      {/* RATING MODAL */}
      {showRating && (
        <div className="rating-overlay" style={{ zIndex: 9999 }}>
          <div className="rating-box">
            <h3>How would you rate this project?</h3>
            <div style={{ margin: "12px 0" }}>
              {["😡", "😕", "😐", "😊", "🤩"].map((emoji, i) => (
                <span key={i} onClick={() => submitRating(i + 1)}>{emoji}</span>
              ))}
            </div>
            <p style={{ marginTop: 8 }}>Tap an emoji to rate.</p>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from "react";

function LoginSignup({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pin, setPin] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [message, setMessage] = useState("");

  // ✅ Use localhost instead of 127.0.0.1 (solves many CORS & connection issues)
  const API = "http://localhost:5000";

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setOtpSent(false);
    setMessage("");
  };

  // ✅ Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      console.log("🔐 Sending login request...");
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      console.log("Response:", data);
      setMessage(data.message || data.error || "No response");
      if (res.ok) onLogin(username);
    } catch (err) {
      console.error("Login error:", err);
      setMessage("❌ Error connecting to server");
    }
  };

  // ✅ Step 1 — Send OTP to Email
  const handleSendOtp = async () => {
    if (!email) return setMessage("Enter a valid email first!");
    try {
      console.log("📧 Sending OTP request...");
      const res = await fetch(`${API}/send_otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      console.log("Response:", data);
      if (res.ok) {
        setOtpSent(true);
        setMessage("✅ OTP sent to your email!");
      } else {
        setMessage(data.error || "Failed to send OTP");
      }
    } catch (err) {
      console.error("Send OTP error:", err);
      setMessage("❌ Error sending OTP");
    }
  };

  // ✅ Step 2 — Verify OTP & Create Account
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    try {
      console.log("🪪 Sending verify_otp request...");
      const res = await fetch(`${API}/verify_otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // 🔧 Include PIN if backend expects it later (futureproof)
        body: JSON.stringify({ username, email, password, otp, pin }),
      });
      const data = await res.json();
      console.log("Response:", data);
      setMessage(data.message || data.error || "No response");
      if (res.ok) {
        setTimeout(() => {
          setIsLogin(true);
          setOtpSent(false);
          setMessage("✅ Signup successful! You can now log in.");
        }, 1500);
      }
    } catch (err) {
      console.error("Verify OTP error:", err);
      setMessage("❌ Error verifying OTP");
    }
  };

  return (
    <div className="auth-container">
      <h2>{isLogin ? "Login" : "Create Account"}</h2>

      <form onSubmit={isLogin ? handleLogin : handleVerifyOtp}>
        {/* Username */}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        {/* Email (signup only) */}
        {!isLogin && (
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        )}

        {/* Password */}
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {/* PIN input (signup step before OTP) */}
        {!isLogin && !otpSent && (
          <input
            type="password"
            placeholder="4-digit PIN"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            required
          />
        )}

        {/* OTP input (after email OTP is sent) */}
        {!isLogin && otpSent && (
          <input
            type="text"
            placeholder="Enter OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />
        )}

        {/* Buttons */}
        {isLogin ? (
          <button type="submit">Login</button>
        ) : !otpSent ? (
          <button type="button" onClick={handleSendOtp}>
            Send OTP
          </button>
        ) : (
          <button type="submit">Verify & Signup</button>
        )}
      </form>

      {/* Status message */}
      {message && <p>{message}</p>}

      <button onClick={toggleMode} className="toggle-btn">
        {isLogin ? "Need an account? Sign up" : "Already have an account? Login"}
      </button>
    </div>
  );
}

export default LoginSignup;

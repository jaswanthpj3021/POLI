const { useState, useEffect } = React;

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function Auth({ onDone }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const path = mode === "login" ? "/api/login" : "/api/signup";
      await api(path, "POST", form);
      onDone();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <h2>{mode === "login" ? "Welcome back" : "Create your planner account"}</h2>
        <p className="mini">Track expenses, budgets, chats and project-ready reports.</p>
        <form onSubmit={submit}>
          {mode === "signup" && (
            <input placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          )}
          <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <input type="password" placeholder="Password (min 6 chars)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <button type="submit">{mode === "login" ? "Login" : "Sign Up"}</button>
          <button type="button" className="ghost" onClick={() => setMode(mode === "login" ? "signup" : "login")}>Switch to {mode === "login" ? "Sign Up" : "Login"}</button>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
        </form>
      </div>
    </div>
  );
}

function Dashboard({ onLogout }) {
  const [tab, setTab] = useState("dashboard");
  const [summary, setSummary] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [notes, setNotes] = useState([]);
  const [messages, setMessages] = useState([]);
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [forms, setForms] = useState({
    budget: { category: "Food", amount: "", period: "Monthly" },
    expense: { title: "", category: "General", amount: "", spent_on: "", image_url: "", note: "" },
    note: { title: "", content: "" },
    chat: "",
  });

  const loadAll = async () => {
    const [s, b, e, n, m] = await Promise.all([
      api("/api/summary"), api("/api/budgets"), api("/api/expenses"), api("/api/notes"), api("/api/messages")
    ]);
    setSummary(s); setBudgets(b); setExpenses(e); setNotes(n); setMessages(m);
  };

  useEffect(() => { loadAll(); }, []);
  useEffect(() => {
    document.body.className = theme === "dark" ? "dark" : "";
    localStorage.setItem("theme", theme);
  }, [theme]);

  const submit = async (kind, path) => {
    await api(path, "POST", forms[kind]);
    if (kind === "budget") setForms({ ...forms, budget: { category: "Food", amount: "", period: "Monthly" } });
    if (kind === "expense") setForms({ ...forms, expense: { title: "", category: "General", amount: "", spent_on: "", image_url: "", note: "" } });
    if (kind === "note") setForms({ ...forms, note: { title: "", content: "" } });
    if (kind === "chat") setForms({ ...forms, chat: "" });
    loadAll();
  };

  return (
    <div className="page">
      <div className="topbar">
        <h2>Campus Cashflow Planner</h2>
        <div>
          <button className="ghost" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>Theme: {theme}</button>
          <button onClick={async () => { await api("/api/logout", "POST"); onLogout(); }}>Logout</button>
        </div>
      </div>

      <div className="navtabs">
        {["dashboard", "transactions", "profile", "notes", "chat"].map((t) => (
          <button key={t} className={tab === t ? "" : "ghost"} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>

      {tab === "dashboard" && summary && (
        <div className="grid">
          <div className="card"><h3>Budget Total</h3><h1>₹{summary.budget_total}</h1></div>
          <div className="card"><h3>Expense Total</h3><h1>₹{summary.expense_total}</h1></div>
          <div className="card"><h3>Remaining</h3><h1>₹{summary.remaining}</h1><p className="mini">Transactions: {summary.transaction_count}</p></div>

          <div className="card">
            <h3>Add Budget Plan</h3>
            <input placeholder="Category" value={forms.budget.category} onChange={(e) => setForms({ ...forms, budget: { ...forms.budget, category: e.target.value } })}/>
            <input type="number" placeholder="Amount" value={forms.budget.amount} onChange={(e) => setForms({ ...forms, budget: { ...forms.budget, amount: e.target.value } })}/>
            <select value={forms.budget.period} onChange={(e) => setForms({ ...forms, budget: { ...forms.budget, period: e.target.value } })}><option>Monthly</option><option>Semester</option><option>Yearly</option></select>
            <button onClick={() => submit("budget", "/api/budgets")}>Save Budget</button>
          </div>

          <div className="card">
            <h3>Add Expense</h3>
            <input placeholder="Title" value={forms.expense.title} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, title: e.target.value } })}/>
            <input placeholder="Category" value={forms.expense.category} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, category: e.target.value } })}/>
            <input type="number" placeholder="Amount" value={forms.expense.amount} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, amount: e.target.value } })}/>
            <input type="date" value={forms.expense.spent_on} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, spent_on: e.target.value } })}/>
            <input placeholder="Image URL" value={forms.expense.image_url} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, image_url: e.target.value } })}/>
            <textarea placeholder="Notes" value={forms.expense.note} onChange={(e) => setForms({ ...forms, expense: { ...forms.expense, note: e.target.value } })}/>
            <button onClick={() => submit("expense", "/api/expenses")}>Save Expense</button>
          </div>

          <div className="card">
            <h3>Budget Plans</h3>
            <div className="list">{budgets.map((b) => <div className="item" key={b.id}><b>{b.category}</b> <span className="badge">{b.period}</span><div>₹{b.amount}</div></div>)}</div>
          </div>
        </div>
      )}

      {tab === "transactions" && (
        <div className="card">
          <h3>Transactions & Expense Gallery</h3>
          <div className="list">{expenses.map((x) => (
            <div className="item" key={x.id}>
              <b>{x.title}</b> - ₹{x.amount} <span className="badge">{x.category}</span>
              <div className="mini">{x.spent_on}</div>
              {x.note && <div>{x.note}</div>}
              {x.image_url && <img src={x.image_url} alt={x.title} style={{ width: "100%", maxWidth: 220, borderRadius: 10, marginTop: 8 }} />}
            </div>
          ))}</div>
        </div>
      )}

      {tab === "profile" && summary && (
        <div className="card">
          <h3>Profile & Project Stats</h3>
          <p><b>Name:</b> {summary.username}</p>
          <p><b>Total Planned:</b> ₹{summary.budget_total}</p>
          <p><b>Total Spent:</b> ₹{summary.expense_total}</p>
          <p><b>Remaining:</b> ₹{summary.remaining}</p>
          <p className="mini">Perfect for college mini/major project demos with login, planning and reports.</p>
        </div>
      )}

      {tab === "notes" && (
        <div className="grid">
          <div className="card">
            <h3>Create Note</h3>
            <input placeholder="Title" value={forms.note.title} onChange={(e) => setForms({ ...forms, note: { ...forms.note, title: e.target.value } })}/>
            <textarea placeholder="Write your notes..." value={forms.note.content} onChange={(e) => setForms({ ...forms, note: { ...forms.note, content: e.target.value } })}/>
            <button onClick={() => submit("note", "/api/notes")}>Save Note</button>
          </div>
          <div className="card">
            <h3>All Notes</h3>
            <div className="list">{notes.map((n) => <div className="item" key={n.id}><b>{n.title}</b><div>{n.content}</div></div>)}</div>
          </div>
        </div>
      )}

      {tab === "chat" && (
        <div className="card">
          <h3>Student Chat Corner</h3>
          <div className="chatbox">{messages.map((m) => <div className="chat-msg" key={m.id}><b>{m.username}:</b> {m.text}</div>)}</div>
          <input placeholder="Send a message..." value={forms.chat} onChange={(e) => setForms({ ...forms, chat: e.target.value })}/>
          <button onClick={() => submit("chat", "/api/messages")}>Send</button>
        </div>
      )}
    </div>
  );
}

function App() {
  const [authed, setAuthed] = useState(false);
  useEffect(() => { api("/api/me").then(() => setAuthed(true)).catch(() => setAuthed(false)); }, []);
  return authed ? <Dashboard onLogout={() => setAuthed(false)} /> : <Auth onDone={() => setAuthed(true)} />;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

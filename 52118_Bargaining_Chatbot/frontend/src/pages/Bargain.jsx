import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { useUser } from "../context/UserContext";
import { api } from "../lib/api";
import Modal from "../components/Modal";

function friendlyError(error) {
  return error?.message === "Invalid or expired token"
    ? "Your session has expired. Please login again."
    : "Something went wrong. Please try again.";
}

export default function Bargain() {
  const { productId, variantId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useUser();

  const [product, setProduct] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [status, setStatus] = useState("ongoing"); // ongoing | accepted | rejected | error
  const [lock, setLock] = useState(null);
  const [error, setError] = useState(null);
  const [limitInfo, setLimitInfo] = useState(null); // { limit, usedToday } when daily limit is hit
  const messagesRef = useRef(null);
  const sessionStorageKey = `bazaaro_negotiation_session_${user?.id}_${variantId}`;

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    let cancelled = false;
    api.getProduct(productId)
      .then((data) => {
        if (!cancelled) setProduct(data);
      })
      .catch((e) => {
        if (!cancelled) setError(friendlyError(e));
      });

    const savedSessionId = localStorage.getItem(sessionStorageKey);
    if (savedSessionId) {
      api.getNegotiationSession(savedSessionId)
        .then((data) => {
          if (cancelled) return;
          setSessionId(savedSessionId);
          setMessages(data.messages || []);
          setStatus(data.status || "ongoing");
          setLock(data.lock || null);
        })
        .catch((e) => {
          if (!cancelled) {
            localStorage.removeItem(sessionStorageKey);
            setError(friendlyError(e));
          }
        });
    } else {
      api.startNegotiation({ productId, variantId })
        .then((data) => {
          if (cancelled) return;
          localStorage.setItem(sessionStorageKey, data.sessionId);
          setSessionId(data.sessionId);
          setMessages([{ from: "bot", text: data.botMessage }]);
        })
        .catch((e) => {
          if (cancelled) return;
          if (e.data?.limitReached) {
            setLimitInfo({ limit: e.data.limit, usedToday: e.data.usedToday });
          } else {
            setError(friendlyError(e));
          }
        });
    }
    return () => { cancelled = true; };
  }, [productId, variantId, isAuthenticated, navigate, sessionStorageKey]);

  useEffect(() => {
    const container = messagesRef.current;
    if (container) container.scrollTop = container.scrollHeight;
  }, [messages, typing]);

  async function send(text) {
    if (!text.trim() || !sessionId || status !== "ongoing") return;
    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setTyping(true);
    try {
      const res = await api.sendMessage({ sessionId, message: text });
      await new Promise((r) => setTimeout(r, 500)); // feels more natural than an instant reply
      setTyping(false);
      setMessages((m) => [...m, { from: "bot", text: res.botMessage }]);
      if (res.status && res.status !== "ongoing") setStatus(res.status);
      if (res.lock) setLock(res.lock);
    } catch (e) {
      setTyping(false);
      setError(friendlyError(e));
    }
  }

  if (limitInfo) {
    return (
      <Modal
        open={true}
        onClose={() => navigate("/")}
        icon={AlertTriangle}
        iconColor="text-marigold-dark"
        title="Daily bargaining limit reached"
        actions={
          <>
            <button
              onClick={() => navigate(`/product/${productId}`)}
              className="flex-1 bg-ink text-ivory py-3 rounded-full text-sm font-medium"
            >
              Buy at listed price
            </button>
            <button
              onClick={() => navigate("/")}
              className="flex-1 border border-ink/15 text-ink-soft py-3 rounded-full text-sm font-medium"
            >
              Keep browsing
            </button>
          </>
        }
      >
        You've used your bargaining chance on all <strong>{limitInfo.limit}</strong> products
        allowed today. This limit resets tomorrow — or you can buy this item at its listed
        price right now.
        <br /><br />
        Negotiating on more products more often, without abusing the system, raises your
        trust tier over time — which increases this daily limit.
      </Modal>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        <XCircle className="w-10 h-10 text-rani mx-auto mb-4" />
        <p className="text-ink-soft">{error}</p>
        <button onClick={() => navigate(-1)} className="mt-6 text-sm underline text-ink">Go back</button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-ink flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-marigold" />
        </div>
        <div>
          <p className="font-display text-lg text-ink">Bargaining for {product?.name || "..."}</p>
          <p className="text-xs text-ink-soft">Listed at ₹{product?.listedPrice?.toLocaleString("en-IN")}</p>
        </div>
      </div>

      <div ref={messagesRef} className="bg-ivory-dim rounded-3xl p-6 h-[440px] overflow-y-auto flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
              className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                m.from === "user"
                  ? "self-end bg-ink text-ivory rounded-br-sm"
                  : "self-start bg-white text-ink rounded-bl-sm shadow-sm"
              }`}
            >
              {m.text}
            </motion.div>
          ))}
        </AnimatePresence>

        {typing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="self-start bg-white rounded-2xl rounded-bl-sm shadow-sm px-4 py-3 flex gap-1"
          >
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-ink-soft/50"
                animate={{ y: [0, -4, 0] }}
                transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.15 }}
              />
            ))}
          </motion.div>
        )}

        {status === "accepted" && lock && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="self-center bg-sage/10 border border-sage/30 rounded-2xl px-5 py-4 text-center mt-2"
          >
            <CheckCircle2 className="w-6 h-6 text-sage mx-auto mb-2" />
            <p className="text-sm text-ink font-medium">Locked at ₹{lock.price.toLocaleString("en-IN")}</p>
            <p className="text-xs text-ink-soft mb-3">
              Valid till {new Intl.DateTimeFormat("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "numeric",
                minute: "2-digit",
                hour12: true,
                timeZone: "Asia/Kolkata",
              }).format(new Date(lock.expiresAt))}
            </p>
            <button
              onClick={() => navigate("/deals")}
              className="text-sm bg-ink text-ivory px-5 py-2 rounded-full"
            >
              Go to My Deals
            </button>
          </motion.div>
        )}

        {status === "rejected" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="self-center text-center text-sm text-ink-soft mt-2">
            Negotiation ended. You can browse other pieces anytime.
          </motion.div>
        )}

      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="mt-4 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={status !== "ongoing"}
          placeholder={status === "ongoing" ? "Type your offer, e.g. 1500..." : "Negotiation ended"}
          className="flex-1 bg-white border border-ink/10 rounded-full px-5 py-3 text-sm outline-none focus:border-rani transition-colors disabled:opacity-50"
        />
        <motion.button
          whileTap={{ scale: 0.9 }}
          type="submit"
          disabled={status !== "ongoing"}
          className="w-12 h-12 rounded-full bg-rani text-white flex items-center justify-center disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </motion.button>
      </form>
    </div>
  );
}

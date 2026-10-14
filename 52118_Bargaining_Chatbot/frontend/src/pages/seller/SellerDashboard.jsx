import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, TrendingUp, Package, Tag, Save } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../lib/api";
import { useUser } from "../../context/UserContext";
import { useNavigate } from "react-router-dom";

export default function SellerDashboard() {
  const { user, isAuthenticated } = useUser();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [productStats, setProductStats] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null); // product being price-edited
  const [error, setError] = useState(null);

  function refresh() {
    api.sellerProducts().then(setProducts).catch((e) => setError(e.message));
    Promise.all([api.sellerAnalytics(), api.sellerProductStats()])
      .then(([nextAnalytics, nextProductStats]) => {
        setAnalytics(nextAnalytics);
        setProductStats(nextProductStats.map((product) => ({
          ...product,
          ceiling: Number(product.ceiling),
          floor: Number(product.floor),
          stock: Number(product.stock),
          reserved: Number(product.reserved),
          negotiations: Number(product.negotiations),
          accepted: Number(product.accepted),
          orders: Number(product.orders),
        })));
      })
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "seller") { navigate("/login"); return; }
    refresh();
  }, [isAuthenticated]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl text-ink">Seller Dashboard</h1>
          <p className="text-ink-soft text-sm">Welcome back, {user?.name}</p>
        </div>
        <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={() => setShowForm(true)} className="bg-ink text-ivory px-5 py-3 rounded-full text-sm font-medium flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Product
        </motion.button>
      </div>

      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <Stat icon={Tag} label="Negotiations" value={analytics.total_negotiations} />
          <Stat icon={TrendingUp} label="Accepted" value={analytics.accepted} />
          <Stat icon={Package} label="Orders" value={analytics.total_orders} />
          <Stat icon={TrendingUp} label="Revenue" value={`₹${Number(analytics.revenue).toLocaleString("en-IN")}`} />
        </div>
      )}

      <section className="mb-10">
        <h2 className="font-display text-2xl text-ink mb-4">Product performance</h2>
        {productStats === null ? (
          <p className="text-sm text-ink-soft">Loading product performance...</p>
        ) : productStats.length === 0 ? (
          <p className="text-sm text-ink-soft">Add your first product to see its performance here.</p>
        ) : (
          <div className="grid gap-5">
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <h3 className="font-medium text-ink mb-4">Negotiations and accepted offers</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={productStats} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e1d5" />
                  <XAxis dataKey="name" tick={{ fill: "#1c1c1e", fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fill: "#1c1c1e", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="negotiations" name="Negotiations" fill="#1c1c1e" />
                  <Bar dataKey="accepted" name="Accepted" fill="#e8a33d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <h3 className="font-medium text-ink mb-4">Floor vs Ceiling price</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={productStats} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e1d5" />
                  <XAxis dataKey="name" tick={{ fill: "#1c1c1e", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#1c1c1e", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="floor" name="Floor" fill="#1c1c1e" />
                  <Bar dataKey="ceiling" name="Ceiling" fill="#e8a33d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </section>

      {error && <p className="text-rani text-sm mb-4">{error}</p>}

      <div className="flex flex-col gap-3">
        {products.map((p) => (
          <ProductRow key={p.id} product={p} onEdit={() => setEditing(p)} />
        ))}
      </div>

      {showForm && <AddProductModal onClose={() => setShowForm(false)} onSaved={() => { setShowForm(false); refresh(); }} />}
      {editing && <PricingModal product={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); refresh(); }} />}
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm">
      <Icon className="w-5 h-5 text-rani mb-3" strokeWidth={1.5} />
      <p className="font-display text-2xl text-ink">{value}</p>
      <p className="text-xs text-ink-soft">{label}</p>
    </div>
  );
}

function ProductRow({ product, onEdit }) {
  const totalStock = product.variants.reduce((s, v) => s + v.stock_quantity, 0);
  const totalReserved = product.variants.reduce((s, v) => s + v.reserved_quantity, 0);
  return (
    <div className="bg-white rounded-2xl p-4 flex items-center gap-4 shadow-sm">
      <div className="flex-1">
        <p className="font-display text-lg text-ink">{product.name}</p>
        <p className="text-xs text-ink-soft">{product.category} · {product.gender_category}</p>
      </div>
      <div className="text-sm text-ink-soft">
        Floor ₹{Number(product.floor_price).toLocaleString("en-IN")} · Ceiling ₹{Number(product.ceiling_price).toLocaleString("en-IN")}
      </div>
      <div className="text-sm text-ink-soft">
        Stock {totalStock} ({totalReserved} reserved)
      </div>
      <span className={`text-xs px-3 py-1 rounded-full font-medium ${product.bargaining_enabled ? "bg-rani/10 text-rani" : "bg-ink/5 text-ink-soft"}`}>
        {product.bargaining_enabled ? "Bargaining On" : "Bargaining Off"}
      </span>
      <button onClick={onEdit} className="text-sm underline text-ink">Edit pricing</button>
    </div>
  );
}

function AddProductModal({ onClose, onSaved }) {
  const [form, setForm] = useState({
    name: "", description: "", gender_category: "men", category: "", fabric_type: "",
    listed_price: "", floor_price: "", ceiling_price: "", bargaining_enabled: true,
    variants: [{ size: "", color: "", stock: "" }],
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  function updateVariant(i, field, value) {
    const variants = [...form.variants];
    variants[i][field] = value;
    setForm({ ...form, variants });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await api.sellerCreateProduct(form);
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-6 z-50" onClick={onClose}>
      <motion.form
        initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
        onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}
        className="bg-ivory rounded-3xl p-8 max-w-lg w-full max-h-[85vh] overflow-y-auto flex flex-col gap-3"
      >
        <h2 className="font-display text-2xl text-ink mb-2">Add Product</h2>
        <input required placeholder="Product name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="modal-input" />
        <textarea placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="modal-input" rows={2} />
        <div className="flex gap-2">
          <select value={form.gender_category} onChange={(e) => setForm({ ...form, gender_category: e.target.value })} className="modal-input">
            <option value="men">Men</option>
            <option value="women">Women</option>
          </select>
          <input placeholder="Category (e.g. Shirts)" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="modal-input" />
        </div>
        <input placeholder="Fabric" value={form.fabric_type} onChange={(e) => setForm({ ...form, fabric_type: e.target.value })} className="modal-input" />
        <div className="grid grid-cols-3 gap-2">
          <input required type="number" placeholder="Listed ₹" value={form.listed_price} onChange={(e) => setForm({ ...form, listed_price: e.target.value })} className="modal-input" />
          <input required type="number" placeholder="Floor ₹" value={form.floor_price} onChange={(e) => setForm({ ...form, floor_price: e.target.value })} className="modal-input" />
          <input required type="number" placeholder="Ceiling ₹" value={form.ceiling_price} onChange={(e) => setForm({ ...form, ceiling_price: e.target.value })} className="modal-input" />
        </div>

        <p className="text-sm font-medium text-ink mt-2">Variants</p>
        {form.variants.map((v, i) => (
          <div key={i} className="grid grid-cols-3 gap-2">
            <input placeholder="Size" value={v.size} onChange={(e) => updateVariant(i, "size", e.target.value)} className="modal-input" />
            <input placeholder="Color" value={v.color} onChange={(e) => updateVariant(i, "color", e.target.value)} className="modal-input" />
            <input type="number" placeholder="Stock" value={v.stock} onChange={(e) => updateVariant(i, "stock", e.target.value)} className="modal-input" />
          </div>
        ))}
        <button type="button" onClick={() => setForm({ ...form, variants: [...form.variants, { size: "", color: "", stock: "" }] })} className="text-sm underline text-ink self-start">
          + Add variant
        </button>

        <label className="flex items-center gap-2 text-sm text-ink-soft mt-2">
          <input type="checkbox" checked={form.bargaining_enabled} onChange={(e) => setForm({ ...form, bargaining_enabled: e.target.checked })} />
          Enable bargaining for this product
        </label>

        {error && <p className="text-rani text-sm">{error}</p>}

        <div className="flex gap-3 mt-4">
          <button type="button" onClick={onClose} className="flex-1 border border-ink/15 py-3 rounded-full text-sm">Cancel</button>
          <button type="submit" disabled={saving} className="flex-1 bg-ink text-ivory py-3 rounded-full text-sm disabled:opacity-60">{saving ? "Saving..." : "Save Product"}</button>
        </div>
      </motion.form>
      <style>{`.modal-input { background: white; border: 1px solid rgba(27,26,46,0.1); border-radius: 0.75rem; padding: 0.7rem 1rem; font-size: 0.875rem; outline: none; width: 100%; } .modal-input:focus { border-color: #B8305C; }`}</style>
    </div>
  );
}

function PricingModal({ product, onClose, onSaved }) {
  const [floor, setFloor] = useState(product.floor_price);
  const [ceiling, setCeiling] = useState(product.ceiling_price);
  const [enabled, setEnabled] = useState(product.bargaining_enabled);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await api.sellerUpdatePricing(product.id, { floor_price: floor, ceiling_price: ceiling, bargaining_enabled: enabled });
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-6 z-50" onClick={onClose}>
      <motion.form initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit} className="bg-ivory rounded-3xl p-8 max-w-sm w-full flex flex-col gap-3">
        <h2 className="font-display text-xl text-ink mb-2">Edit Pricing — {product.name}</h2>
        <label className="text-xs text-ink-soft">Floor price (minimum acceptable)</label>
        <input type="number" value={floor} onChange={(e) => setFloor(e.target.value)} className="modal-input2" />
        <label className="text-xs text-ink-soft">Ceiling price (listed price)</label>
        <input type="number" value={ceiling} onChange={(e) => setCeiling(e.target.value)} className="modal-input2" />
        <label className="flex items-center gap-2 text-sm text-ink-soft mt-2">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> Bargaining enabled
        </label>
        {error && <p className="text-rani text-sm">{error}</p>}
        <div className="flex gap-3 mt-4">
          <button type="button" onClick={onClose} className="flex-1 border border-ink/15 py-3 rounded-full text-sm">Cancel</button>
          <button type="submit" disabled={saving} className="flex-1 bg-ink text-ivory py-3 rounded-full text-sm flex items-center justify-center gap-2 disabled:opacity-60">
            <Save className="w-4 h-4" /> {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </motion.form>
      <style>{`.modal-input2 { background: white; border: 1px solid rgba(27,26,46,0.1); border-radius: 0.75rem; padding: 0.7rem 1rem; font-size: 0.875rem; outline: none; } .modal-input2:focus { border-color: #B8305C; }`}</style>
    </div>
  );
}

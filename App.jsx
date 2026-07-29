import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from '
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  Wrench, Users, CheckCircle, Clock, AlertTriangle, TrendingUp, ShieldAlert,
  UserCheck, LayoutDashboard, Settings, Sun, Moon, Languages, LogOut, Plus,
  Search, Filter, Phone, MapPin, Calendar, Edit2, Trash2, X, ChevronDown, Bell
} from 'lucide-react';
import { TECHNICIANS, INITIAL_ORDERS, CHART_DATA, STATUS_CONFIG, USERS } from './data';

// ─── Context ────────────────────────────────────────────────────────────────
const ConfigContext = createContext();
const AppContext = createContext();

const ConfigProvider = ({ children }) => {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'fa');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
    localStorage.setItem('lang', lang);
  }, [lang]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const value = useMemo(() => ({
    lang, theme,
    isRtl: lang === 'fa',
    isDark: theme === 'dark',
    toggleLang: () => setLang(p => p === 'fa' ? 'en' : 'fa'),
    toggleTheme: () => setTheme(p => p === 'light' ? 'dark' : 'light'),
  }), [lang, theme]);

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
};

const useConfig = () => useContext(ConfigContext);
const useApp = () => useContext(AppContext);

// ─── Shared UI ───────────────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const { isRtl } = useConfig();
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.cls}`}>
      {isRtl ? cfg.fa : cfg.en}
    </span>
  );
};

const Modal = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg">
      <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
        <h3 className="font-bold text-gray-800 dark:text-white">{title}</h3>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
          <X size={18} className="dark:text-white" />
        </button>
      </div>
      <div className="p-5">{children}</div>
    </div>
  </div>
);

const Input = ({ label, ...props }) => (
  <div className="mb-4">
    {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>}
    <input
      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      {...props}
    />
  </div>
);

const Select = ({ label, children, ...props }) => (
  <div className="mb-4">
    {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>}
    <select
      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      {...props}
    >
      {children}
    </select>
  </div>
);

const StatCard = ({ title, value, icon: Icon, colorClass, sub }) => (
  <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between">
    <div>
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <h3 className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">{value}</h3>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
    <div className={`p-3.5 rounded-xl ${colorClass}`}><Icon size={22} /></div>
  </div>
);

// ─── Login ───────────────────────────────────────────────────────────────────
const Login = ({ onLogin }) => {
  const [form, setForm] = useState({ username: '', password: '', error: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    const user = USERS.find(u => u.id === form.username && u.password === form.password);
    if (user) onLogin(user);
    else setForm(p => ({ ...p, error: 'نام کاربری یا رمز اشتباه است' }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Wrench size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">FixPanel</h1>
          <p className="text-sm text-gray-500 mt-1">پنل مدیریت تعمیرات</p>
        </div>
        <form onSubmit={handleSubmit}>
          <Select label="کاربر" value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))}>
            <option value="">انتخاب کنید...</option>
            {USERS.map(u => <option key={u.id} value={u.id}>{u.name} ({u.role === 'admin' ? 'مدیر' : 'تکنیسین'})</option>)}
          </Select>
          <Input label="رمز عبور" type="password" placeholder="رمز عبور" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} />
          {form.error && <p className="text-red-500 text-xs mb-3">{form.error}</p>}
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-xl transition-all">
            ورود
          </button>
        </form>
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-xs text-gray-500 dark:text-gray-400">
          <p>مدیر: admin-1 / admin123</p>
          <p>تکنیسین: tech-1 / tech123</p>
        </div>
      </div>
    </div>
  );
};

// ─── Sidebar ─────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: 'dashboard', icon: LayoutDashboard, fa: 'داشبورد', en: 'Dashboard', roles: ['admin', 'technician'] },
  { id: 'orders',    icon: Wrench,          fa: 'سفارشات',  en: 'Orders',    roles: ['admin', 'technician'] },
  { id: 'techs',     icon: Users,           fa: 'تکنیسین‌ها', en: 'Technicians', roles: ['admin'] },
  { id: 'settings',  icon: Settings,        fa: 'تنظیمات',  en: 'Settings',  roles: ['admin', 'technician'] },
];

const Sidebar = ({ activePage, setActivePage }) => {
  const { isRtl } = useConfig();
  const { currentUser, logout } = useApp();

  return (
    <aside className={`w-60 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 p-4 fixed h-full flex flex-col z-20 ${isRtl ? 'right-0 border-l' : 'left-0 border-r'}`}>
      <div className="text-xl font-bold text-blue-600 mb-8 px-2 flex items-center gap-2">
        <Wrench size={22} /> FixPanel
      </div>
      <nav className="flex-1">
        {NAV_ITEMS.filter(i => i.roles.includes(currentUser.role)).map(item => (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className={`w-full flex items-center gap-3 p-3 mb-1 rounded-xl transition-all text-sm font-medium ${
              activePage === item.id
                ? 'bg-blue-600 text-white shadow-md shadow-blue-200 dark:shadow-none'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <item.icon size={18} />
            {isRtl ? item.fa : item.en}
          </button>
        ))}
      </nav>
      <div className="border-t dark:border-gray-700 pt-4">
        <div className="flex items-center gap-3 px-2 mb-3">
          <div className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {currentUser.name[0]}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-800 dark:text-white truncate">{currentUser.name}</p>
            <p className="text-xs text-gray-400">{currentUser.role === 'admin' ? 'مدیر کل' : 'تکنیسین'}</p>
          </div>
        </div>
        <button onClick={logout} className="w-full flex items-center gap-2 p-2.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl text-sm transition-all">
          <LogOut size={16} /> {isRtl ? 'خروج' : 'Logout'}
        </button>
      </div>
    </aside>
  );
};

// ─── Header ───────────────────────────────────────────────────────────────────
const PAGE_TITLES = { dashboard: { fa: 'داشبورد', en: 'Dashboard' }, orders: { fa: 'سفارشات تعمیر', en: 'Repair Orders' }, techs: { fa: 'مدیریت تکنیسین‌ها', en: 'Technicians' }, settings: { fa: 'تنظیمات', en: 'Settings' } };

const Header = ({ activePage }) => {
  const { lang, theme, isRtl, toggleLang, toggleTheme } = useConfig();
  const { orders } = useApp();
  const pendingCount = orders.filter(o => o.status === 'pending').length;

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex items-center justify-between px-6 sticky top-0 z-10">
      <h1 className="text-base font-bold dark:text-white">
        {isRtl ? PAGE_TITLES[activePage]?.fa : PAGE_TITLES[activePage]?.en}
      </h1>
      <div className="flex items-center gap-2">
        <div className="relative">
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full relative">
            <Bell size={18} className="dark:text-white" />
            {pendingCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center leading-none">
                {pendingCount}
              </span>
            )}
          </button>
        </div>
        <button onClick={toggleLang} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
          <Languages size={18} className="dark:text-white" />
        </button>
        <button onClick={toggleTheme} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} className="text-yellow-400" />}
        </button>
      </div>
    </header>
  );
};

// ─── Dashboard Page ───────────────────────────────────────────────────────────
const DashboardPage = () => {
  const { isRtl, isDark } = useConfig();
  const { currentUser, orders } = useApp();

  const myOrders = currentUser.role === 'admin' ? orders : orders.filter(o => o.techId === currentUser.id);
  const locale = isRtl ? 'fa-IR' : 'en-US';

  const stats = useMemo(() => ({
    total: myOrders.length,
    pending: myOrders.filter(o => o.status === 'pending').length,
    inProgress: myOrders.filter(o => o.status === 'in_progress').length,
    completed: myOrders.filter(o => o.status === 'completed').length,
    revenue: myOrders.reduce((s, o) => s + o.cost, 0),
  }), [myOrders]);

  const tooltipStyle = { backgroundColor: isDark ? '#1f2937' : '#fff', borderColor: isDark ? '#374151' : '#e5e7eb', borderRadius: 8 };
  const axisStroke = isDark ? '#9ca3af' : '#6b7280';
  const gridStroke = isDark ? '#374151' : '#f3f4f6';

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center gap-3 bg-gradient-to-l from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/30">
        {currentUser.role === 'admin' ? <ShieldAlert className="text-blue-600 dark:text-blue-400 shrink-0" size={22} /> : <UserCheck className="text-green-600 dark:text-green-400 shrink-0" size={22} />}
        <div>
          <h2 className="font-bold text-gray-800 dark:text-gray-200 text-sm">
            {isRtl ? `خوش آمدید، ${currentUser.name}` : `Welcome, ${currentUser.name}`}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {isRtl ? `نقش: ${currentUser.role === 'admin' ? 'مدیر کل' : 'تکنیسین فنی'}` : `Role: ${currentUser.role === 'admin' ? 'Administrator' : 'Technician'}`}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title={isRtl ? 'کل سفارشات' : 'Total Orders'} value={stats.total} icon={Wrench} colorClass="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" />
        <StatCard title={isRtl ? 'در انتظار' : 'Pending'} value={stats.pending} icon={Clock} colorClass="bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400" />
        <StatCard title={isRtl ? 'انجام شده' : 'Completed'} value={stats.completed} icon={CheckCircle} colorClass="bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400" />
        <StatCard title={isRtl ? 'درآمد (ریال)' : 'Revenue'} value={stats.revenue.toLocaleString(locale)} icon={TrendingUp} colorClass="bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400" sub={isRtl ? 'مجموع کل' : 'Total'} />
      </div>

      {/* Charts */}
      {currentUser.role === 'admin' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-bold text-gray-800 dark:text-white mb-4">{isRtl ? 'گزارش درآمد هفتگی' : 'Weekly Revenue'}</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={CHART_DATA}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                  <XAxis dataKey="name" stroke={axisStroke} tick={{ fontSize: 10 }} />
                  <YAxis stroke={axisStroke} tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="revenue" stroke="#2563eb" fill="url(#rev)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-bold text-gray-800 dark:text-white mb-4">{isRtl ? 'سفارشات روزانه' : 'Daily Orders'}</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={CHART_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                  <XAxis dataKey="name" stroke={axisStroke} tick={{ fontSize: 10 }} />
                  <YAxis stroke={axisStroke} tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="orders" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Recent Orders */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="px-5 py-4 border-b dark:border-gray-700">
          <h3 className="text-sm font-bold text-gray-800 dark:text-white">{isRtl ? 'آخرین سفارش‌ها' : 'Recent Orders'}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 text-xs">
              <tr>
                <th className="p-4 text-right">{isRtl ? 'کد' : 'ID'}</th>
                <th className="p-4 text-right">{isRtl ? 'مشتری' : 'Customer'}</th>
                <th className="p-4 text-right">{isRtl ? 'دستگاه' : 'Device'}</th>
                <th className="p-4 text-right">{isRtl ? 'وضعیت' : 'Status'}</th>
                <th className="p-4 text-right">{isRtl ? 'هزینه' : 'Cost'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {myOrders.slice(0, 5).map(order => (
                <tr key={order.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 text-gray-700 dark:text-gray-300 text-xs">
                  <td className="p-4 font-mono font-bold text-blue-600 dark:text-blue-400">{order.id}</td>
                  <td className="p-4">{order.customer}</td>
                  <td className="p-4">{order.device}</td>
                  <td className="p-4"><StatusBadge status={order.status} /></td>
                  <td className="p-4 font-semibold">{order.cost.toLocaleString(locale)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─── Orders Page ──────────────────────────────────────────────────────────────
const OrderModal = ({ order, onClose }) => {
  const { isRtl } = useConfig();
  const { currentUser, orders, setOrders } = useApp();
  const isNew = !order;

  const [form, setForm] = useState(order ?? {
    id: `ORD-${Date.now().[form, setForm] = useState(order ?? {
    id: `ORD-${Date.now()}`,
```jsx
customer: '', phone: '', address: '', device: '', issue: 

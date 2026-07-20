import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area 
} from 'recharts';
import { 
  Wrench, Users, CheckCircle, Clock, AlertTriangle, 
  TrendingUp, ShieldAlert, UserCheck, LayoutDashboard, Settings, Sun, Moon, Languages
} from 'lucide-react';

// ========================================
// ۱. بخش مدیریت تنظیمات (Context) در همین فایل
// ==========================================
const ConfigContext = createContext();

const ConfigProvider = ({ children }) => {
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'fa');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    const dir = lang === 'fa' ? 'rtl' : 'ltr';
    document.documentElement.dir = dir;
    document.documentElement.lang = lang;
    localStorage.setItem('lang', lang);

    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [lang, theme]);

  const toggleLang = () => setLang(prev => prev === 'fa' ? 'en' : 'fa');
  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  return (
    <ConfigContext.Provider value={{ lang, theme, toggleLang, toggleTheme }}>
      {children}
    </ConfigContext.Provider>
  );
};

const useConfig = () => useContext(ConfigContext);

// ==========================================
// ۲. داده‌های فرضی (Mock Data)
// ==========================================
const MOCK_ORDERS = [
  { id: 'ORD-101', customer: 'علی رضایی', device: 'ماشین لباسشویی LG', status: 'pending', techId: 'tech-1', cost: 1200000 },
  { id: 'ORD-102', customer: 'مریم حسینی', device: 'یخچال ساید سامسونگ', status: 'in_progress', techId: 'tech-2', cost: 4500000 },
  { id: 'ORD-103', customer: 'رضا عباسی', device: 'ماشین ظرفشویی بوش', status: 'completed', techId: 'tech-1', cost: 2800000 },
  { id: 'ORD-104', customer: 'زهرا تقوی', device: 'کولر گازی جنرال', status: 'pending', techId: null, cost: 0 },
  { id: 'ORD-105', customer: 'حسین محمدی', device: 'مایکروویو پاناسونیک', status: 'completed', techId: 'tech-2', cost: 850000 },
];

const CHART_DATA = [
  { name: 'شنبه', revenue: 1200000, orders: 1 },
  { name: 'یکشنبه', revenue: 4500000, orders: 2 },
  { name: 'دوشنبه', revenue: 2800000, orders: 1 },
  { name: 'سه‌شنبه', revenue: 850000, orders: 1 },
  { name: 'چهارشنبه', revenue: 5300000, orders: 3 },
];

// ==========================================
// ۳. کامپوننت‌های فرعی UI
// ==========================================
const SidebarItem = ({ icon: Icon, label, active }) => (
  <div className={`flex items-center p-3 mb-2 cursor-pointer rounded-lg transition-all ${
    active ? 'bg-blue-600 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'
  }`}>
    <Icon size={20} className="mx-2" />
    <span className="font-medium text-sm">{label}</span>
  </div>
);

const StatCard = ({ title, value, icon: Icon, colorClass }) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between transition-all duration-300">
    <div>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <h3 className="text-2xl font-bold mt-2 text-gray-900 dark:text-white">{value}</h3>
    </div>
    <div className={`p-4 rounded-xl ${colorClass}`}>
      <Icon size={24} />
    </div>
  </div>
);

// ==========================================
// ۴. قالب اصلی پنل (Layout)
// ==========================================
const AdminLayout = ({ children }) => {
  const { lang, theme, toggleLang, toggleTheme } = useConfig();
  const isRtl = lang === 'fa';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex transition-colors duration-300">
      {/* Sidebar */}
      <aside className={`w-64 bg-white dark:bg-gray-800 border-l border-r dark:border-gray-700 p-4 fixed h-full ${isRtl ? 'right-0' : 'left-0'}`}>
        <div className="text-2xl font-bold text-blue-600 mb-8 px-2">FixPanel</div>
        <nav>
          <SidebarItem icon={LayoutDashboard} label={isRtl ? 'داشبورد' : 'Dashboard'} active />
          <SidebarItem icon={Wrench} label={isRtl ? 'سفارشات تعمیر' : 'Repair Orders'} />
          <SidebarItem icon={Users} label={isRtl ? 'تکنیسین‌ها' : 'Technicians'} />
          <SidebarItem icon={Settings} label={isRtl ? 'تنظیمات' : 'Settings'} />
        </nav>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 ${isRtl ? 'mr-64' : 'ml-64'} transition-all`}>
        {/* Navbar */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex items-center justify-between px-6 sticky top-0 z-10">
          <h1 className="text-lg font-bold dark:text-white">
            {isRtl ? 'مدیریت خدمات تعمیرات آنلاین' : 'Service Management Dashboard'}
          </h1>
          
          <div className="flex items-center gap-4">
            <button onClick={toggleLang} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full" title="تغییر زبان / Toggle Language">
              <Languages size={20} className="dark:text-white" />
            </button>
            <button onClick={toggleTheme} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full" title="تغییر تم / Toggle Theme">
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} className="text-yellow-400" />}
            </button>
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm">
              م‌ح
            </div>
          </div>
        </header>

        <section className="p-6">
          {children}
        </section>
      </main>
    </div>
  );
};

// ==========================================
// ۵. محتوای داشبورد و کنترل سطح دسترسی (RBAC)
// ==========================================
const DashboardContent = ({ currentUser }) => {
  const { lang, theme } = useConfig();
  const isRtl = lang === 'fa';
  const isDark = theme === 'dark';

  // منطق کنترل سطح دسترسی: ادمین همه سفارش‌ها را می‌بیند، تکنیسین فقط سفارش‌های خودش را.
  const filteredOrders = currentUser.role === 'admin' 
    ? MOCK_ORDERS 
    : MOCK_ORDERS.filter(order => order.techId === currentUser.id);

  const totalRevenue = filteredOrders.reduce((sum, item) => sum + item.cost, 0);
  const pendingCount = filteredOrders.filter(o => o.status === 'pending').length;
  const completedCount = filteredOrders.filter(o => o.status === 'completed').length;

  return (
    <div className="space-y-8">
      {/* پیام خوش‌آمدگویی بر اساس نقش کاربر */}
      <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800/30">
        <div className="flex items-center gap-3">
          {currentUser.role === 'admin' ? (
            <ShieldAlert className="text-blue-600 dark:text-blue-400" size={24} />
          ) : (
            <UserCheck className="text-green-600 dark:text-green-400" size={24} />
          )}
          <div>
            <h2 className="font-bold text-gray-800 dark:text-gray-200 text-sm md:text-base">
              {isRtl ? `خوش آمدید، ${currentUser.name}` : `Welcome, ${currentUser.name}`}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {isRtl 
                ? `سطح دسترسی فعلی شما: ${currentUser.role === 'admin' ? 'مدیر کل (Admin)' : 'تکنیسین فنی (Technician)'}`
                : `Current Role: ${currentUser.role === 'admin' ? 'Administrator' : 'Technician'}`
              }
            </p>
          </div>
        </div>
      </div>

      {/* کارت‌های آمار */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title={isRtl ? 'تعداد کل کارها' : 'Total Tasks'} 
          value={filteredOrders.length} 
          icon={Wrench} 
          colorClass="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" 
        />
        <StatCard 
          title={isRtl ? 'در انتظار اقدام' : 'Pending'} 
          value={pendingCount} 
          icon={Clock} 
          colorClass="bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400" 
        />
        <StatCard 
          title={isRtl ? 'انجام شده' : 'Completed'} 
          value={completedCount} 
          icon={CheckCircle} 
          colorClass="bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400" 
        />
        <StatCard 
          title={isRtl ? 'درآمد (تومان)' : 'Revenue (IRR)'} 
          value={totalRevenue.toLocaleString(isRtl ? 'fa-IR' : 'en-US')} 
          icon={TrendingUp} 
          colorClass="bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400" 
        />
      </div>

      {/* بخش نمودارها با Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-base font-bold text-gray-800 dark:text-white mb-4">
            {isRtl ? 'گزارش مالی و درآمد' : 'Revenue Report'}
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART_DATA}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f3f4f6'} />
                <XAxis dataKey="name" stroke={isDark ? '#9ca3af' : '#4b5563'} tick={{ fontSize: 11 }} />
                <YAxis stroke={isDark ? '#9ca3af' : '#4b5563'} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderColor: isDark ? '#374151' : '#e5e7eb' }} />
                <Area type="monotone" dataKey="revenue" stroke="#2563eb" fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="text-base font-bold text-gray-800 dark:text-white mb-4">
            {isRtl ? 'نمودار تعداد سفارشات روزانه' : 'Daily Orders'}
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={CHART_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#f3f4f6'} />
                <XAxis dataKey="name" stroke={isDark ? '#9ca3af' : '#4b5563'} tick={{ fontSize: 11 }} />
                <YAxis stroke={isDark ? '#9ca3af' : '#4b5563'} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: isDark ? '#1f2937' : '#fff', borderColor: isDark ? '#374151' : '#e5e7eb' }} />
                <Bar dataKey="orders" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* جدول داده‌ها */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-base font-bold text-gray-800 dark:text-white">
            {isRtl ? 'لیست آخرین سفارش‌های خدمات تعمیر' : 'Service Orders'}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-gray-50 dark:bg-gray-700/50 text-gray-600 dark:text-gray-300 text-xs">
              <tr>
                <th className="p-4">{isRtl ? 'کد سفارش' : 'Order ID'}</th>
                <th className="p-4">{isRtl ? 'مشتری' : 'Customer'}</th>
                <th className="p-4">{isRtl ? 'دستگاه' : 'Device'}</th>
                <th className="p-4">{isRtl ? 'وضعیت' : 'Status'}</th>
                <th className="p-4">{isRtl ? 'هزینه (تومان)' : 'Cost (IRR)'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-xs">
              {filteredOrders.map(order => (
                <tr key={order.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 text-gray-700 dark:text-gray-300">
                  <td className="p-4 font-mono font-bold text-blue-600 dark:text-blue-400">{order.id}</td>
                  <td className="p-4">{order.customer}</td>
                  <td className="p-4">{order.device}</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-1 rounded-full text-2xs font-semibold ${
                      order.status === 'completed' 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400'
                        : order.status === 'in_progress'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                    }`}>
                      {order.status === 'completed' && (isRtl ? 'تکمیل شده' : 'Completed')}
                      {order.status === 'in_progress' && (isRtl ? 'در حال انجام' : 'In Progress')}
                      {order.status === 'pending' && (isRtl ? 'معلق' : 'Pending')}
                    </span>
                  </td>
                  <td className="p-4 font-semibold">{order.cost.toLocaleString(isRtl ? 'fa-IR' : 'en-US')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// ۶. کامپوننت اصلی و روت برنامه
// ==========================================
export default function App() {
  // نقش پیش‌فرض کاربر سیستم 'technician' است.
  const [currentUser, setCurrentUser] = useState({
    id: 'tech-1',
    name: 'محمدحسین (تکنیسین)',
    role: 'technician'
  });

  const toggleUserRole = () => {
    setCurrentUser(prev => 
      prev.role === 'admin' 
        ? { id: 'tech-1', name: 'محمدحسین (تکنیسین)', role: 'technician' }
        : { id: 'admin-1', name: 'مدیر کل (Admin)', role: 'admin' }
    );
  };

  return (
    <ConfigProvider>
      <AdminLayout>
        {/* دکمه سوئیچر تستی برای تغییر نقش و مشاهده تغییر اطلاعات */}
        <div className="mb-4 flex justify-end">
          <button 
            onClick={toggleUserRole}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white text-xs px-3.5 py-2 rounded-xl shadow-md transition-all active:scale-95"
          >
            <AlertTriangle size={14} />
            تغییر نقش تستی (نقش فعلی: {currentUser.role})
          </button>
        </div>

        <DashboardContent currentUser={currentUser} />
      </AdminLayout>
    </ConfigProvider>
  );
}

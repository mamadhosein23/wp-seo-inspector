export const TECHNICIANS = [
  { id: 'tech-1', name: 'احمد کریمی', phone: '09131234567', specialty: 'ماشین لباسشویی، ظرفشویی', active: true } 
  { id: 'tech-2', name: 'سعید نوری', phone: '09139876543', specialty: 'یخچال، کولر گازی', active: true } 
  { id: 'tech-3', name: 'مهدی صادقی', phone: '09135551234', specialty: 'مایکروویو، اجاق گاز', active: false } , 
];

export const INITIAL_ORDERS = [
  { id: 'ORD-101', customer: 'علی رضایی', phone: '09121111111', address: 'اصفهان، خیابان چهارباغ', device: 'ماشین لباسشویی LG', issue: 'آب نمی‌کشد', status: 'pending', techId: null, cost: 0, createdAt: '1405/05/01', scheduledAt: '1405/05/07' },
  { id: 'ORD-102', customer: 'مریم حسینی', phone: '09122222222', address: 'اصفهان، سعادت‌آباد', device: 'یخچال ساید سامسونگ', issue: 'خنک نمی‌کند', status: 'in_progress', techId: 'tech-2', cost: 4500000, createdAt: '1405/05/02', scheduledAt: '1405/05/06' },
  { id: 'ORD-103', customer: 'رضا عباسی', phone: '09123333333', address: 'اصفهان، بهارستان', device: 'ماشین ظرفشویی بوش', issue: 'تخلیه نمی‌کند', status: 'completed', techId: 'tech-1', cost: 2800000, createdAt: '1405/04/28', scheduledAt: '1405/05/03' },
  { id: 'ORD-104', customer: 'زهرا تقوی', phone: '09124444444', address: 'اصفهان، جی', device: 'کولر گازی جنرال', issue: 'سرد نمی‌کند', status: 'pending', techId: null, cost: 0, createdAt: '1405/05/04', scheduledAt: '1405/05/08' },
  { id: 'ORD-105', customer: 'حسین محمدی', phone: '09125555555', address: 'اصفهان، فلاورجان', device: 'مایکروویو پاناسونیک', issue: 'روشن نمی‌شود', status: 'completed', techId: 'tech-2', cost: 850000, createdAt: '1405/05/03', scheduledAt: '1405/05/05' },
  { id: 'ORD-106', customer: 'فاطمه موسوی', phone: '09126666666', address: 'اصفهان، خمینی‌شهر', device: 'اجاق گاز اسنوا', issue: 'شعله روشن نمی‌شود', status: 'in_progress', techId: 'tech-1', cost: 1500000, createdAt: '1405/05/05', scheduledAt: '1405/05/06' },
  { id: 'ORD-107', customer: 'علیرضا کمالی', phone: '09127777777', address: 'اصفهان، نجف‌آباد', device: 'لباسشویی آریستون', issue: 'لرزش زیاد', status: 'cancelled', techId: 'tech-3', cost: 0, createdAt: '1405/05/01', scheduledAt: '1405/05/04' },
];

export const CHART_DATA = [
  { name: 'شنبه', revenue: 1200000, orders: 2 },
  { name: 'یکشنبه', revenue: 4500000, orders: 3 },
  { name: 'دوشنبه', revenue: 2800000, orders: 2 },
  { name: 'سه‌شنبه', revenue: 850000, orders: 1 },
  { name: 'چهارشنبه', revenue: 5300000, orders: 4 },
  { name: 'پنجشنبه', revenue: 3100000, orders: 3 },
];

export const STATUS_CONFIG = {
  completed:   { fa: 'تکمیل شده',   en: 'Completed',   cls: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' },
  in_progress: { fa: 'در حال انجام', en: 'In Progress', cls: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' },
  pending:     { fa: 'معلق',         en: 'Pending',     cls: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' },
  cancelled:   { fa: 'لغو شده',      en: 'Cancelled',   cls: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' },
};

export const USERS = [
  { id: 'admin-1', name: 'محمدحسین', role: 'admin', password: 'admin123' },
  { id: 'tech-1',  name: 'احمد کریمی', role: 'technician', password: 'tech123' },
  { id: 'tech-2',  name: 'سعید نوری',  role: 'technician', password: 'tech456' },
];

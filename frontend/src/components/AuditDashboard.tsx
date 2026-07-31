// frontend/src/components/AuditDashboard.tsx
import { AuditResponse, CheckItem, CheckStatus } from "@/types/audit";
import { BadgeCheck, XCircle, AlertTriangle, Info, Zap, Link } from "lucide-react";
import LinkComponent from "next/link"; // برای لینک به بیرون

interface AuditDashboardProps {
  result: AuditResponse;
}

const statusMap: Record<CheckStatus, { icon: React.FC<any>, color: string, label: string }> = {
  success: { icon: BadgeCheck, color: "text-green-500", label: "موفق" },
  warning: { icon: AlertTriangle, color: "text-yellow-500", label: "هشدار" },
  error: { icon: XCircle, color: "text-red-500", label: "خطا" },
  info: { icon: Info, color: "text-blue-500", label: "اطلاعات" },
};

const getStatusClasses = (status: CheckStatus) => {
    switch(status) {
        case 'success': return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
        case 'warning': return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
        case 'error': return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
        case 'info': return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
    }
}

// ----------------------------------------------------
// Sub-Components
// ----------------------------------------------------

const ScoreCard: React.FC<{ score: number }> = ({ score }) => {
  const color = score > 90 ? 'text-green-500' : score > 70 ? 'text-yellow-500' : 'text-red-500';

  return (
    <div className="card text-center p-8 col-span-full md:col-span-1">
      <Zap className={`w-10 h-10 mx-auto mb-2 ${color}`} />
      <h3 className="text-xl font-semibold text-gray-500 dark:text-gray-400">امتیاز سئو</h3>
      <div className={`text-6xl font-extrabold ${color} mt-2`}>{score}</div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">از 100</p>
    </div>
  );
};

const ChecksSummary: React.FC<{ checks: CheckItem[] }> = ({ checks }) => {
    const counts = checks.reduce((acc, item) => {
        acc[item.status] = (acc[item.status] || 0) + 1;
        return acc;
    }, {} as Record<CheckStatus, number>);

    return (
        <div className="card col-span-full md:col-span-2 grid grid-cols-2 lg:grid-cols-4 gap-4">
            {(['error', 'warning', 'success', 'info'] as CheckStatus[]).map(statusKey => {
                const { icon: Icon, color, label } = statusMap[statusKey];
                const count = counts[statusKey] || 0;
                
                return (
                    <div key={statusKey} className="text-center p-3 rounded-lg border border-gray-100 dark:border-gray-800">
                        <Icon className={`w-7 h-7 mx-auto mb-1 ${color}`} />
                        <div className="text-3xl font-bold">{count}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
                    </div>
                )
            })}
        </div>
    );
}

const CheckItemComponent: React.FC<{ item: CheckItem }> = ({ item }) => {
    const { icon: Icon, color, label } = statusMap[item.status];
    const itemClasses = getStatusClasses(item.status);

    return (
        <div className={`p-4 border-l-4 rounded-lg ${itemClasses} mb-3`}>
            <div className="flex items-center justify-between">
                <div className="flex items-center">
                    <Icon className={`w-5 h-5 ml-2 ${color}`} />
                    <span className="font-semibold text-gray-800 dark:text-gray-100">{item.label}</span>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                    {item.value !== undefined && item.value !== null ? String(item.value) : ''}
                </span>
            </div>
            <p className="text-sm mt-1 text-gray-700 dark:text-gray-300">{item.message}</p>
            {item.recommendation && (
                <div className="mt-2 pt-2 border-t border-dashed border-gray-300 dark:border-gray-700">
                    <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">توصیه: </span>
                    <span className="text-sm text-gray-600 dark:text-gray-400">{item.recommendation}</span>
                </div>
            )}
        </div>
    );
}

// ----------------------------------------------------
// Main Dashboard Component
// ----------------------------------------------------

export default function AuditDashboard({ result }: AuditDashboardProps) {
  const { url, final_url, score, checks, title, meta_description } = result;

  // فیلتر کردن و مرتب‌سازی
  const orderedChecks = checks.sort((a, b) => {
    const statusOrder: Record<CheckStatus, number> = { error: 1, warning: 2, info: 3, success: 4 };
    return statusOrder[a.status] - statusOrder[b.status];
  });


  return (
    <div className="space-y-8">
      {/* Target URL and Quick Info */}
      <div className="card p-5">
        <h2 className="text-2xl font-bold mb-2">نتیجه تحلیل</h2>
        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <Link className="w-4 h-4 ml-2" />
            <span className="font-medium">URL تحلیل‌شده: </span>
            <LinkComponent href={final_url} target="_blank" className="truncate hover:text-indigo-500 transition-colors mr-2">
                {final_url}
            </LinkComponent>
        </div>
      </div>

      {/* Score and Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ScoreCard score={score} />
        <ChecksSummary checks={checks} />
      </div>

      {/* Main SEO Elements */}
      <div className="card">
        <h3 className="text-xl font-semibold border-b pb-2 mb-4 border-gray-200 dark:border-gray-800">
            عناصر اصلی سئو
        </h3>
        <div className="space-y-4">
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Title Tag:</p>
                <p className="mt-1 text-gray-800 dark:text-gray-200">{title || '— نامشخص —'}</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Meta Description:</p>
                <p className="mt-1 text-gray-800 dark:text-gray-200">{meta_description || '— نامشخص —'}</p>
            </div>
        </div>
      </div>

      {/* Detailed Checks */}
      <div className="card">
        <h3 className="text-xl font-semibold border-b pb-2 mb-4 border-gray-200 dark:border-gray-800">
            بررسی‌های فنی (Total: {checks.length})
        </h3>
        <div>
            {orderedChecks.map((check, index) => (
                <CheckItemComponent key={index} item={check} />
            ))}
        </div>
      </div>
      
    </div>
  );
}

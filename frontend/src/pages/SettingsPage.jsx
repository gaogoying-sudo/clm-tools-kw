import { useState } from 'react'

const tabs = [
  { key: 'users', label: '用户权限' },
  { key: 'questions', label: '问题模板' },
  { key: 'engineers', label: '工程师花名册' },
  { key: 'datasource', label: '数据源配置' },
  { key: 'logs', label: '系统日志' },
]

export function SettingsPage() {
  const [tab, setTab] = useState('users')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">系统管理</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-6">
          {tabs.map(t => (
            <button key={t.key}
              onClick={() => setTab(t.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
        {tab === 'users' && '用户权限管理 — 角色分配、访问范围设置'}
        {tab === 'questions' && '问题模板管理 — 增删改查问题模板及触发规则'}
        {tab === 'engineers' && '工程师花名册管理 — 36位工程师信息维护'}
        {tab === 'datasource' && '数据源配置 — 公司后台数据库连接管理'}
        {tab === 'logs' && '系统日志 — 操作记录、错误日志、性能监控'}
      </div>
    </div>
  )
}

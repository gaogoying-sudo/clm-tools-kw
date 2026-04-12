import { useState, useEffect } from 'react'
import { api } from '../api'

const tabs = [
  { key: 'engineers', label: '工程师花名册' },
  { key: 'questions', label: '问题模板' },
  { key: 'datasource', label: '数据源配置' },
  { key: 'users', label: '用户权限' },
  { key: 'logs', label: '系统日志' },
]

export function SettingsPage() {
  const [tab, setTab] = useState('engineers')
  const [engineers, setEngineers] = useState([])
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (tab === 'engineers') {
      setLoading(true)
      api.getEngineers('').then(setEngineers).catch(() => {}).finally(() => setLoading(false))
    } else if (tab === 'questions') {
      setLoading(true)
      api.getQuestions().then(setQuestions).catch(() => {}).finally(() => setLoading(false))
    }
  }, [tab])

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
      {loading && <div className="flex items-center justify-center h-32 text-gray-400">加载中...</div>}

      {/* Engineers Tab */}
      {!loading && tab === 'engineers' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">工程师花名册 ({engineers.length} 人)</h2>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b border-gray-100">
                <th className="px-6 py-3 font-medium">姓名</th>
                <th className="px-6 py-3 font-medium">角色</th>
                <th className="px-6 py-3 font-medium">区域</th>
                <th className="px-6 py-3 font-medium">今日任务</th>
                <th className="px-6 py-3 font-medium">总执行</th>
              </tr>
            </thead>
            <tbody>
              {engineers.map(e => (
                <tr key={e.engineer.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-6 py-3 font-medium text-gray-900">{e.engineer.name}</td>
                  <td className="px-6 py-3 text-sm text-gray-600">{e.engineer.role}</td>
                  <td className="px-6 py-3 text-sm text-gray-600">{e.engineer.region}</td>
                  <td className="px-6 py-3 text-sm">{e.task_count}</td>
                  <td className="px-6 py-3 text-sm">{e.total_exec}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Questions Tab */}
      {!loading && tab === 'questions' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">问题模板 ({questions.length} 个)</h2>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b border-gray-100">
                <th className="px-6 py-3 font-medium">Key</th>
                <th className="px-6 py-3 font-medium">标题</th>
                <th className="px-6 py-3 font-medium">类型</th>
                <th className="px-6 py-3 font-medium">触发题</th>
                <th className="px-6 py-3 font-medium">状态</th>
              </tr>
            </thead>
            <tbody>
              {questions.map(q => (
                <tr key={q.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-6 py-3 font-mono text-sm text-blue-600">{q.question_key}</td>
                  <td className="px-6 py-3 text-sm text-gray-900">{q.title}</td>
                  <td className="px-6 py-3 text-sm text-gray-600">{q.question_type}</td>
                  <td className="px-6 py-3 text-sm">{q.is_triggered ? <span className="text-orange-600">是</span> : '否'}</td>
                  <td className="px-6 py-3 text-sm">{q.is_active ? <span className="text-green-600">启用</span> : <span className="text-gray-400">禁用</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Placeholder tabs */}
      {!loading && tab === 'datasource' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">数据源配置</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">本地 MySQL</div>
                <div className="text-sm text-gray-500">clm_review (mock 模式)</div>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">已连接</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">公司源数据库 (btyc)</div>
                <div className="text-sm text-gray-500">待配置</div>
              </div>
              <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs font-medium">未连接</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">云服务器 MySQL</div>
                <div className="text-sm text-gray-500">82.156.187.35:3306</div>
              </div>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">待部署</span>
            </div>
          </div>
        </div>
      )}

      {!loading && tab === 'users' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-400">
          用户权限管理 — 角色分配、访问范围设置（开发中）
        </div>
      )}

      {!loading && tab === 'logs' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-400">
          系统日志 — 操作记录、错误日志、性能监控（开发中）
        </div>
      )}
    </div>
  )
}

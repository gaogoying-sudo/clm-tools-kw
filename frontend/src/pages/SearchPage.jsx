import { useState, useEffect } from 'react'
import { api } from '../api'

export function SearchPage() {
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10),
    endDate: new Date().toISOString().slice(0, 10),
    engineerName: '',
    dishName: '',
    status: '',
    hasAbnormal: '',
  })
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [fromCache, setFromCache] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [engineers, setEngineers] = useState([])

  useEffect(() => {
    api.getEngineers('').then(setEngineers).catch(() => {})
  }, [])

  const handleSearch = async (p = 1) => {
    setLoading(true)
    setPage(p)
    try {
      const params = {
        start_date: filters.startDate,
        end_date: filters.endDate,
        page: p,
        size: 20,
      }
      if (filters.engineerName) params.engineer_name = filters.engineerName
      if (filters.dishName) params.dish_name = filters.dishName
      if (filters.status) params.status = filters.status
      if (filters.hasAbnormal) params.has_abnormal = filters.hasAbnormal === 'true'

      const data = await api.searchData(params)
      setResults(data.items || [])
      setTotal(data.total_all || 0)
      setFromCache(data.from_cache || false)
    } catch (err) {
      console.error('Search error:', err)
      setResults([])
    }
    setLoading(false)
  }

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const statusColors = {
    pending: 'bg-blue-100 text-blue-700',
    pushed: 'bg-yellow-100 text-yellow-700',
    submitted: 'bg-green-100 text-green-700',
    expired: 'bg-gray-100 text-gray-500',
  }
  const statusLabels = { pending: '待填写', pushed: '已推送', submitted: '已回收', expired: '已过期' }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">数据检索</h1>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">开始日期</label>
            <input type="date" value={filters.startDate} onChange={e => setFilters({...filters, startDate: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">结束日期</label>
            <input type="date" value={filters.endDate} onChange={e => setFilters({...filters, endDate: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">工程师</label>
            <select value={filters.engineerName} onChange={e => setFilters({...filters, engineerName: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">全部工程师</option>
              {engineers.map(e => <option key={e.engineer.id} value={e.engineer.name}>{e.engineer.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">菜品</label>
            <input type="text" placeholder="菜名关键词" value={filters.dishName} onChange={e => setFilters({...filters, dishName: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">会话状态</label>
            <select value={filters.status} onChange={e => setFilters({...filters, status: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">全部</option>
              <option value="pending">待填写</option>
              <option value="pushed">已推送</option>
              <option value="submitted">已回收</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">异常标记</label>
            <select value={filters.hasAbnormal} onChange={e => setFilters({...filters, hasAbnormal: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">全部</option>
              <option value="true">有异常</option>
              <option value="false">无异常</option>
            </select>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => handleSearch(1)} disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {loading ? '检索中...' : '检索'}
          </button>
          {fromCache && <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">命中本地缓存</span>}
        </div>
      </div>

      {/* Cache status notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>缓存策略：</strong>历史已检索数据将直接从本地缓存返回。当天未完成的数据将标记为"进行中"，不会直接返回。
      </div>

      {/* Results */}
      {loading && <div className="flex items-center justify-center h-32 text-gray-400">检索中...</div>}

      {!loading && results.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
          设置检索条件后点击"检索"按钮
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <div className="text-sm text-gray-500">共 {total} 条记录，当前第 {page} 页</div>
          <div className="space-y-3">
            {results.map(item => (
              <div key={item.session_id} className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                  onClick={() => toggleExpand(item.session_id)}>
                  <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <div>
                      <span className="font-medium text-gray-900">{item.engineer?.name || '未知'}</span>
                      <span className="text-xs text-gray-400 ml-2">{item.engineer?.role || ''}</span>
                    </div>
                    <span className="text-sm text-gray-500">{item.session_date}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">{item.task_count}道菜 · {item.total_exec}次执行
                      {item.failed_count > 0 && <span className="text-red-500 ml-1">{item.failed_count}失败</span>}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[item.status] || 'bg-gray-100 text-gray-500'}`}>
                      {statusLabels[item.status] || item.status}
                    </span>
                    <span className="text-gray-400">{expandedId === item.session_id ? '▼' : '▶'}</span>
                  </div>
                </div>

                {expandedId === item.session_id && (
                  <div className="px-6 pb-4 border-t border-gray-100">
                    <div className="mt-3">
                      <div className="text-sm font-medium text-gray-700 mb-2">任务详情</div>
                      <div className="grid grid-cols-2 gap-3">
                        {item.tasks?.map(t => (
                          <div key={t.id} className={`p-3 rounded-lg text-sm ${t.has_abnormal ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
                            <div className="font-medium text-gray-900">{t.dish_name}</div>
                            <div className="text-gray-500 mt-1">
                              执行 {t.exec_count} 次 · 状态: {t.status === 'failed' ? <span className="text-red-600">失败</span> : <span className="text-green-600">通过</span>}
                            </div>
                            {t.customer_name && <div className="text-gray-400 text-xs mt-1">{t.customer_name} · {t.device_id}</div>}
                            {t.modifications?.length > 0 && (
                              <div className="mt-2 text-xs text-orange-600">
                                调整记录: {t.modifications.join('；')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-2">
              <button onClick={() => handleSearch(page - 1)} disabled={page <= 1}
                className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 text-sm">上一页</button>
              <span className="text-sm text-gray-500">第 {page} 页</span>
              <button onClick={() => handleSearch(page + 1)} disabled={results.length < 20}
                className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 text-sm">下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

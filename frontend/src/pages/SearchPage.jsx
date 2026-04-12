import { useState } from 'react'

export function SearchPage() {
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    engineer: '',
    dish: '',
    keyword: '',
  })
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  const handleSearch = async () => {
    setLoading(true)
    // TODO: implement search API with cache layer
    // For now, show placeholder
    setResults([])
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">数据检索</h1>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-5 gap-4 mb-4">
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
            <input type="text" placeholder="姓名或ID" value={filters.engineer} onChange={e => setFilters({...filters, engineer: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">菜品</label>
            <input type="text" placeholder="菜名关键词" value={filters.dish} onChange={e => setFilters({...filters, dish: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">关键词</label>
            <input type="text" placeholder="全文搜索" value={filters.keyword} onChange={e => setFilters({...filters, keyword: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>
        <button onClick={handleSearch} disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {loading ? '检索中...' : '检索'}
        </button>
      </div>

      {/* Results */}
      {results.length === 0 && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
          设置检索条件后点击"检索"按钮
        </div>
      )}

      {/* Cache status notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>缓存策略：</strong>历史已检索数据将直接从本地缓存返回。当天未完成的数据将标记为"进行中"，不会直接返回。
      </div>
    </div>
  )
}
